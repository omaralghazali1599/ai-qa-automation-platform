from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = "thesis-secret-key"

# In-memory user store (no DB needed for testing)
users = {}
reset_tokens = {}

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()   

    if not email or not password or not name:
        return jsonify({"error": "All fields are required"}), 400
    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if email in users:
        return jsonify({"error": "Email already registered"}), 409

    users[email] = {
        "name": name,
        "phone": phone,
        "password": generate_password_hash(password),
        "locked": False
    }
    return jsonify({"message": "Registration successful"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if email not in users:
        return jsonify({"error": "Invalid credentials"}), 401
    if users[email]["locked"]:
        return jsonify({"error": "Account is locked"}), 403
    if not check_password_hash(users[email]["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    session["user"] = email
    return jsonify({"message": "Login successful", "name": users[email]["name"]}), 200


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logged out successfully"}), 200


@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"error": "Email is required"}), 400
    if email not in users:
        return jsonify({"error": "Email not found"}), 404

    token = f"reset-token-{email}"
    reset_tokens[token] = email
    return jsonify({"message": "Reset link sent", "token": token}), 200


@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    token = data.get("token", "")
    new_password = data.get("new_password", "")

    if token not in reset_tokens:
        return jsonify({"error": "Invalid or expired token"}), 400
    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    email = reset_tokens.pop(token)
    users[email]["password"] = generate_password_hash(new_password)
    return jsonify({"message": "Password reset successful"}), 200


@app.route("/profile", methods=["GET"])
def profile():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    email = session["user"]
    return jsonify({"email": email, "name": users[email]["name"], "phone": users[email]["phone"]}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5001)