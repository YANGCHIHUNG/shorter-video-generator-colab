from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, flash, session
import os
import asyncio
import threading
import platform
import shutil
import secrets
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from api.whisper_LLM_api import api
from pyngrok import ngrok
from dotenv import load_dotenv

load_dotenv()

# ✅ Flask Configuration
app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["OUTPUT_FOLDER"] = "output"
app.config["ALLOWED_EXTENSIONS"] = {"mp4", "pdf"}
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"

system_os = platform.system()
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ✅ Admin Credentials
admin_account = os.getenv("admin_account")
admin_password = os.getenv("admin_password")

# ✅ Ensure Upload & Output Folders Exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

# ✅ User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ Check Allowed File Types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

# ✅ Background Processing Task
def run_processing(video_path, pdf_path, num_of_pages, resolution, user_folder, TTS_model_type, extra_prompt, voice):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    video_folder = os.path.join(user_folder, 'video')
    os.makedirs(video_folder, exist_ok=True)
    status_file = os.path.join(video_folder, "processing.txt")
    with open(status_file, "w") as f:
        f.write("processing")
    try:
        loop.run_until_complete(api(
            video_path=video_path,
            pdf_file_path=pdf_path,
            poppler_path=None,
            output_audio_dir=os.path.join(user_folder, 'audio'),
            output_video_dir=os.path.join(user_folder, 'video'),
            output_text_path=os.path.join(user_folder, "text_output.txt"),
            num_of_pages=num_of_pages,
            resolution=int(resolution),
            tts_model=TTS_model_type,
            extra_prompt=extra_prompt,
            voice=voice
        ))
        os.remove(status_file)
        app.logger.info("✅ Video Processing Completed!")
    except Exception as e:
        app.logger.error(f"❌ Error during processing: {e}", exc_info=True)
        with open(status_file, "w") as f:
            f.write("failed")

# ✅ Home Route
@app.route("/")
def index():
    return render_template("index.html")

# ✅ Signup Route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        if User.query.filter_by(email=email).first():
            flash("⚠️ Email already registered!", "error")
            return redirect(url_for("signup"))
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("✅ Account created! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("signup.html")

# ✅ Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        # ✅ Admin Login Check
        if email == admin_account and password == admin_password:
            user = User.query.filter_by(email=admin_account).first()
            if not user:
                admin_hashed = bcrypt.generate_password_hash(admin_password).decode("utf-8")
                user = User(email=admin_account, password=admin_hashed)
                db.session.add(user)
                db.session.commit()
            login_user(user)
            token = secrets.token_hex(16)
            session["admin_token"] = token
            flash("✅ Admin logged in successfully!", "success")
            return redirect(url_for("admin_dashboard", token=token))
        # ✅ Normal User Login
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("✅ Logged in successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("❌ Invalid email or password.", "error")
    return render_template("login.html")

# ✅ Logout Route
@app.route("/logout")
@login_required
def logout():
    session.pop("admin_token", None)
    logout_user()
    flash("🔓 Logged out successfully.", "success")
    return redirect(url_for("index"))

# ✅ Process Video Route
@app.route("/process", methods=["POST"])
@login_required
def process_video():
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], str(current_user.id))
    os.makedirs(user_folder, exist_ok=True)
    try:
        video_file = request.files.get("video")
        pdf_file = request.files.get("pdf")
        resolution = request.form.get("resolution")
        num_of_pages = request.form.get('num_of_pages')
        TTS_model_type = request.form.get("TTS_model_type")
        extra_prompt = request.form.get("extra_prompt")
        voice = request.form.get("voice")

        if not pdf_file:
            app.logger.warning("⚠️ No PDF file uploaded.")
            return jsonify({"status": "error", "message": "⚠️ Please upload a PDF file."}), 400

        if video_file and video_file.filename != "":
            video_path = os.path.join(user_folder, secure_filename(video_file.filename))
            video_file.save(video_path)
        else:
            video_path = None
            app.logger.info("No video file uploaded; proceeding without video.")

        pdf_path = os.path.join(user_folder, secure_filename(pdf_file.filename))
        pdf_file.save(pdf_path)

        processing_thread = threading.Thread(
            target=run_processing, args=(
                video_path, pdf_path, num_of_pages, resolution, user_folder, TTS_model_type, extra_prompt, voice
            )
        )
        processing_thread.start()
        app.logger.info("Processing thread started successfully.")
        return jsonify({"status": "success", "message": "🚀 Processing started!"}), 200
    except Exception as e:
        app.logger.error(f"Error in /process: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Server error: {e}"}), 500

# ✅ Download Page (User Restricted)
@app.route("/download")
@login_required
def download():
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], str(current_user.id), 'video')
    processing_file = os.path.join(user_folder, "processing.txt")
    is_processing = os.path.exists(processing_file)
    files = []
    if os.path.exists(user_folder) and not is_processing:
        files = [f for f in os.listdir(user_folder) if f.endswith(".mp4")]
    return render_template("download.html", files=files, is_processing=is_processing)

# ✅ Secure File Download
@app.route("/download/<filename>")
@login_required
def download_file(filename):
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], str(current_user.id), 'video')
    if not filename:
        flash("⚠️ Invalid file request!", "error")
        return redirect(url_for("download"))
    secure_file = secure_filename(filename.strip())
    file_path = os.path.join(user_folder, secure_file)
    app.logger.info(f"📂 Looking for: {file_path}")
    app.logger.info(f"🛠️ File Exists: {os.path.exists(file_path)}")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("⚠️ File not found!", "error")
        return redirect(url_for("download"))

# ✅ Delete File Endpoint (User Restricted)
@app.route("/delete/<filename>", methods=["DELETE"])
@login_required
def delete_file(filename):
    try:
        user_folder = os.path.join(app.config["OUTPUT_FOLDER"], str(current_user.id), 'video')
        file_path = os.path.join(user_folder, secure_filename(filename))
        if os.path.exists(file_path):
            os.remove(file_path)
            app.logger.info(f"File deleted: {file_path}")
            return jsonify({"status": "success", "message": "File deleted successfully!"})
        else:
            app.logger.warning(f"File not found for deletion: {file_path}")
            return jsonify({"status": "error", "message": "File not found."}), 404
    except Exception as e:
        app.logger.error(f"Error deleting file: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Error deleting file: {str(e)}"}), 500

# ✅ Admin Dashboard: List All Users with Temporary Token
@app.route("/admin/<token>")
@login_required
def admin_dashboard(token):
    if current_user.email != admin_account or session.get("admin_token") != token:
        flash("⚠️ Unauthorized access!", "error")
        return redirect(url_for("index"))
    users = User.query.all()
    return render_template("admin_dashboard.html", users=users, token=token, admin_account=admin_account)

# ✅ Admin Delete User Endpoint with Temporary Token
@app.route("/admin/<token>/delete_user/<int:user_id>", methods=["POST"])
@login_required
def admin_delete_user(token, user_id):
    if current_user.email != admin_account or session.get("admin_token") != token:
        flash("⚠️ Unauthorized action!", "error")
        return redirect(url_for("index"))
    user = User.query.get(user_id)
    if user:
        user_folder = os.path.join(app.config["OUTPUT_FOLDER"], str(user.id))
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder)
        db.session.delete(user)
        db.session.commit()
        flash("✅ User deleted successfully!", "success")
    else:
        flash("⚠️ User not found!", "error")
    return redirect(url_for("admin_dashboard", token=token))

# ✅ Initialize Database
with app.app_context():
    db.create_all()

@app.route("/documentation")
def documentation():
    return render_template("documentation.html")

if __name__ == "__main__":
    public_url = ngrok.connect(5001)
    print(f" * ngrok tunnel URL: {public_url}")
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
