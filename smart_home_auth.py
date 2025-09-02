
from flask import Flask, request, redirect, url_for, render_template_string, session

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for sessions. Change in real apps!

# --- Fake database of users (in-memory) ---
USERS = {
    "admin": "1234",      # username: password
    "guest": "guestpass"
}

# --- HTML templates ---
layout_top = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Home</title>
</head>
<body style="font-family:sans-serif; max-width:400px; margin:auto;">
    <h2>🏠 Smart Home System</h2>
"""
layout_bottom = """
</body>
</html>
"""

login_page = layout_top + """
    <h3>Login</h3>
    <form method="post" action="/login">
        <label>Username:</label><br>
        <input type="text" name="username"><br><br>
        <label>Password:</label><br>
        <input type="password" name="password"><br><br>
        <button type="submit">Log In</button>
    </form>
    <p>Don't have an account? <a href="/register">Register here</a>.</p>
    {% if error %}
    <p style="color:red;">{{ error }}</p>
    {% endif %}
""" + layout_bottom

register_page = layout_top + """
    <h3>Register</h3>
    <form method="post" action="/register">
        <label>Choose Username:</label><br>
        <input type="text" name="username"><br><br>
        <label>Choose Password:</label><br>
        <input type="password" name="password"><br><br>
        <button type="submit">Register</button>
    </form>
    <p>Already have an account? <a href="/">Login here</a>.</p>
    {% if error %}
    <p style="color:red;">{{ error }}</p>
    {% endif %}
""" + layout_bottom

control_panel = layout_top + """
    <h3>Welcome, {{ user }}!</h3>
    <p>You now have access to the smart home control panel.</p>
    <ul>
        <li><button>Turn on lights</button></li>
        <li><button>Lock doors</button></li>
        <li><button>Adjust thermostat</button></li>
    </ul>
    <p><a href="/logout">Log out</a></p>
""" + layout_bottom

# --- Routes ---
@app.route("/")
def home():
    if "user" in session:
        return render_template_string(control_panel, user=session["user"])
    return render_template_string(login_page)

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    if username in USERS and USERS[username] == password:
        session["user"] = username
        return redirect(url_for("home"))
    else:
        return render_template_string(login_page, error="Invalid username or password.")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS:
            return render_template_string(register_page, error="Username already taken.")
        if not username or not password:
            return render_template_string(register_page, error="Please fill all fields.")
        USERS[username] = password
        session["user"] = username
        return redirect(url_for("home"))
    return render_template_string(register_page)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
