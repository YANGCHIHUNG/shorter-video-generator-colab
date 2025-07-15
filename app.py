from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, flash, session
import os
import asyncio
import threading
import platform
import shutil
import secrets
import sys
import warnings
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from api.whisper_LLM_api import api, api_with_edited_script, api_generate_text_only
from pyngrok import ngrok
from dotenv import load_dotenv

# ✅ Suppress warnings and error messages
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Disable CUDA warnings if not needed
os.environ['XDG_RUNTIME_DIR'] = '/tmp/runtime-root'  # Fix XDG_RUNTIME_DIR warning

# Suppress ALSA warnings
try:
    import alsaaudio
    # Redirect stderr to devnull temporarily for ALSA
    stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
except ImportError:
    pass

load_dotenv()

# ✅ Flask Configuration
app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"

# ✅ Get absolute paths relative to the script directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(BASE_DIR, "output")
app.config["ALLOWED_EXTENSIONS"] = {"mp4", "pdf"}
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'users.db')}"

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
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

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
        # ✅ 立即刪除處理狀態檔案，讓用戶可以下載影片
        if os.path.exists(status_file):
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
        return jsonify({"status": "success", "message": "Processing... Please wait"}), 200
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

# ✅ Check Processing Status Endpoint
@app.route("/status")
@login_required
def check_status():
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], str(current_user.id), 'video')
    processing_file = os.path.join(user_folder, "processing.txt")
    
    if not os.path.exists(processing_file):
        # Check if there are any video files
        if os.path.exists(user_folder):
            files = [f for f in os.listdir(user_folder) if f.endswith(".mp4")]
            if files:
                return jsonify({"status": "completed", "message": "Video generation completed!"})
        return jsonify({"status": "idle", "message": "No processing in progress"})
    
    # Read the status from the file
    try:
        with open(processing_file, "r") as f:
            status_content = f.read().strip()
        
        if status_content == "processing":
            return jsonify({"status": "processing", "message": "Processing... Please wait"})
        elif status_content == "failed":
            return jsonify({"status": "failed", "message": "Processing failed"})
        else:
            return jsonify({"status": "processing", "message": "Processing... Please wait"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error checking status: {str(e)}"})

# ✅ Generate Text from PDF (First Stage)
@app.route("/generate_text", methods=["POST"])
@login_required
def generate_text():
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], str(current_user.id))
    os.makedirs(user_folder, exist_ok=True)
    
    try:
        pdf_file = request.files.get("pdf")
        video_file = request.files.get("video")
        extra_prompt = request.form.get("extra_prompt")

        if not pdf_file:
            app.logger.warning("⚠️ No PDF file uploaded.")
            return jsonify({"status": "error", "message": "⚠️ Please upload a PDF file."}), 400

        # Save PDF file
        pdf_path = os.path.join(user_folder, secure_filename(pdf_file.filename))
        pdf_file.save(pdf_path)

        # Save video file if provided
        video_path = None
        if video_file and video_file.filename != '':
            video_path = os.path.join(user_folder, secure_filename(video_file.filename))
            video_file.save(video_path)

        # Generate text using the new API function
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            generated_pages = loop.run_until_complete(
                api_generate_text_only(
                    pdf_file_path=pdf_path,
                    poppler_path=None,
                    num_of_pages="all",
                    extra_prompt=extra_prompt if extra_prompt else None,
                    video_path=video_path
                )
            )
            
            # Store generated text in session for the edit page
            session['generated_pages'] = generated_pages
            session['pdf_path'] = pdf_path
            session['video_path'] = video_path
            session['extra_prompt'] = extra_prompt
            
            return jsonify({
                'status': 'success',
                'pages': generated_pages,
                'message': f'Successfully generated text for {len(generated_pages)} pages'
            })
            
        except Exception as e:
            app.logger.error(f"Error generating text: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': f'Error generating text: {str(e)}'})
        
        finally:
            loop.close()
        
    except Exception as e:
        app.logger.error(f"Error in /generate_text: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Server error: {e}"}), 500

# ✅ Process Video with Edited Text (Second Stage)
@app.route("/process_with_edited_text", methods=["POST"])
@login_required
def process_with_edited_text():
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], str(current_user.id))
    
    try:
        # Get data from JSON request
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Get edited pages from request
        edited_pages = request_data.get('pages', [])
        resolution = request_data.get('resolution', 480)
        TTS_model_type = request_data.get('TTS_model_type', 'edge')
        voice = request_data.get('voice', 'zh-TW-YunJheNeural')
        
        # Get saved parameters from session
        pdf_path = session.get('pdf_path')
        video_path = session.get('video_path')
        extra_prompt = session.get('extra_prompt')
        
        app.logger.info(f"Session data - PDF: {pdf_path}, Video: {video_path}, Pages: {len(edited_pages) if edited_pages else 0}")
        
        if not pdf_path or not edited_pages:
            missing_items = []
            if not pdf_path:
                missing_items.append("PDF path")
            if not edited_pages:
                missing_items.append("edited pages")
            return jsonify({
                "status": "error", 
                "message": f"Missing required data: {', '.join(missing_items)}"
            }), 400
        
        # Validate that PDF file still exists
        if not os.path.exists(pdf_path):
            return jsonify({
                "status": "error", 
                "message": "PDF file not found. Please upload again."
            }), 400
        
        # Convert resolution to int
        try:
            resolution = int(resolution)
        except (ValueError, TypeError):
            resolution = 480
        
        # Start processing with edited content
        processing_thread = threading.Thread(
            target=run_processing_with_edited_text, 
            args=(video_path, pdf_path, edited_pages, resolution, user_folder, TTS_model_type, voice)
        )
        processing_thread.start()
        
        app.logger.info("Processing with edited text started successfully.")
        return jsonify({"status": "success", "message": "Processing... Please wait"}), 200
        
    except Exception as e:
        app.logger.error(f"Error in /process_with_edited_text: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Server error: {e}"}), 500

def run_processing_with_edited_text(video_path, pdf_path, edited_pages, resolution, user_folder, TTS_model_type, voice):
    """Background processing task with edited text"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    video_folder = os.path.join(user_folder, 'video')
    os.makedirs(video_folder, exist_ok=True)
    status_file = os.path.join(video_folder, "processing.txt")
    
    with open(status_file, "w") as f:
        f.write("processing")
    
    try:
        # Convert edited pages to script format
        edited_script = ""
        for i, page in enumerate(edited_pages):
            edited_script += f"## Page {i+1}\n{page}\n\n"
        
        # Process with edited script
        loop.run_until_complete(api_with_edited_script(
            video_path=video_path,
            pdf_file_path=pdf_path,
            edited_script=edited_script,
            poppler_path=None,
            output_audio_dir=os.path.join(user_folder, 'audio'),
            output_video_dir=os.path.join(user_folder, 'video'),
            output_text_path=os.path.join(user_folder, "text_output.txt"),
            resolution=int(resolution),
            tts_model=TTS_model_type,
            voice=voice
        ))
        
        # Clean up
        if os.path.exists(status_file):
            os.remove(status_file)
            
        app.logger.info("✅ Video Processing with Edited Text Completed!")
        
    except Exception as e:
        app.logger.error(f"❌ Error during processing with edited text: {e}", exc_info=True)
        with open(status_file, "w") as f:
            f.write("failed")
    finally:
        loop.close()

# ✅ Text Editing Page
@app.route('/edit_text')
@login_required
def edit_text():
    """Display the text editing page"""
    pages = request.args.get('pages')
    if not pages:
        flash('No generated text found. Please start from the upload page.', 'error')
        return redirect(url_for('index'))
    
    return render_template('edit_text.html')

if __name__ == "__main__":
    public_url = ngrok.connect(5001)
    print(f" * ngrok tunnel URL: 👉👉👉 {public_url} 👈👈👈 Click here!")
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
