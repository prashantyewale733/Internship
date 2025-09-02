
# stock_dashboard_app.py
# A simple beginner-friendly real-time-ish stock dashboard using Streamlit + yfinance.
# Run with: streamlit run stock_dashboard_app.py

import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Simple Stock Dashboard", page_icon="📈", layout="wide")

# ---------------------------
# Sidebar controls
# ---------------------------
st.sidebar.title("📊 Stock Dashboard")
default_watchlist = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA"]
watchlist = st.sidebar.text_input(
    "Watchlist (comma-separated tickers)",
    value=",".join(default_watchlist),
    help="Enter symbols separated by commas (e.g., AAPL,MSFT,TSLA)",
)

refresh_sec = st.sidebar.slider("Auto-refresh every (seconds)", 5, 60, 10, help="How often to refresh data")
chart_type = st.sidebar.selectbox("Chart type", ["Line (1m)", "Candlestick (5m)"])
range_map = {
    "Line (1m)": ("1d", "1m"),
    "Candlestick (5m)": ("5d", "5m"),
}
period, interval = range_map[chart_type]

# ---------------------------
# Utility functions
# ---------------------------
@st.cache_data(ttl=30)
def fetch_intraday_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    data = yf.download(tickers=ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    # If empty, return empty DataFrame
    if data is None or data.empty:
        return pd.DataFrame()
    # Ensure DatetimeIndex is timezone-aware for proper plotting
    if data.index.tz is None:
        data.index = data.index.tz_localize("UTC").tz_convert("America/New_York")
    else:
        data.index = data.index.tz_convert("America/New_York")
    return data

@st.cache_data(ttl=15)
def fetch_quote(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).fast_info
        return {
            "last_price": float(info.get("last_price")) if info.get("last_price") is not None else np.nan,
            "open": float(info.get("open")) if info.get("open") is not None else np.nan,
            "previous_close": float(info.get("previous_close")) if info.get("previous_close") is not None else np.nan,
            "currency": info.get("currency") or "",
            "exchange": info.get("exchange") or "",
        }
    except Exception:
        return {
            "last_price": np.nan,
            "open": np.nan,
            "previous_close": np.nan,
            "currency": "",
            "exchange": "",
        }

def pct_change(curr, prev):
    if pd.isna(curr) or pd.isna(prev) or prev == 0:
        return np.nan
    return (curr - prev) / prev * 100.0

# ---------------------------
# Header
# ---------------------------
st.title("📈 Simple Real‑Time Stock Dashboard")
st.caption("Beginner-friendly project using Streamlit + yfinance. Data auto-refreshes on a timer. "
           "Note: 'real-time' here means refreshed frequently from public endpoints; it may be delayed by up to a few minutes.")

# ---------------------------
# Parse tickers
# ---------------------------
tickers = [t.strip().upper() for t in watchlist.split(",") if t.strip()]
if not tickers:
    st.warning("Please enter at least one valid ticker in the sidebar.")
    st.stop()

# ---------------------------
# Top metrics grid
# ---------------------------
cols = st.columns(min(4, len(tickers)))
for i, t in enumerate(tickers[:4]):  # show first 4 as highlight
    q = fetch_quote(t)
    last_price = q["last_price"]
    prev_close = q["previous_close"]
    change = (last_price - prev_close) if (not pd.isna(last_price) and not pd.isna(prev_close)) else np.nan
    change_pct = pct_change(last_price, prev_close)
    with cols[i % 4]:
        st.metric(
            label=f"{t} ({q['exchange']})",
            value=f"{'' if pd.isna(last_price) else round(last_price, 2)} {q['currency']}",
            delta=f"{'' if pd.isna(change_pct) else round(change_pct, 2)}%",
            help=f"Prev close: {'' if pd.isna(prev_close) else round(prev_close,2)} {q['currency']}",
        )

# ---------------------------
# Tabs for each ticker
# ---------------------------
tabs = st.tabs(tickers)
for i, t in enumerate(tabs):
    with t:
        df = fetch_intraday_history(tickers[i], period, interval)

        st.subheader(f"{tickers[i]}")
        q = fetch_quote(tickers[i])

        # Quote row
        qcols = st.columns(4)
        qcols[0].write("**Last**")
        qcols[0].write(f"{'' if pd.isna(q['last_price']) else round(q['last_price'], 2)} {q['currency']}")
        qcols[1].write("**Open**")
        qcols[1].write(f"{'' if pd.isna(q['open']) else round(q['open'], 2)} {q['currency']}")
        qcols[2].write("**Prev Close**")
        qcols[2].write(f"{'' if pd.isna(q['previous_close']) else round(q['previous_close'], 2)} {q['currency']}")
        if not pd.isna(q['last_price']) and not pd.isna(q['previous_close']):
            delta_pct = pct_change(q['last_price'], q['previous_close'])
            qcols[3].metric("Change vs Prev Close", f"{round(q['last_price'] - q['previous_close'], 2)}", f"{round(delta_pct, 2)}%")
        else:
            qcols[3].metric("Change vs Prev Close", "—", "—")

        st.divider()

        if df.empty:
            st.info("No data returned (market closed or invalid ticker). Try a different symbol or a wider range.")
        else:
            if chart_type == "Line (1m)":
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close"))
                fig.update_layout(
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=350,
                    xaxis_title="Time (New York)",
                    yaxis_title="Price",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig = go.Figure(
                    data=[
                        go.Candlestick(
                            x=df.index,
                            open=df["Open"],
                            high=df["High"],
                            low=df["Low"],
                            close=df["Close"],
                            name="OHLC",
                        )
                    ]
                )
                fig.update_layout(
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=350,
                    xaxis_title="Time (New York)",
                    yaxis_title="Price",
                )
                st.plotly_chart(fig, use_container_width=True)

            # Volume bar chart
            if "Volume" in df.columns and not df["Volume"].isna().all():
                vol_fig = go.Figure()
                vol_fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume"))
                vol_fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=200, xaxis_title="Time", yaxis_title="Volume")
                st.plotly_chart(vol_fig, use_container_width=True)

        st.caption("Data source: Yahoo Finance via yfinance. Times shown in America/New_York.")

# ---------------------------
# Auto refresh
# ---------------------------
st.sidebar.markdown("---")
st.sidebar.write("⏱️ Auto-refresh is enabled.")
st.experimental_set_query_params(_=int(time.time()))  # forces URL change for Streamlit cloud
st_autorefresh = st.sidebar.empty()
st_autorefresh.text(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
time.sleep(refresh_sec)
st.rerun()
