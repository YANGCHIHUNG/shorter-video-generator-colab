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
import logging
from datetime import datetime
import traceback

# ✅ 設置詳細的日誌系統
def setup_logging():
    """設置詳細的日誌配置"""
    # 創建日誌格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    
    # 配置根日誌記錄器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('app.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 創建專用的日誌記錄器
    logger = logging.getLogger('ShorterVideoGenerator')
    logger.setLevel(logging.DEBUG)
    
    return logger

# 初始化日誌
app_logger = setup_logging()

# ✅ 字體支援檢查和安裝
def ensure_chinese_font_support():
    """確保系統支援中文字體"""
    import platform
    import subprocess
    
    try:
        system = platform.system().lower()
        app_logger.info(f"🔤 檢查字體支援，系統: {system}")
        
        if system == "linux":
            # 在Linux系統中檢查和安裝中文字體
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
            ]
            
            fonts_found = [path for path in font_paths if os.path.exists(path)]
            
            if fonts_found:
                app_logger.info(f"✅ 找到中文字體支援: {fonts_found[0]}")
                return True
            else:
                app_logger.warning("⚠️ 未找到中文字體，嘗試安裝...")
                try:
                    # 嘗試安裝字體
                    subprocess.run(['apt-get', 'update'], check=False, capture_output=True)
                    subprocess.run(['apt-get', 'install', '-y', 'fonts-noto-cjk'], check=False, capture_output=True)
                    subprocess.run(['fc-cache', '-f', '-v'], check=False, capture_output=True)
                    app_logger.info("✅ 嘗試安裝中文字體完成")
                    return True
                except Exception as e:
                    app_logger.warning(f"⚠️ 字體安裝失敗: {e}")
                    return False
        else:
            # Windows/macOS 通常有基本字體支援
            app_logger.info("✅ 非Linux系統，假設有字體支援")
            return True
            
    except Exception as e:
        app_logger.error(f"❌ 字體檢查失敗: {e}")
        return False

# 啟動時檢查字體支援
ensure_chinese_font_support()

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

# ✅ 日誌中間件
@app.before_request
def log_request_info():
    """記錄每個請求的詳細信息"""
    app_logger.info(f"🌐 Request: {request.method} {request.url}")
    app_logger.info(f"📱 User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    app_logger.info(f"🔗 Referrer: {request.headers.get('Referer', 'Direct')}")
    if request.method == 'POST':
        app_logger.info(f"📦 Content-Type: {request.headers.get('Content-Type', 'Unknown')}")
        if request.is_json:
            app_logger.info(f"📋 JSON Data Keys: {list(request.json.keys()) if request.json else 'None'}")
        if request.form:
            app_logger.info(f"📝 Form Data Keys: {list(request.form.keys())}")
        if request.files:
            app_logger.info(f"📁 Files: {list(request.files.keys())}")

@app.after_request
def log_response_info(response):
    """記錄每個響應的詳細信息"""
    app_logger.info(f"📤 Response: {response.status_code} - {response.status}")
    app_logger.info(f"📊 Response Size: {response.content_length or 'Unknown'} bytes")
    return response

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
    """背景處理任務，包含詳細日誌"""
    process_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    app_logger.info(f"🚀 開始處理作業 ID: {process_id}")
    app_logger.info(f"📄 PDF路徑: {pdf_path}")
    app_logger.info(f"🎬 視頻路徑: {video_path}")
    app_logger.info(f"📊 參數 - 頁數: {num_of_pages}, 解析度: {resolution}, TTS: {TTS_model_type}, 語音: {voice}")
    app_logger.info(f"💬 額外提示: {extra_prompt[:100] if extra_prompt else 'None'}...")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app_logger.info(f"⚙️ 事件循環已設置")
        
        # 🧹 清理舊檔案：在開始新處理前清除所有舊的輸出檔案
        video_folder = os.path.join(user_folder, 'video')
        audio_folder = os.path.join(user_folder, 'audio')
        
        app_logger.info(f"🗑️ 開始清理舊檔案...")
        app_logger.info(f"🗑️ 視頻資料夾: {video_folder}")
        app_logger.info(f"🗑️ 音頻資料夾: {audio_folder}")
        
        # 刪除舊的影片和音檔
        deleted_folders = []
        for folder in [video_folder, audio_folder]:
            if os.path.exists(folder):
                try:
                    import shutil
                    file_count = len(os.listdir(folder)) if os.path.exists(folder) else 0
                    app_logger.info(f"🗑️ 清理 {folder} - 包含 {file_count} 個檔案")
                    shutil.rmtree(folder)
                    deleted_folders.append(folder)
                    app_logger.info(f"✅ 成功清理: {folder}")
                except Exception as e:
                    app_logger.error(f"❌ 清理失敗 {folder}: {e}")
        
        # 重新建立資料夾
        os.makedirs(video_folder, exist_ok=True)
        os.makedirs(audio_folder, exist_ok=True)
        app_logger.info(f"📁 重新建立資料夾完成")
        
        status_file = os.path.join(video_folder, "processing.txt")
        app_logger.info(f"📝 狀態檔案: {status_file}")
        
        with open(status_file, "w") as f:
            f.write("processing")
        app_logger.info(f"✅ 狀態檔案已建立")
        
        try:
            app_logger.info(f"🎯 開始呼叫 API 函數...")
            start_time = datetime.now()
            
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
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            app_logger.info(f"⏱️ API 處理完成，耗時: {processing_time:.2f} 秒")
            
            # ✅ 立即刪除處理狀態檔案，讓用戶可以下載影片
            if os.path.exists(status_file):
                os.remove(status_file)
                app_logger.info(f"🗑️ 狀態檔案已刪除")
            
            # 檢查輸出檔案
            video_files = [f for f in os.listdir(video_folder) if f.endswith('.mp4')] if os.path.exists(video_folder) else []
            audio_files = [f for f in os.listdir(audio_folder) if f.endswith('.mp3')] if os.path.exists(audio_folder) else []
            
            app_logger.info(f"📊 處理結果統計:")
            app_logger.info(f"  - 視頻檔案: {len(video_files)} 個")
            app_logger.info(f"  - 音頻檔案: {len(audio_files)} 個")
            
            if video_files:
                for video_file in video_files:
                    video_path_full = os.path.join(video_folder, video_file)
                    file_size = os.path.getsize(video_path_full) / (1024 * 1024)  # MB
                    app_logger.info(f"  - {video_file}: {file_size:.2f} MB")
            
            app_logger.info(f"✅ 作業 {process_id} 處理完成!")
            
        except Exception as api_error:
            app_logger.error(f"❌ API 呼叫失敗: {api_error}")
            app_logger.error(f"❌ 錯誤詳情: {traceback.format_exc()}")
            raise
            
    except Exception as e:
        app_logger.error(f"❌ 作業 {process_id} 處理失敗: {e}")
        app_logger.error(f"❌ 完整錯誤追蹤: {traceback.format_exc()}")
        
        with open(status_file, "w") as f:
            f.write("failed")
        app_logger.info(f"📝 狀態檔案已更新為失敗")
    finally:
        try:
            loop.close()
            app_logger.info(f"⚙️ 事件循環已關閉")
        except Exception as loop_error:
            app_logger.error(f"❌ 關閉事件循環失敗: {loop_error}")

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
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    app_logger.info(f"🎬 開始處理視頻請求 ID: {request_id}")
    
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user")
    os.makedirs(user_folder, exist_ok=True)
    app_logger.info(f"📁 用戶資料夾: {user_folder}")
    
    try:
        # 記錄請求參數
        app_logger.info(f"📋 表單資料:")
        for key, value in request.form.items():
            if len(str(value)) > 100:
                app_logger.info(f"  - {key}: {str(value)[:100]}... (truncated)")
            else:
                app_logger.info(f"  - {key}: {value}")
        
        app_logger.info(f"📁 上傳檔案:")
        for key, file in request.files.items():
            if file and file.filename:
                app_logger.info(f"  - {key}: {file.filename} ({file.content_type})")
            else:
                app_logger.info(f"  - {key}: None")
        
        video_file = request.files.get("video")
        pdf_file = request.files.get("pdf")
        resolution = request.form.get("resolution")
        num_of_pages = request.form.get('num_of_pages')
        TTS_model_type = request.form.get("TTS_model_type")
        extra_prompt = request.form.get("extra_prompt")
        voice = request.form.get("voice")

        if not pdf_file:
            app_logger.warning(f"⚠️ 請求 {request_id} - 沒有上傳 PDF 檔案")
            return jsonify({"status": "error", "message": "⚠️ Please upload a PDF file."}), 400

        # 處理視頻檔案
        video_path = None
        if video_file and video_file.filename != "":
            video_filename = secure_filename(video_file.filename)
            video_path = os.path.join(user_folder, video_filename)
            app_logger.info(f"💾 儲存視頻檔案: {video_path}")
            
            try:
                video_file.save(video_path)
                file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
                app_logger.info(f"✅ 視頻檔案儲存成功: {file_size:.2f} MB")
            except Exception as save_error:
                app_logger.error(f"❌ 視頻檔案儲存失敗: {save_error}")
                raise
        else:
            app_logger.info(f"📝 沒有上傳視頻檔案，僅處理 PDF")

        # 處理PDF檔案
        pdf_filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(user_folder, pdf_filename)
        app_logger.info(f"💾 儲存 PDF 檔案: {pdf_path}")
        
        try:
            pdf_file.save(pdf_path)
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
            app_logger.info(f"✅ PDF 檔案儲存成功: {file_size:.2f} MB")
        except Exception as save_error:
            app_logger.error(f"❌ PDF 檔案儲存失敗: {save_error}")
            raise

        # 啟動背景處理
        app_logger.info(f"🚀 啟動背景處理線程...")
        processing_thread = threading.Thread(
            target=run_processing, args=(
                video_path, pdf_path, num_of_pages, resolution, user_folder, TTS_model_type, extra_prompt, voice
            )
        )
        processing_thread.start()
        app_logger.info(f"✅ 請求 {request_id} - 背景處理線程已啟動")
        
        return jsonify({"status": "success", "message": "Processing... Please wait"}), 200
        
    except Exception as e:
        app_logger.error(f"❌ 請求 {request_id} 處理失敗: {e}")
        app_logger.error(f"❌ 完整錯誤追蹤: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"Server error: {e}"}), 500

# ✅ Download Page
# ✅ Download Route - Redirect to home (download.html removed)
@app.route("/download")
def download():
    return redirect(url_for("index"))

# ✅ Secure File Download
@app.route("/download/<filename>")
def download_file(filename):
    app_logger.info(f"📥 下載請求: {filename}")
    
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user", 'video')
    if not filename:
        app_logger.warning(f"⚠️ 無效的檔案請求")
        flash("⚠️ Invalid file request!", "error")
        return redirect(url_for("download"))
    
    secure_file = secure_filename(filename.strip())
    file_path = os.path.join(user_folder, secure_file)
    
    app_logger.info(f"📂 尋找檔案: {file_path}")
    app_logger.info(f"🛠️ 檔案存在: {os.path.exists(file_path)}")
    
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        app_logger.info(f"✅ 開始下載: {filename} ({file_size:.2f} MB)")
        return send_file(file_path, as_attachment=True)
    else:
        app_logger.warning(f"❌ 檔案不存在: {file_path}")
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
    
    app_logger.debug(f"🔍 檢查狀態: {processing_file}")
    
    if not os.path.exists(processing_file):
        # Check if there are any video files
        if os.path.exists(user_folder):
            files = [f for f in os.listdir(user_folder) if f.endswith(".mp4")]
            if files:
                app_logger.info(f"✅ 處理完成，找到 {len(files)} 個視頻檔案")
                return jsonify({"status": "completed", "message": "Video generation completed!"})
        app_logger.debug(f"💤 閒置狀態")
        return jsonify({"status": "idle", "message": "No processing in progress"})
    
    # Read the status from the file
    try:
        with open(processing_file, "r") as f:
            status_content = f.read().strip()
        
        app_logger.debug(f"📊 狀態檔案內容: {status_content}")
        
        if status_content == "processing":
            return jsonify({"status": "processing", "message": "Processing... Please wait"})
        elif status_content == "failed":
            app_logger.warning(f"❌ 處理失敗狀態")
            return jsonify({"status": "failed", "message": "Processing failed"})
        else:
            return jsonify({"status": "processing", "message": "Processing... Please wait"})
    except Exception as e:
        app_logger.error(f"❌ 檢查狀態失敗: {e}")
        return jsonify({"status": "error", "message": f"Error checking status: {str(e)}"})

# ✅ Generate Text from PDF (First Stage)
@app.route("/generate_text", methods=["POST"])
def generate_text():
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    app_logger.info(f"📝 開始文字生成請求 ID: {request_id}")
    
    user_folder = os.path.join(app.config["OUTPUT_FOLDER"], "default_user")
    os.makedirs(user_folder, exist_ok=True)
    
    try:
        # 🧹 清除舊的 session 數據，確保新處理不受影響
        old_session_keys = list(session.keys())
        session.clear()
        app_logger.info(f"🗑️ 清除舊 session 數據: {old_session_keys}")
        
        # 🧹 同時清除 session backup 文件，避免重新載入舊數據
        backup_file = os.path.join(user_folder, "session_backup.json")
        if os.path.exists(backup_file):
            try:
                backup_size = os.path.getsize(backup_file)
                os.remove(backup_file)
                app_logger.info(f"🗑️ 刪除舊 session backup 檔案: {backup_size} bytes")
            except Exception as e:
                app_logger.warning(f"⚠️ 無法刪除 backup 檔案: {e}")
        
        # 記錄請求參數
        app_logger.info(f"� 文字生成參數:")
        for key, value in request.form.items():
            if key == 'extra_prompt' and len(str(value)) > 100:
                app_logger.info(f"  - {key}: {str(value)[:100]}... (truncated)")
            else:
                app_logger.info(f"  - {key}: {value}")
        
        pdf_file = request.files.get("pdf")
        video_file = request.files.get("video")
        extra_prompt = request.form.get("extra_prompt")
        
        # Get video generation parameters from first stage
        num_of_pages = request.form.get("num_of_pages", "all")
        TTS_model_type = request.form.get("TTS_model_type", "edge")
        resolution = request.form.get("resolution", "1080")
        voice = request.form.get("voice", "zh-TW-YunJheNeural")

        if not pdf_file:
            app_logger.warning(f"⚠️ 請求 {request_id} - 沒有上傳 PDF 檔案")
            return jsonify({"status": "error", "message": "⚠️ Please upload a PDF file."}), 400

        # 處理檔案儲存
        pdf_filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(user_folder, pdf_filename)
        app_logger.info(f"💾 儲存 PDF 檔案: {pdf_path}")
        
        try:
            pdf_file.save(pdf_path)
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
            app_logger.info(f"✅ PDF 檔案儲存成功: {file_size:.2f} MB")
        except Exception as save_error:
            app_logger.error(f"❌ PDF 檔案儲存失敗: {save_error}")
            raise

        # Save video file if provided
        video_path = None
        if video_file and video_file.filename != '':
            video_filename = secure_filename(video_file.filename)
            video_path = os.path.join(user_folder, video_filename)
            app_logger.info(f"💾 儲存視頻檔案: {video_path}")
            
            try:
                video_file.save(video_path)
                file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
                app_logger.info(f"✅ 視頻檔案儲存成功: {file_size:.2f} MB")
            except Exception as save_error:
                app_logger.error(f"❌ 視頻檔案儲存失敗: {save_error}")
                raise

        # Generate text using the new API function
        app_logger.info(f"🎯 開始呼叫文字生成 API...")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            start_time = datetime.now()
            
            generated_pages = loop.run_until_complete(
                api_generate_text_only(
                    pdf_file_path=pdf_path,
                    poppler_path=None,  # Use system-installed Poppler
                    num_of_pages=num_of_pages,
                    extra_prompt=extra_prompt if extra_prompt else None,
                    video_path=video_path
                )
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            app_logger.info(f"⏱️ 文字生成完成，耗時: {processing_time:.2f} 秒")
            app_logger.info(f"📊 生成頁數: {len(generated_pages)}")
            
            # 記錄每頁的文字長度
            for i, page in enumerate(generated_pages):
                app_logger.info(f"  - 第 {i+1} 頁: {len(page)} 字元")
            
            # Store ALL parameters in session for the edit page (with backup)
            session_data = {
                'generated_pages': generated_pages,
                'pdf_path': pdf_path,
                'video_path': video_path,
                'extra_prompt': extra_prompt,
                'num_of_pages': num_of_pages,
                'TTS_model_type': TTS_model_type,
                'resolution': int(resolution),
                'voice': voice
            }
            
            app_logger.info(f"💾 儲存 session 數據:")
            for key, value in session_data.items():
                if key == 'generated_pages':
                    app_logger.info(f"  - {key}: {len(value)} 頁")
                elif isinstance(value, str) and len(value) > 100:
                    app_logger.info(f"  - {key}: {value[:100]}... (truncated)")
                else:
                    app_logger.info(f"  - {key}: {value}")
            
            for key, value in session_data.items():
                set_session_data(key, value)
            
            # 重要：立即驗證session數據的正確性
            stored_pdf_path = get_session_data('pdf_path')
            if stored_pdf_path != pdf_path:
                app_logger.error(f"❌ Session 數據驗證失敗! 預期: {pdf_path}, 實際: {stored_pdf_path}")
                # 強制重新設置
                session['pdf_path'] = pdf_path
                app_logger.info(f"🔧 強制重設 PDF 路徑: {pdf_path}")
            else:
                app_logger.info(f"✅ Session 數據驗證通過: {stored_pdf_path}")
            
            # Debug logging
            app_logger.info(f"📊 Session 摘要 - PDF: {pdf_path}, Video: {video_path}, 頁數: {len(generated_pages)}")
            app_logger.info(f"🔑 Session keys: {list(session.keys())}")
            
            app_logger.info(f"✅ 請求 {request_id} 文字生成完成")
            
            return jsonify({
                'status': 'success',
                'pages': generated_pages,
                'message': f'Successfully generated text for {len(generated_pages)} pages'
            })
            
        except Exception as e:
            error_message = str(e)
            app_logger.error(f"❌ 文字生成 API 失敗: {e}")
            app_logger.error(f"❌ 完整錯誤追蹤: {traceback.format_exc()}")
            
            # Handle different types of errors with user-friendly messages
            if "503" in error_message or "UNAVAILABLE" in error_message or "overloaded" in error_message:
                app_logger.warning(f"⚠️ API 服務過載")
                return jsonify({
                    'status': 'error', 
                    'message': '🚫 AI 服務目前過載，請稍後再試。這是暫時性問題，通常幾分鐘後就會恢復正常。'
                })
            elif "RESOURCE_EXHAUSTED" in error_message or "429" in error_message:
                app_logger.warning(f"⚠️ API 配額耗盡")
                return jsonify({
                    'status': 'error', 
                    'message': '⏰ API 配額已用完，請稍後再試或檢查 API 金鑰配置。'
                })
            elif "500" in error_message or "INTERNAL" in error_message:
                app_logger.warning(f"⚠️ API 服務內部錯誤")
                return jsonify({
                    'status': 'error', 
                    'message': '🔧 AI 服務內部錯誤，請稍後再試。'
                })
            elif "401" in error_message or "UNAUTHORIZED" in error_message:
                app_logger.warning(f"⚠️ API 認證失敗")
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
            app_logger.info(f"⚙️ 事件循環已關閉")
        
    except Exception as e:
        app_logger.error(f"❌ 請求 {request_id} 失敗: {e}")
        app_logger.error(f"❌ 完整錯誤追蹤: {traceback.format_exc()}")
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
        subtitle_method = request_data.get('subtitle_method', 'speech_rate')
        subtitle_style = request_data.get('subtitle_style', 'default')
        traditional_chinese = request_data.get('traditional_chinese', False)
        subtitle_length_mode = 'punctuation_only'  # 固定使用標點符號斷句
        
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
            args=(video_path, pdf_path, edited_pages, resolution, user_folder, TTS_model_type, voice, enable_subtitles, subtitle_method, subtitle_style, traditional_chinese, subtitle_length_mode)
        )
        processing_thread.start()
        
        app.logger.info("Processing with edited text started successfully.")
        return jsonify({"status": "success", "message": "Processing... Please wait"}), 200
        
    except Exception as e:
        app.logger.error(f"Error in /process_with_edited_text: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Server error: {e}"}), 500

def run_processing_with_edited_text(video_path, pdf_path, edited_pages, resolution, user_folder, TTS_model_type, voice, enable_subtitles=False, subtitle_method="speech_rate", subtitle_style="default", traditional_chinese=False, subtitle_length_mode="punctuation_only"):
    """Background processing task with edited text"""
    process_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    app_logger.info(f"✏️ 開始編輯文字處理作業 ID: {process_id}")
    
    # Add debug logging for parameters
    app_logger.info(f"📊 處理參數詳情:")
    app_logger.info(f"  - 視頻路徑: {video_path}")
    app_logger.info(f"  - PDF 路徑: {pdf_path}")
    app_logger.info(f"  - 編輯頁數: {len(edited_pages)}")
    app_logger.info(f"  - 解析度: {resolution}")
    app_logger.info(f"  - TTS 模型: {TTS_model_type}")
    app_logger.info(f"  - 語音: {voice}")
    app_logger.info(f"  - 啟用字幕: {enable_subtitles}")
    app_logger.info(f"  - 字幕方法: {subtitle_method}")
    app_logger.info(f"  - 字幕樣式: {subtitle_style}")
    app_logger.info(f"  - 繁體中文: {traditional_chinese}")
    app_logger.info(f"  - 字幕長度模式: {subtitle_length_mode}")
    
    # 記錄每頁編輯內容的長度
    for i, page in enumerate(edited_pages):
        app_logger.info(f"  - 第 {i+1} 頁: {len(page)} 字元")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app_logger.info(f"⚙️ 事件循環已設置")
    
    # 🧹 清理舊檔案：在開始新處理前清除所有舊的輸出檔案
    video_folder = os.path.join(user_folder, 'video')
    audio_folder = os.path.join(user_folder, 'audio')
    
    app_logger.info(f"🗑️ 開始清理舊檔案...")
    
    # 刪除舊的影片和音檔
    for folder in [video_folder, audio_folder]:
        if os.path.exists(folder):
            try:
                file_count = len(os.listdir(folder))
                app_logger.info(f"🗑️ 清理 {folder} - 包含 {file_count} 個檔案")
                
                import shutil
                shutil.rmtree(folder)
                app_logger.info(f"✅ 成功清理: {folder}")
            except Exception as e:
                app_logger.error(f"❌ 清理失敗 {folder}: {e}")
    
    # 重新建立資料夾
    os.makedirs(video_folder, exist_ok=True)
    os.makedirs(audio_folder, exist_ok=True)
    app_logger.info(f"📁 重新建立資料夾完成")
    
    status_file = os.path.join(video_folder, "processing.txt")
    app_logger.info(f"📝 狀態檔案: {status_file}")
    
    with open(status_file, "w") as f:
        f.write("processing")
    app_logger.info(f"✅ 狀態檔案已建立")
    
    try:
        # Convert edited pages to script format
        app_logger.info(f"📝 轉換編輯頁面為腳本格式...")
        edited_script = ""
        for i, page in enumerate(edited_pages):
            edited_script += f"## Page {i+1}\n{page}\n\n"
        
        script_length = len(edited_script)
        app_logger.info(f"📋 腳本總長度: {script_length} 字元")
        
        # Process with edited script
        app_logger.info(f"🎯 開始呼叫編輯腳本 API...")
        start_time = datetime.now()
        
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
            subtitle_method=subtitle_method,
            subtitle_style=subtitle_style,
            traditional_chinese=traditional_chinese,
            subtitle_length_mode=subtitle_length_mode
        ))
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        app_logger.info(f"⏱️ 編輯腳本 API 處理完成，耗時: {processing_time:.2f} 秒")
        
        # Clean up
        if os.path.exists(status_file):
            os.remove(status_file)
            app_logger.info(f"🗑️ 狀態檔案已刪除")
        
        # 檢查輸出檔案
        video_files = [f for f in os.listdir(video_folder) if f.endswith('.mp4')] if os.path.exists(video_folder) else []
        audio_files = [f for f in os.listdir(audio_folder) if f.endswith('.mp3')] if os.path.exists(audio_folder) else []
        
        app_logger.info(f"📊 處理結果統計:")
        app_logger.info(f"  - 視頻檔案: {len(video_files)} 個")
        app_logger.info(f"  - 音頻檔案: {len(audio_files)} 個")
        
        if video_files:
            for video_file in video_files:
                video_file_path = os.path.join(video_folder, video_file)
                file_size = os.path.getsize(video_file_path) / (1024 * 1024)  # MB
                app_logger.info(f"  - {video_file}: {file_size:.2f} MB")
        
        if enable_subtitles:
            srt_files = [f for f in os.listdir(video_folder) if f.endswith('.srt')] if os.path.exists(video_folder) else []
            app_logger.info(f"  - 字幕檔案: {len(srt_files)} 個")
            for srt_file in srt_files:
                app_logger.info(f"    - {srt_file}")
            
        app_logger.info(f"✅ 作業 {process_id} 編輯文字處理完成!")
        
    except Exception as e:
        app_logger.error(f"❌ 作業 {process_id} 編輯文字處理失敗: {e}")
        app_logger.error(f"❌ 完整錯誤追蹤: {traceback.format_exc()}")
        
        with open(status_file, "w") as f:
            f.write("failed")
        app_logger.info(f"📝 狀態檔案已更新為失敗")
    finally:
        try:
            loop.close()
            app_logger.info(f"⚙️ 事件循環已關閉")
        except Exception as loop_error:
            app_logger.error(f"❌ 關閉事件循環失敗: {loop_error}")

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
    app_logger.info(f"🚀 Shorter Video Generator 應用程式啟動")
    app_logger.info(f"💻 系統: {platform.system()} {platform.release()}")
    app_logger.info(f"🐍 Python: {sys.version}")
    app_logger.info(f"📁 基礎目錄: {BASE_DIR}")
    app_logger.info(f"📁 上傳資料夾: {app.config['UPLOAD_FOLDER']}")
    app_logger.info(f"📁 輸出資料夾: {app.config['OUTPUT_FOLDER']}")
    
    try:
        public_url = ngrok.connect(5001)
        app_logger.info(f"🌐 ngrok 隧道 URL: {public_url}")
        print(f" * ngrok tunnel URL: 👉👉👉 {public_url} 👈👈👈 Click here!")
    except Exception as e:
        app_logger.warning(f"⚠️ ngrok 失敗: {e}")
        print(f" * ngrok failed: {e}")
        print(" * Running locally without ngrok")
    
    app_logger.info(f"🌍 Flask 應用程式在 0.0.0.0:5001 啟動")
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
 