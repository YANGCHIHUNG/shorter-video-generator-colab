import os
import sys
import asyncio
import time
import logging
import subprocess
import nest_asyncio
import warnings
from tqdm import tqdm
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
from dotenv import load_dotenv

# Suppress audio system warnings for headless environments (like Colab)
os.environ.setdefault('ALSA_PCM_CARD', '0')
os.environ.setdefault('ALSA_PCM_DEVICE', '0')
os.environ.setdefault('XDG_RUNTIME_DIR', '/tmp/runtime-root')

# Suppress common warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

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

# Import with error handling for Colab environment
try:
    from utility.whisper_subtitle import WhisperSubtitleGenerator
    SUBTITLE_AVAILABLE = True
    logger.info("✅ Subtitle functionality available")
except ImportError as e:
    logger.warning(f"⚠️ Subtitle functionality not available: {e}")
    WhisperSubtitleGenerator = None
    SUBTITLE_AVAILABLE = False

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
    1080: (1920, 1080), # 1080p
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
    resolution: int = 1080,
    tts_model: str = 'edge',
    extra_prompt: str = None,
    voice: str = None
):
    logger.info("🚀 Starting the process...")

    ensure_directories_exist(output_audio_dir, output_video_dir, os.path.dirname(output_text_path))

    # Validate resolution input
    if resolution not in RESOLUTION_MAP:
        logger.error(f"⚠️ Invalid resolution selected: {resolution}p. Defaulting to 1080p.")
        resolution = 1080
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

async def api_with_edited_script(video_path, pdf_file_path, edited_script, poppler_path, output_audio_dir, output_video_dir, output_text_path, resolution, tts_model, voice, enable_subtitles=False, subtitle_style="default"):
    """
    API function to process video with pre-edited script content
    Args:
        enable_subtitles: Whether to generate and embed subtitles
        subtitle_style: Style for subtitles ('default', 'yellow', 'white_box', 'custom')
    """
    logger.info("🎬 Starting video processing with edited script...")
    
    # Ensure directories exist
    ensure_directories_exist(output_audio_dir, output_video_dir, os.path.dirname(output_text_path))
    
    # Validate resolution input
    if resolution not in RESOLUTION_MAP:
        logger.error(f"⚠️ Invalid resolution selected: {resolution}p. Defaulting to 1080p.")
        resolution = 1080
    TARGET_WIDTH, TARGET_HEIGHT = RESOLUTION_MAP[resolution]
    logger.info(f"📏 Selected Resolution: {resolution}p ({TARGET_WIDTH}x{TARGET_HEIGHT})")
    
    # Save the edited script
    with open(output_text_path, 'w', encoding='utf-8') as f:
        f.write(edited_script)
    
    # Parse edited script into pages
    pages = []
    current_page = ""
    
    for line in edited_script.split('\n'):
        if line.strip().startswith('## Page') or line.strip().startswith('# Page'):
            if current_page.strip():
                pages.append(current_page.strip())
            current_page = ""
        else:
            current_page += line + '\n'
    
    if current_page.strip():
        pages.append(current_page.strip())
    
    logger.info(f"📝 Parsed {len(pages)} pages from edited script")
    
    # Convert PDF pages to images
    logger.info(f"🖼️ Converting PDF pages to images...")
    try:
        pdf_images = convert_from_path(
            pdf_file_path,
            poppler_path=poppler_path,
            thread_count=THREAD_COUNT
        )
        logger.info(f"✅ Successfully converted {len(pdf_images)} PDF pages to images")
    except Exception as e:
        logger.error(f"❌ PDF to image conversion failed: {e}", exc_info=True)
        raise
    
    # Generate audio for each page
    logger.info("🔊 Generating speech from edited text...")
    audio_files = []
    tasks = []
    
    try:
        for idx, page_text in enumerate(pages):
            if not page_text.strip():
                continue
                
            filename = f"audio_{idx}.mp3"
            if tts_model == 'edge':
                if voice is None:
                    voice = "zh-TW-YunJheNeural"
                logger.info(f"🎤 Processing segment {idx} with voice: {voice}")
                tasks.append(edge_tts_example(page_text, output_audio_dir, filename, voice))
        
        # Generate all audio files
        audio_files = await asyncio.gather(*tasks)
        
        # Validate audio files
        valid_audio_files = []
        for idx, audio_file in enumerate(audio_files):
            if audio_file and os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                valid_audio_files.append(audio_file)
                logger.info(f"✅ Audio file for segment {idx} created: {audio_file}")
            else:
                logger.error(f"❌ Audio file for segment {idx} failed")
                raise RuntimeError(f"Audio generation failed for segment {idx}")
        
        logger.info(f"✅ All {len(valid_audio_files)} audio files generated successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during TTS generation: {e}", exc_info=True)
        raise

    # Create video clips
    logger.info("🎬 Creating video clips...")
    video_clips = []
    
    try:
        for idx, (img, audio_file) in enumerate(zip(pdf_images, valid_audio_files)):
            # Resize image to target resolution
            img_resized = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.LANCZOS)
            frame = np.array(img_resized)
            
            # Create audio and video clips
            audioclip = AudioFileClip(audio_file)
            duration = audioclip.duration
            image_clip = ImageClip(frame).set_duration(duration)
            video_clip = image_clip.set_audio(audioclip)
            video_clips.append(video_clip)
            
            logger.info(f"✅ Video clip {idx} created (duration: {duration:.2f}s)")
    
    except Exception as e:
        logger.error(f"❌ Error during video clip creation: {e}", exc_info=True)
        raise

    # Concatenate and export final video
    logger.info("📹 Concatenating video clips...")
    try:
        final_video = concatenate_videoclips(video_clips, method="chain")
        
        output_video_path = os.path.join(output_video_dir, f"output_video_{resolution}p.mp4")
        logger.info(f"📤 Exporting final video to: {output_video_path}")
        
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
        
        # Clean up
        final_video.close()
        for clip in video_clips:
            clip.close()
        
        # Process subtitles if enabled
        if enable_subtitles:
            logger.info("🎯 Processing subtitles...")
            
            if not SUBTITLE_AVAILABLE or WhisperSubtitleGenerator is None:
                logger.warning("⚠️ Subtitle functionality not available. Skipping subtitle generation.")
                logger.info("💡 To enable subtitles, install: pip install openai-whisper")
            else:
                try:
                    subtitle_generator = WhisperSubtitleGenerator()
                    
                    # Create temporary video path for subtitle processing
                    temp_video_path = output_video_path.replace('.mp4', '_temp.mp4')
                    os.rename(output_video_path, temp_video_path)
                    
                    # Generate and embed subtitles
                    success = subtitle_generator.process_video_with_subtitles(
                        input_video_path=temp_video_path,
                        output_video_path=output_video_path,
                        subtitle_style=subtitle_style,
                        language=None  # Use auto-detection (None instead of "auto")
                    )
                    
                    if success:
                        logger.info("✅ Subtitles added successfully!")
                        # Remove temporary video file
                        if os.path.exists(temp_video_path):
                            os.remove(temp_video_path)
                    else:
                        logger.warning("⚠️ Subtitle generation failed, keeping original video")
                        # Restore original video if subtitle processing failed
                        if os.path.exists(temp_video_path):
                            os.rename(temp_video_path, output_video_path)
                            
                except Exception as e:
                    logger.error(f"❌ Error processing subtitles: {e}")
                    # Restore original video if subtitle processing failed
                    temp_video_path = output_video_path.replace('.mp4', '_temp.mp4')
                    if os.path.exists(temp_video_path):
                        os.rename(temp_video_path, output_video_path)
        
        logger.info("✅ Video processing with edited script completed!")
        
    except Exception as e:
        logger.error(f"❌ Error during video export: {e}", exc_info=True)
        raise

async def api_generate_text_only(
    pdf_file_path: str,
    poppler_path: str,
    num_of_pages="all",
    extra_prompt: str = None,
    video_path: str = None
):
    """
    Generate text responses from PDF without creating audio or video.
    Returns an array of text responses for each page.
    """
    logger.info("📝 Starting text generation process...")
    
    # Process video if provided
    if video_path is None:
        logger.info("No MP4 passed in. Go on processing without video.")
        script = "No video for this file. Please use the passage only to generate."
    else:
        # Convert MP4 to MP3 and transcribe
        logger.info(f"🎵 Converting MP4 to MP3: {video_path}")
        try:
            audio = convert_mp4_to_mp3(video_path)
            script = transcribe_audio(audio, model_size="base")['text']
        except Exception as e:
            logger.error(f"❌ Error processing video: {e}", exc_info=True)
            raise

    # Add extra prompt if provided
    if extra_prompt:
        logger.info(f"📝 Adding extra prompt to script: {extra_prompt}")
        script += f"\n\n this is the extra prompt instructed by the user: {extra_prompt}"

    # Get API key
    try:
        keys = eval(os.getenv("api_key"))
    except Exception as e:
        logger.error(f"❌ Error loading API key: {e}", exc_info=True)
        raise

    logger.info(f"📄 Extracting text from PDF: {pdf_file_path}")

    # Detect total number of pages
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

    # Extract text from PDF
    try:
        text_array = pdf_to_text_array(pdf_file_path)
    except Exception as e:
        logger.error(f"❌ Error extracting text from PDF: {e}", exc_info=True)
        raise

    # Generate AI responses
    logger.info(f"🤖 Generating AI responses for {total_pages} pages...")
    try:
        response_array = gemini_chat(text_array[:total_pages], script=script, keys=keys)
        logger.info(f"✅ Successfully generated text for {len(response_array)} pages")
        return response_array
    except Exception as e:
        logger.error(f"❌ Error during AI response generation: {e}", exc_info=True)
        raise

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
