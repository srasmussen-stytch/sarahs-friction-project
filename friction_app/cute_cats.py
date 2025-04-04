from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import os
import dotenv
from stytch import Client
from stytch.core.response_base import StytchError

# load the .env file
dotenv.load_dotenv()

# Load stytch client
stytch_client = Client(
  project_id=os.getenv("STYTCH_PROJECT_ID"),
  secret=os.getenv("STYTCH_SECRET"),
  environment="test"
)

app = Flask(__name__)
app.secret_key = "super_safe_secret_key"

# Directory where images are stored
IMAGE_DIR = "static/images"

def get_random_image():
    """Gets a random image from the image directory."""
    images = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    if not images:
        return None  # Return None if no images are found
    return random.choice(images)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        try:
            resp = stytch_client.passwords.create(
                email=username,
                password=password,
            )

        except StytchError as e:
            return render_template("signup.html", error=f"An error occurred: {e.details}")
        return redirect(url_for("login"))
    return render_template("signup.html", error=None)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        try:
            resp = stytch_client.passwords.authenticate(
                email=username,
                password=password,
            )
            session["username"] = username
            return redirect(url_for("cat_vote"))
        except StytchError as e:
            return render_template("login.html", error=f"There was an error {e.details.error_type}")
    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        username = request.form.get("username")
        try:
            stytch_client.passwords.email.reset_start(
                email=username,
            )
            return render_template("password_reset_sent.html")
        except StytchError as e:
            return render_template("reset_password.html", error = f'Failed to send reset email. {e.details}')
    return render_template("reset_password.html", error=None)

@app.route("/complete_password_reset", methods=["GET", "POST"])
def reset_password_token():
    token = request.args.get("token", None)
    if token:
        if request.method == "POST":
            new_password = request.form.get("new_password")
            stytch_client.passwords.email.reset(
                token=token,
                password=new_password,
            )
            return redirect(url_for("login"))
        return render_template("complete_password_reset.html")
    else:
        return "Invalid reset token"

@app.route("/", methods=["GET", "POST"])
def cat_vote():
    if "username" not in session:
        return redirect(url_for("login"))
    
    """Renders the main page and handles cute/not cute submissions."""
    image_file = get_random_image()
    if image_file is None:
        return "Please add images to the static/images folder."

    if request.method == "POST":
        cute = request.form.get("cute")
        # You can store the 'cute' value in a database or file here
        # For simplicity, we just print it
        print(f"Image {image_file} marked as: {'Cute' if cute else 'Very Cute'}")
        return jsonify({"success": True}) # Return a JSON response for AJAX

    return render_template("cat_vote.html", image_file=image_file)

if __name__ == "__main__":
    app.run(debug=True)