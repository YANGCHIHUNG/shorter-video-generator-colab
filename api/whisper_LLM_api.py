import os
import sys
import asyncio
import time
import logging
import subprocess
import nest_asyncio
from tqdm import tqdm
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
from dotenv import load_dotenv

# Logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

# Add parent directory to sys.path to import custom utility modules
parent_dir = os.path.join(os.getcwd(), "..")
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utility.audio import *
from utility.pdf import *
from utility.api import *

load_dotenv()
THREAD_COUNT = int(os.getenv("THREAD_COUNT", "4"))
nest_asyncio.apply()

# Resolution Mapping
RESOLUTION_MAP = {
    144: (256, 144),   # 144p
    240: (426, 240),   # 240p
    360: (640, 360),   # 360p
    480: (854, 480),   # 480p
    720: (1280, 720),  # 720p
}

def ensure_directories_exist(*dirs):
    """
    Creates directories if they do not exist.
    :param dirs: List of directory paths to create.
    """
    for directory in dirs:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"📁 Created missing directory: {directory}")

async def api(
    video_path: str,
    pdf_file_path: str,
    poppler_path: str,
    output_audio_dir: str,
    output_video_dir: str,
    output_text_path: str,
    num_of_pages="all",
    resolution: int = 480,
    tts_model: str = 'edge',
    extra_prompt: str = None,
    voice: str = None
):
    logger.info("🚀 Starting the process...")

    ensure_directories_exist(output_audio_dir, output_video_dir, os.path.dirname(output_text_path))

    # Validate resolution input
    if resolution not in RESOLUTION_MAP:
        logger.error(f"⚠️ Invalid resolution selected: {resolution}p. Defaulting to 480p.")
        resolution = 480
    TARGET_WIDTH, TARGET_HEIGHT = RESOLUTION_MAP[resolution]
    logger.info(f"📏 Selected Resolution: {resolution}p ({TARGET_WIDTH}x{TARGET_HEIGHT})")

    if video_path is None:
        logger.info("No MP4 passed in. Go on processing without video.")
        script = "No video for this file. Please use the passage only to generate."
    else:
        # Step 1: Convert MP4 to MP3
        logger.info(f"🎵 Converting MP4 to MP3: {video_path}")
        try:
            audio = convert_mp4_to_mp3(video_path)
        except Exception as e:
            logger.error(f"❌ Error converting MP4 to MP3: {e}", exc_info=True)
            raise

        # Step 2: Transcribe the audio
        logger.info("📝 Transcribing audio to text...")
        try:
            script = transcribe_audio(audio, model_size="base")['text']
        except Exception as e:
            logger.error(f"❌ Error during audio transcription: {e}", exc_info=True)
            raise

    if extra_prompt:
        logger.info(f"📝 Adding extra prompt to script: {extra_prompt}")
        script += f"\n\n this is the extra prompt instructed by the user: {extra_prompt}"

    # Step 4: Get API key and process PDF
    try:
        keys = eval(os.getenv("api_key"))
    except Exception as e:
        logger.error(f"❌ Error loading API key: {e}", exc_info=True)
        raise

    logger.info(f"📄 Extracting text from PDF: {pdf_file_path}")

    # Detect total number of pages if 'all' is set
    try:
        if num_of_pages == "all":
            total_pages = len(convert_from_path(
                pdf_file_path, poppler_path=poppler_path, thread_count=THREAD_COUNT
            ))
            logger.info(f"📚 Detected total pages: {total_pages}")
        else:
            try:
                total_pages = int(num_of_pages)
                logger.info(f"📃 Selected Number of Pages: {num_of_pages}")
            except Exception:
                total_pages = len(convert_from_path(
                    pdf_file_path, poppler_path=poppler_path, thread_count=THREAD_COUNT
                ))
                logger.info(f"📚 Detected total pages (fallback): {total_pages}")
    except Exception as e:
        logger.error(f"❌ Error reading PDF pages: {e}", exc_info=True)
        raise

    try:
        text_array = pdf_to_text_array(pdf_file_path)
    except Exception as e:
        logger.error(f"❌ Error extracting text from PDF: {e}", exc_info=True)
        raise

    # Step 5: Use AI model to generate responses
    logger.info(f"🤖 Generating AI responses for {total_pages} pages...")
    try:
        response_array = gemini_chat(text_array[:total_pages], script=script, keys=keys)
    except Exception as e:
        logger.error(f"❌ Error during AI response generation: {e}", exc_info=True)
        raise

    # Step 6: Convert AI-generated text to speech (without saving permanently)
    logger.info("🔊 Generating speech from AI responses...")
    audio_files = []
    tasks = []
    try:
        for idx, response in enumerate(tqdm(response_array, desc="Processing Audio")):
            filename = f"audio_{idx}.mp3"
            if tts_model == 'edge':
                if voice is None:
                    voice = "zh-TW-YunJheNeural"
                logger.info(f"🎤 Processing segment {idx} with voice: {voice}")
                tasks.append(edge_tts_example(response, output_audio_dir, filename, voice))
            elif tts_model == 'kokoro':
                tasks.append(kokoro_tts_example(response, output_audio_dir, filename))
        
        # Gather results - fail immediately if any task fails
        audio_files = await asyncio.gather(*tasks)
        
        # Strict validation - all audio files must be successfully generated
        failed_indices = []
        for idx, audio_file in enumerate(audio_files):
            if audio_file is None:
                failed_indices.append(idx)
                logger.error(f"❌ Audio file for segment {idx} was not generated (returned None).")
            elif not os.path.exists(audio_file):
                failed_indices.append(idx)
                logger.error(f"❌ Audio file for segment {idx} does not exist: {audio_file}")
            elif os.path.getsize(audio_file) == 0:
                failed_indices.append(idx)
                logger.error(f"❌ Audio file for segment {idx} is empty: {audio_file}")
            else:
                # Log successful files for debugging
                file_size = os.path.getsize(audio_file)
                logger.info(f"✅ Audio file for segment {idx} successfully created: {audio_file} ({file_size} bytes)")
        
        # If any audio file failed, stop the entire process
        if failed_indices:
            error_msg = f"❌ {len(failed_indices)} out of {len(audio_files)} audio files failed to generate properly. Failed segments: {failed_indices}"
            logger.error(error_msg)
            
            # Log the successful files count for debugging
            successful_count = len(audio_files) - len(failed_indices)
            logger.info(f"📊 Summary: {successful_count} successful, {len(failed_indices)} failed out of {len(audio_files)} total")
            
            raise RuntimeError(f"TTS 音訊生成失敗。必須所有音檔都成功生成才能繼續製作影片。失敗的段落: {failed_indices}")
        
        logger.info(f"✅ All {len(audio_files)} audio files generated successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during TTS generation: {e}", exc_info=True)
        raise

    # Step 7: Convert PDF pages to images
    logger.info(f"🖼️ Converting {total_pages} PDF pages to images...")
    try:
        pages = convert_from_path(
            pdf_file_path,
            poppler_path=poppler_path,
            first_page=1,
            last_page=total_pages,
            thread_count=THREAD_COUNT
        )
    except Exception as e:
        logger.error(f"❌ PDF to image conversion failed: {e}", exc_info=True)
        raise

    logger.info("🎬 Creating video clips...")
    video_clips = []
    try:
        for idx, (img, audio_file) in enumerate(tqdm(zip(pages, audio_files), total=len(audio_files), desc="Processing Videos")):
            img_resized = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.LANCZOS)
            frame = np.array(img_resized)
            
            # All audio files are guaranteed to exist at this point
            audioclip = AudioFileClip(audio_file)
            duration = audioclip.duration
            image_clip = ImageClip(frame).set_duration(duration)
            video_clip = image_clip.set_audio(audioclip)
            video_clips.append(video_clip)
    except Exception as e:
        logger.error(f"❌ Error during video clip creation: {e}", exc_info=True)
        raise

    # Step 10: Concatenate video clips
    logger.info("📹 Concatenating video clips...")
    try:
        final_video = concatenate_videoclips(video_clips, method="chain")
    except Exception as e:
        logger.error(f"❌ Error during video concatenation: {e}", exc_info=True)
        raise

    # Step 12: Export final video
    output_video_path = os.path.join(output_video_dir, f"output_video_{resolution}p.mp4")
    logger.info(f"📤 Exporting final video to: {output_video_path}")
    try:
        final_video.write_videofile(
            output_video_path,
            fps=24,
            logger=None,
            audio_bitrate="50k",
            write_logfile=False,
            threads=THREAD_COUNT,
            ffmpeg_params=[
                "-b:v", "5M",
                "-preset", "ultrafast",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-pix_fmt", "yuv420p",
            ],
        )
    except Exception as e:
        logger.error(f"❌ Video export failed: {e}", exc_info=True)
        raise

    # Cleanup temporary files
    temp_audiofile = os.path.join(output_audio_dir, "output_videoTEMP_MPY_wvf_snd.mp3")
    time.sleep(3)
    try:
        if os.path.exists(temp_audiofile):
            os.remove(temp_audiofile)
            logger.info(f"✅ Deleted temp audio file: {temp_audiofile}")
    except PermissionError:
        logger.warning(f"⚠️ Warning: Could not delete {temp_audiofile}. It might still be in use.")

    # Remove the transcript text file
    if os.path.exists(output_text_path):
        try:
            os.remove(output_text_path)
            logger.info(f"✅ Deleted transcript file: {output_text_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete transcript file: {e}")

    logger.info("✅ Cleanup process completed!")

if __name__ == "__main__":
    asyncio.run(api(
        video_path="../video/video1.mp4",
        pdf_file_path="../pdf/1_Basics_1.pdf",
        poppler_path=None,
        output_audio_dir="../output_audio",
        output_video_dir="../output_video",
        output_text_path="../output_text/text_output.txt",
        num_of_pages=1,  # Set to 'all' for full PDF processing
        resolution=480
    ))
