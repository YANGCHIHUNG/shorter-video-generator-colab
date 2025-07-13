from google import genai
import edge_tts
from tqdm import tqdm
import time
import itertools
import os
import torch
import numpy as np
from utility.text import *
from kokoro import KPipeline
import soundfile as sf

async def kokoro_tts_example(text, output_dir, filename, voice="zm_yunyang"):
    """
    Generates speech from text using Kokoro's KPipeline and saves it to a specific directory.
    
    :param text: Text to be converted to speech.
    :param output_dir: Directory where the audio file will be saved.
    :param filename: Name of the audio file.
    :param voice: The voice model to use.
    :return: Full path of the saved audio file.
    """
    if not text or text.strip() == "":
        print("⚠️ Warning: Received empty text for speech synthesis.")
        return None  # Skip empty text

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Define the full file path (using .wav for this example)
    output_file_path = os.path.join(output_dir, filename)
    
    try:
        # Clean the text to remove any problematic characters
        cleaned_text = text.strip()
        if len(cleaned_text) > 1000:
            print(f"⚠️ Warning: Text is very long ({len(cleaned_text)} chars), truncating...")
            cleaned_text = cleaned_text[:1000] + "..."
        
        print(f"🔊 Generating speech using voice: {voice}, Text length: {len(cleaned_text)}")
        
        # Initialize the KPipeline with an explicit repo_id to suppress the warning
        pipeline_instance = KPipeline(lang_code='z', repo_id="hexgrad/Kokoro-82M")
        
        # Create a generator that yields (graphemes, phonemes, audio)
        generator = pipeline_instance(
            cleaned_text, voice=voice, speed=1, split_pattern=r'\n+'
        )
        
        # Merge audio segments (convert Tensors to NumPy arrays if needed)
        audio_segments = []
        for i, (_, _, audio) in enumerate(generator):
            # Check if the audio segment is a Tensor and convert it to a NumPy array
            if isinstance(audio, torch.Tensor):
                audio_np = audio.detach().cpu().numpy()
            else:
                audio_np = audio
            audio_segments.append(audio_np)
        
        if audio_segments:
            # Concatenate the segments along the first dimension
            final_audio = np.concatenate(audio_segments, axis=0)
            sf.write(output_file_path, final_audio, 24000)
            
            # Verify that the file was actually created and has content
            if os.path.exists(output_file_path):
                file_size = os.path.getsize(output_file_path)
                if file_size > 0:
                    print(f"✅ Successfully saved TTS audio: {output_file_path} ({file_size} bytes)")
                    return output_file_path
                else:
                    print(f"❌ Error: Audio file {output_file_path} is empty (0 bytes)")
                    return None
            else:
                print(f"❌ Error: Audio file {output_file_path} was not created")
                return None
        else:
            print("⚠️ No audio segments were generated.")
            return None

    except Exception as e:
        print(f"❌ Error generating speech: {e}")
        print(f"❌ Text that caused error: {text[:100]}...")
        return None

async def edge_tts_example(text, output_dir, filename, voice="zh-CN-YunxiNeural"):
    """
    Generates speech from text and saves it to a specific directory.
    
    :param text: Text to be converted to speech.
    :param output_dir: Directory where the audio file will be saved.
    :param filename: Name of the audio file.
    :param voice: The voice model to use.
    :return: Full path of the saved audio file.
    """
    if not text or text.strip() == "":
        print("⚠️ Warning: Received empty text for speech synthesis.")
        return None  # Skip empty text

    # ✅ Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # ✅ Define the full file path
    output_file_path = os.path.join(output_dir, filename)

    # ✅ Generate speech and save it to the file
    try:
        # Clean the text to remove any problematic characters
        cleaned_text = text.strip()
        if len(cleaned_text) > 1000:
            print(f"⚠️ Warning: Text is very long ({len(cleaned_text)} chars), truncating...")
            cleaned_text = cleaned_text[:1000] + "..."
        
        print(f"💾 Saving TTS audio to: {output_file_path}")
        print(f"🔊 Using voice: {voice}, Text length: {len(cleaned_text)}")
        
        # Validate voice parameter for Chinese text
        if any('\u4e00' <= char <= '\u9fff' for char in cleaned_text):  # Check for Chinese characters
            if not voice.startswith(('zh-', 'zh_')):
                print(f"⚠️ Warning: Chinese text detected but using non-Chinese voice: {voice}")
                # Auto-correct to Chinese voice
                voice = "zh-TW-YunJheNeural"
                print(f"🔄 Auto-corrected to Chinese voice: {voice}")
        
        communicate = edge_tts.Communicate(cleaned_text, voice, rate="+20%")
        await communicate.save(output_file_path)
        
        # Add a small delay to ensure file is written
        import asyncio
        await asyncio.sleep(0.2)
        
        # Verify that the file was actually created and has content
        if os.path.exists(output_file_path):
            file_size = os.path.getsize(output_file_path)
            if file_size > 0:
                print(f"✅ Successfully saved TTS audio: {output_file_path} ({file_size} bytes)")
                return output_file_path
            else:
                print(f"❌ Error: Audio file {output_file_path} is empty (0 bytes)")
                return None
        else:
            print(f"❌ Error: Audio file {output_file_path} was not created")
            return None
            
    except Exception as e:
        print(f"❌ Error saving audio: {e}")
        print(f"❌ Voice used: {voice}")
        print(f"❌ Text that caused error: {text[:100]}...")
        return None



def gemini_chat(text_array=None, script=None, clients=None, keys=None, max_retries=100):
    if text_array is None or script is None:
        raise ValueError("script or text_array can't be None")
    
    if (clients is None or len(clients) == 0) and (keys is None or len(keys) == 0):
        raise ValueError("Either clients or keys must be provided")

    # ✅ If only keys are provided, create clients
    if clients is None or len(clients) == 0:
        clients = [genai.Client(api_key=key) for key in keys]

    # ✅ Ensure we have multiple clients to rotate
    client_cycle = itertools.cycle(clients)

    response_array_of_text = []
    count = 0
    for idx, text in enumerate(tqdm(text_array)):
        retries = 0
        client = next(client_cycle)  # Get the first client

        while retries < max_retries:
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f'''以下是我們的完整講稿：{script}  
                    以下是第 {count} 張 Ptt 內容，前面幾張已經處理完畢：{text}  
                    請仔細閱讀上述資料，並從中萃取與此張投影片直接相關的重點，生成一段針對該投影片的講稿。  
                    要求如下：  
                    1. 假裝你是講者，用人類的方式講話，不要囉唆與投影片無關的資訊。  
                    2. 回應內容必須嚴格限定在該投影片範圍內，不得擴展到其他部分，不能講 "好的" ... 避免讓人發現此為 AI 產生。  
                    3. 避免提到會多久講完。
                    4. 不要念一些無意義的東西例如：連結: https://www.ptt.cc/bbs/Beauty/M.1700000000.A.123.html'''
                )
                response_array_of_text.append(remove_markdown(response.text))
                count += 1
                break  # ✅ Successful request; exit retry loop
            except Exception as e:
                error_message = str(e)
                if "RESOURCE_EXHAUSTED" in error_message:
                    wait_time = 2 ** retries  # Exponential backoff
                    print(f"Rate limit reached for current client. Switching client and retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                    client = next(client_cycle)  # 🔄 Rotate to the next client
                else:
                    raise e  # ⚠️ Other errors should not be retried (e.g., invalid request)
        else:
            raise Exception("Max retries reached. Aborting.")
    
    return response_array_of_text
