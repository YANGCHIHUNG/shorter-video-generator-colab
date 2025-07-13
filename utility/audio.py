import os
import whisper
from moviepy.editor import VideoFileClip
import torch
import subprocess
def convert_mp4_to_mp3(input_file, output_file=None, bitrate="64k", sample_rate="32000"):
    if not output_file:
        output_file = os.path.splitext(input_file)[0] + ".mp3"
    

    try:
        command = [
            "ffmpeg", "-i", input_file, "-vn",  # Ignore video
            "-b:a", bitrate, "-ar", sample_rate, "-ac", "1",  # Lower quality settings
            "-map", "0:a", "-compression_level", "0",  # Faster audio extraction
            "-preset", "ultrafast", "-y", output_file  # Fastest encoding settings
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"Conversion successful: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error converting {input_file}: {e}")
        return None

def transcribe_audio(audio_path, model_size="medium"):  # Load large Whisper model
    if not os.path.exists(audio_path):
        print(f"Error: File {audio_path} not found.")
        return
    # Determine the device: use GPU if available, otherwise CPU.
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading Whisper model: {model_size} on {device}")

    model = whisper.load_model(model_size).to(device)
    print("Start transcribing...")
    result = model.transcribe(audio_path)
    print("Transcription:")
    print(result.get("text", "No transcription available."))
    return result
