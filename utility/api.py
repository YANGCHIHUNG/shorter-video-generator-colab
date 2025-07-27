from google import genai
import edge_tts
from tqdm import tqdm
import time
import itertools
import os
import torch
import numpy as np
from utility.text import *
import soundfile as sf

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
                retries += 1
                
                # Handle different types of errors
                if "RESOURCE_EXHAUSTED" in error_message:
                    wait_time = min(2 ** retries, 60)  # Exponential backoff with max 60 seconds
                    print(f"⚠️ Rate limit reached for current client. Switching client and retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    client = next(client_cycle)  # 🔄 Rotate to the next client
                elif "503" in error_message or "UNAVAILABLE" in error_message or "overloaded" in error_message:
                    wait_time = min(5 * retries, 120)  # Longer wait for service unavailable
                    print(f"⚠️ Service unavailable (503/overloaded). Retrying in {wait_time} seconds... (Attempt {retries}/{max_retries})")
                    time.sleep(wait_time)
                    client = next(client_cycle)  # 🔄 Rotate to the next client
                elif "500" in error_message or "INTERNAL" in error_message:
                    wait_time = min(3 * retries, 60)  # Wait for internal server errors
                    print(f"⚠️ Internal server error (500). Retrying in {wait_time} seconds... (Attempt {retries}/{max_retries})")
                    time.sleep(wait_time)
                    client = next(client_cycle)  # 🔄 Rotate to the next client
                elif "429" in error_message or "QUOTA_EXCEEDED" in error_message:
                    wait_time = min(10 * retries, 300)  # Longer wait for quota exceeded
                    print(f"⚠️ API quota exceeded. Retrying in {wait_time} seconds... (Attempt {retries}/{max_retries})")
                    time.sleep(wait_time)
                    client = next(client_cycle)  # 🔄 Rotate to the next client
                else:
                    # For other errors, try a few times with shorter wait
                    if retries <= 3:
                        wait_time = min(2 * retries, 10)
                        print(f"⚠️ Error: {error_message}. Retrying in {wait_time} seconds... (Attempt {retries}/{max_retries})")
                        time.sleep(wait_time)
                        client = next(client_cycle)  # 🔄 Rotate to the next client
                    else:
                        print(f"❌ Persistent error after {retries} attempts: {error_message}")
                        raise e  # ⚠️ Other persistent errors should not be retried indefinitely
        else:
            raise Exception(f"❌ Max retries ({max_retries}) reached for page {idx + 1}. Last error: {error_message}")
    
    return response_array_of_text
