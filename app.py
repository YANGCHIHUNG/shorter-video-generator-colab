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
from api.whisper_LLM_api import api, api_with_edited_script, api_generate_text_only
from pyngrok import ngrok
from dotenv import load_dotenv
import json
import tempfile
from pdf2image import convert_from_path
from PIL import Image
import io
import base64

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
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

# ✅ Get absolute paths relative to the script directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(BASE_DIR, "output")
app.config["ALLOWED_EXTENSIONS"] = {"mp4", "pdf"}

system_os = platform.system()

# ✅ Ensure Upload & Output Folders Exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

# ✅ Check Allowed File Types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

# ✅ Background Processing Task
def run_processing(video_path, pdf_path, num_of_pages, resolution, user_folder, TTS_model_type, extra_prompt, voice):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 🧹 清理舊檔案：在開始新處理前清除所有舊的輸出檔案
    video_folder = os.path.join(user_folder, 'video')
    audio_folder = os.path.join(user_folder, 'audio')
    
    # 刪除舊的影片和音檔
    for folder in [video_folder, audio_folder]:
        if os.path.exists(folder):
            try:
                import shutil
                shutil.rmtree(folder)
                app.logger.info(f"🗑️ Cleaned old files in: {folder}")
            except Exception as e:
                app.logger.warning(f"⚠️ Could not clean folder {folder}: {e}")
    
    # 重新建立資料夾
    os.makedirs(video_folder, exist_ok=True)
    os.makedirs(audio_folder, exist_ok=True)
    
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

# ✅ Process Video Route
@app.route("/process", methods=["POST"])
def process_video():
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user")
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

# ✅ Download Page
# ✅ Download Route - Redirect to home (download.html removed)
@app.route("/download")
def download():
    return redirect(url_for("index"))

# ✅ Secure File Download
@app.route("/download/<filename>")
def download_file(filename):
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user", 'video')
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

# ✅ List Output Files Endpoint
@app.route("/list_output_files")
def list_output_files():
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user", 'video')
    files = []
    if os.path.exists(user_folder):
        files = [f for f in os.listdir(user_folder) if f.endswith(".mp4")]
    return jsonify({"files": files})

# ✅ Delete File Endpoint
@app.route("/delete/<filename>", methods=["DELETE"])
def delete_file(filename):
    try:
        user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user", 'video')
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

# ✅ Documentation Route
@app.route("/documentation")
def documentation():
    return render_template("documentation.html")

# ✅ Check Processing Status Endpoint
@app.route("/status")
def check_status():
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user", 'video')
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
def generate_text():
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user")
    os.makedirs(user_folder, exist_ok=True)
    
    try:
        # 🧹 清除舊的 session 數據，確保新處理不受影響
        session.clear()
        
        # 🧹 同時清除 session backup 文件，避免重新載入舊數據
        backup_file = os.path.join(user_folder, "session_backup.json")
        if os.path.exists(backup_file):
            try:
                os.remove(backup_file)
                app.logger.info("🗑️ Removed old session backup file")
            except Exception as e:
                app.logger.warning(f"⚠️ Could not remove backup file: {e}")
        
        app.logger.info("🗑️ Cleared old session data for new PDF processing")
        
        pdf_file = request.files.get("pdf")
        video_file = request.files.get("video")
        extra_prompt = request.form.get("extra_prompt")
        
        # Get video generation parameters from first stage
        num_of_pages = request.form.get("num_of_pages", "all")
        TTS_model_type = request.form.get("TTS_model_type", "edge")
        resolution = request.form.get("resolution", "1080")
        voice = request.form.get("voice", "zh-TW-YunJheNeural")

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
                    poppler_path=None,  # Use system-installed Poppler
                    num_of_pages=num_of_pages,
                    extra_prompt=extra_prompt if extra_prompt else None,
                    video_path=video_path
                )
            )
            
            # Store ALL parameters in session for the edit page (with backup)
            set_session_data('generated_pages', generated_pages)
            set_session_data('pdf_path', pdf_path)
            set_session_data('video_path', video_path)
            set_session_data('extra_prompt', extra_prompt)
            set_session_data('num_of_pages', num_of_pages)
            set_session_data('TTS_model_type', TTS_model_type)
            set_session_data('resolution', int(resolution))
            set_session_data('voice', voice)
            
            # 重要：立即驗證session數據的正確性
            stored_pdf_path = get_session_data('pdf_path')
            if stored_pdf_path != pdf_path:
                app.logger.error(f"❌ Session data verification failed! Expected: {pdf_path}, Got: {stored_pdf_path}")
                # 強制重新設置
                session['pdf_path'] = pdf_path
                app.logger.info(f"🔧 Force reset PDF path in session: {pdf_path}")
            else:
                app.logger.info(f"✅ Session data verification passed: {stored_pdf_path}")
            
            # Debug logging
            app.logger.info(f"Session data saved - PDF: {pdf_path}, Video: {video_path}, Pages: {len(generated_pages)}")
            app.logger.info(f"Session keys after saving: {list(session.keys())}")
            
            return jsonify({
                'status': 'success',
                'pages': generated_pages,
                'message': f'Successfully generated text for {len(generated_pages)} pages'
            })
            
        except Exception as e:
            error_message = str(e)
            app.logger.error(f"Error generating text: {e}", exc_info=True)
            
            # Handle different types of errors with user-friendly messages
            if "503" in error_message or "UNAVAILABLE" in error_message or "overloaded" in error_message:
                return jsonify({
                    'status': 'error', 
                    'message': '🚫 AI 服務目前過載，請稍後再試。這是暫時性問題，通常幾分鐘後就會恢復正常。'
                })
            elif "RESOURCE_EXHAUSTED" in error_message or "429" in error_message:
                return jsonify({
                    'status': 'error', 
                    'message': '⏰ API 配額已用完，請稍後再試或檢查 API 金鑰配置。'
                })
            elif "500" in error_message or "INTERNAL" in error_message:
                return jsonify({
                    'status': 'error', 
                    'message': '🔧 AI 服務內部錯誤，請稍後再試。'
                })
            elif "401" in error_message or "UNAUTHORIZED" in error_message:
                return jsonify({
                    'status': 'error', 
                    'message': '🔑 API 金鑰無效或已過期，請檢查配置。'
                })
            else:
                return jsonify({
                    'status': 'error', 
                    'message': f'❌ 文本生成失敗：{error_message}'
                })
        
        finally:
            loop.close()
        
    except Exception as e:
        app.logger.error(f"Error in /generate_text: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Server error: {e}"}), 500

# ✅ Process Video with Edited Text (Second Stage)
@app.route("/process_with_edited_text", methods=["POST"])
def process_with_edited_text():
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user")
    
    try:
        # Get data from JSON request
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Get edited pages from request
        edited_pages = request_data.get('pages', [])
        resolution = request_data.get('resolution', 1080)
        TTS_model_type = request_data.get('TTS_model_type', 'edge')
        voice = request_data.get('voice', 'zh-TW-YunJheNeural')
        enable_subtitles = request_data.get('enable_subtitles', False)
        subtitle_style = request_data.get('subtitle_style', 'default')
        traditional_chinese = request_data.get('traditional_chinese', False)
        
        # Get saved parameters from session (with backup fallback)
        # 但首先檢查 backup 文件是否存在，如果不存在說明是新的處理會話
        backup_file = os.path.join(user_folder, "session_backup.json")
        if not os.path.exists(backup_file):
            app.logger.warning("⚠️ No session backup found, session data might be incomplete")
            return jsonify({"status": "error", "message": "Session expired, please upload PDF again"}), 400
        
        pdf_path = get_session_data('pdf_path')
        video_path = get_session_data('video_path')
        extra_prompt = get_session_data('extra_prompt')
        
        # Enhanced debug logging
        app.logger.info(f"Session data - PDF: {pdf_path}, Video: {video_path}, Pages: {len(edited_pages) if edited_pages else 0}")
        app.logger.info(f"Session keys: {list(session.keys())}")
        app.logger.info(f"Request data keys: {list(request_data.keys())}")
        
        if not pdf_path or not edited_pages:
            missing_items = []
            if not pdf_path:
                missing_items.append("PDF path")
                app.logger.error(f"PDF path is missing from session. Session PDF path: {pdf_path}")
            if not edited_pages:
                missing_items.append("edited pages")
                app.logger.error(f"Edited pages is missing from request. Pages: {edited_pages}")
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
            resolution = 1080
        
        # Start processing with edited content
        processing_thread = threading.Thread(
            target=run_processing_with_edited_text, 
            args=(video_path, pdf_path, edited_pages, resolution, user_folder, TTS_model_type, voice, enable_subtitles, subtitle_style, traditional_chinese)
        )
        processing_thread.start()
        
        app.logger.info("Processing with edited text started successfully.")
        return jsonify({"status": "success", "message": "Processing... Please wait"}), 200
        
    except Exception as e:
        app.logger.error(f"Error in /process_with_edited_text: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Server error: {e}"}), 500

def run_processing_with_edited_text(video_path, pdf_path, edited_pages, resolution, user_folder, TTS_model_type, voice, enable_subtitles=False, subtitle_style="default", traditional_chinese=False):
    """Background processing task with edited text"""
    # Add debug logging for traditional chinese parameter
    app.logger.info(f"🇹🇼 Processing with traditional_chinese={traditional_chinese}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 🧹 清理舊檔案：在開始新處理前清除所有舊的輸出檔案
    video_folder = os.path.join(user_folder, 'video')
    audio_folder = os.path.join(user_folder, 'audio')
    
    # 刪除舊的影片和音檔
    for folder in [video_folder, audio_folder]:
        if os.path.exists(folder):
            try:
                import shutil
                shutil.rmtree(folder)
                app.logger.info(f"🗑️ Cleaned old files in: {folder}")
            except Exception as e:
                app.logger.warning(f"⚠️ Could not clean folder {folder}: {e}")
    
    # 重新建立資料夾
    os.makedirs(video_folder, exist_ok=True)
    os.makedirs(audio_folder, exist_ok=True)
    
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
            poppler_path=None,  # Use system-installed Poppler
            output_audio_dir=os.path.join(user_folder, 'audio'),
            output_video_dir=os.path.join(user_folder, 'video'),
            output_text_path=os.path.join(user_folder, "text_output.txt"),
            resolution=int(resolution),
            tts_model=TTS_model_type,
            voice=voice,
            enable_subtitles=enable_subtitles,
            subtitle_style=subtitle_style,
            traditional_chinese=traditional_chinese
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
def edit_text():
    """Display the text editing page"""
    # Check if pages data is in URL parameters (from frontend redirect)
    pages_param = request.args.get('pages')
    
    # Try to get data from URL parameters first, then session
    generated_pages = []
    if pages_param:
        try:
            generated_pages = json.loads(pages_param)
            app.logger.info(f"Got pages data from URL parameter: {len(generated_pages)} pages")
        except (json.JSONDecodeError, TypeError) as e:
            app.logger.error(f"Error parsing pages parameter: {e}")
    
    # If no data from URL, try session data (with backup fallback)
    if not generated_pages:
        generated_pages = get_session_data('generated_pages', [])
        app.logger.info(f"Got pages data from session: {len(generated_pages)} pages")
    
    # Get other session data
    pdf_path = get_session_data('pdf_path')
    TTS_model_type = get_session_data('TTS_model_type', 'edge')
    resolution = get_session_data('resolution', 1080)
    voice = get_session_data('voice', 'zh-TW-YunJheNeural')
    
    app.logger.info(f"Edit text page - Session data: PDF={pdf_path}, Pages={len(generated_pages)}")
    app.logger.info(f"Edit text page - Parameters: TTS={TTS_model_type}, Resolution={resolution}, Voice={voice}")
    app.logger.info(f"Edit text page - Session keys: {list(session.keys())}")
    
    if not generated_pages:
        flash('No generated text found. Please start from the upload page.', 'error')
        return redirect(url_for('index'))
    
    # Store pages data in session for later use
    if pages_param:
        set_session_data('generated_pages', generated_pages)
    
    return render_template('edit_text.html', 
                          pages=generated_pages,
                          pages_json=json.dumps(generated_pages),  # Fix: Add missing pages_json
                          TTS_model_type=TTS_model_type,
                          resolution=resolution,
                          voice=voice)

@app.route('/pdf_preview/<int:page_num>')
def pdf_preview(page_num):
    """生成PDF頁面預覽圖片"""
    try:
        user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user")
        
        # 獲取PDF路徑
        pdf_path = get_session_data('pdf_path')
        if not pdf_path or not os.path.exists(pdf_path):
            app.logger.error(f"PDF file not found: {pdf_path}")
            return jsonify({"error": "PDF file not found"}), 404
        
        # 設置poppler路徑
        if system_os == "Windows":
            poppler_path = os.path.join(BASE_DIR, "poppler", "poppler-0.89.0", "bin")
        else:
            poppler_path = None
        
        # 轉換特定頁面為圖片
        try:
            pages = convert_from_path(
                pdf_path,
                poppler_path=poppler_path,
                first_page=page_num,
                last_page=page_num,
                dpi=300,  # 提高DPI以獲得更好的圖片質量
                thread_count=1
            )
            
            if not pages:
                return jsonify({"error": f"Page {page_num} not found"}), 404
            
            # 將圖片轉換為Base64字符串
            page_image = pages[0]
            
            # 調整圖片大小以適合預覽（寬度最大800px，保持高畫質）
            max_width = 800
            aspect_ratio = page_image.height / page_image.width
            new_width = min(max_width, page_image.width)
            new_height = int(new_width * aspect_ratio)
            
            # 只有當原圖比目標尺寸大時才縮放，否則保持原尺寸
            if page_image.width > max_width:
                resized_image = page_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                resized_image = page_image
                new_width = page_image.width
                new_height = page_image.height
            
            # 轉換為Base64，使用高質量PNG格式
            buffer = io.BytesIO()
            resized_image.save(buffer, format='PNG', optimize=False)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return jsonify({
                "success": True,
                "image": f"data:image/png;base64,{img_base64}",
                "page": page_num,
                "width": new_width,
                "height": new_height
            })
            
        except Exception as e:
            app.logger.error(f"Error converting PDF page {page_num}: {e}")
            return jsonify({"error": f"Error converting PDF page: {str(e)}"}), 500
            
    except Exception as e:
        app.logger.error(f"Error in pdf_preview: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/cleanup_files', methods=['POST'])
def cleanup_files():
    """清理所有產生的檔案並清除session數據"""
    try:
        user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user")
        
        # 要清理的資料夾
        folders_to_clean = ['video', 'audio']
        
        # 要刪除的檔案類型
        files_to_clean = []
        
        # 收集所有要刪除的檔案
        if os.path.exists(user_folder):
            # 刪除PDF檔案
            for file in os.listdir(user_folder):
                if file.endswith('.pdf'):
                    files_to_clean.append(os.path.join(user_folder, file))
            
            # 刪除text_output.txt
            text_output = os.path.join(user_folder, "text_output.txt")
            if os.path.exists(text_output):
                files_to_clean.append(text_output)
            
            # 刪除session backup
            session_backup = os.path.join(user_folder, "session_backup.json")
            if os.path.exists(session_backup):
                files_to_clean.append(session_backup)
        
        # 刪除檔案
        deleted_files = []
        for file_path in files_to_clean:
            try:
                os.remove(file_path)
                deleted_files.append(os.path.basename(file_path))
                app.logger.info(f"🗑️ Deleted file: {file_path}")
            except Exception as e:
                app.logger.warning(f"⚠️ Could not delete file {file_path}: {e}")
        
        # 刪除資料夾
        deleted_folders = []
        for folder_name in folders_to_clean:
            folder_path = os.path.join(user_folder, folder_name)
            if os.path.exists(folder_path):
                try:
                    shutil.rmtree(folder_path)
                    deleted_folders.append(folder_name)
                    app.logger.info(f"🗑️ Deleted folder: {folder_path}")
                except Exception as e:
                    app.logger.warning(f"⚠️ Could not delete folder {folder_path}: {e}")
        
        # 清除Flask session
        session.clear()
        app.logger.info("🗑️ Cleared Flask session data")
        
        return jsonify({
            'status': 'success',
            'message': 'All files cleaned successfully',
            'deleted_files': deleted_files,
            'deleted_folders': deleted_folders
        })
        
    except Exception as e:
        app.logger.error(f"❌ Error during cleanup: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Cleanup failed: {str(e)}'
        }), 500

# ✅ Session backup storage (simplified for single user)
def save_session_backup(data):
    """Save session data to a backup file"""
    backup_dir = os.path.join(app.config["OUTPUT_FOLDER"], "default_user")
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, "session_backup.json")
    
    try:
        # 特別記錄PDF路徑的保存
        if 'pdf_path' in data:
            app.logger.info(f"💾 Saving PDF path to backup: {data['pdf_path']}")
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        app.logger.info(f"Session backup saved to {backup_file}")
    except Exception as e:
        app.logger.error(f"Failed to save session backup: {e}")

def load_session_backup():
    """Load session data from backup file"""
    backup_dir = os.path.join(app.config["OUTPUT_FOLDER"], "default_user")
    backup_file = os.path.join(backup_dir, "session_backup.json")
    
    if not os.path.exists(backup_file):
        return {}
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        app.logger.info(f"Session backup loaded from {backup_file}")
        return data
    except Exception as e:
        app.logger.error(f"Failed to load session backup: {e}")
        return {}

def get_session_data(key, default=None):
    """Get session data with backup fallback"""
    # Try Flask session first
    value = session.get(key, default)
    
    # 特別記錄PDF路徑的獲取
    if key == 'pdf_path':
        app.logger.info(f"🔍 Getting PDF path - Session value: {value}")
    
    # If not found, try backup
    if value is None:
        backup_data = load_session_backup()
        value = backup_data.get(key, default)
        
        if key == 'pdf_path':
            app.logger.info(f"🔍 PDF path from backup: {value}")
        
        # If found in backup, restore to session
        if value is not None:
            session[key] = value
            if key == 'pdf_path':
                app.logger.info(f"🔄 Restored PDF path to session: {value}")
    
    return value

def set_session_data(key, value):
    """Set session data with backup"""
    session[key] = value
    
    # 特別記錄PDF路徑的設置
    if key == 'pdf_path':
        app.logger.info(f"🔧 Setting PDF path in session: {value}")
    
    # Also save to backup
    backup_data = load_session_backup()
    backup_data[key] = value
    save_session_backup(backup_data)
    
    # 驗證設置是否成功
    if key == 'pdf_path':
        app.logger.info(f"✅ PDF path verification - Session: {session.get(key)}, Backup will contain: {backup_data.get(key)}")

if __name__ == "__main__":
    try:
        public_url = ngrok.connect(5001)
        print(f" * ngrok tunnel URL: 👉👉👉 {public_url} 👈👈👈 Click here!")
    except Exception as e:
        print(f" * ngrok failed: {e}")
        print(" * Running locally without ngrok")
    
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
