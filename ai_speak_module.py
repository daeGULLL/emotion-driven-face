import os
import time
from google import genai
from google.genai import types
from google.cloud import texttospeech
from collections import deque
#from google.oauth2 import service_account

# ----------------------------------------------------
# 1. Environment Setup and Client Initialization
# ----------------------------------------------------

init_speak = True
tts_counter = 0
# Queues for asynchronous processing (Gemini -> TTS -> Speak)
need_to_tts_queue = deque() 
need_to_say_queue = deque()

# Initialize the Gemini API client.
# The GEMINI_API_KEY environment variable must be set.
try:
    gemini_client = genai.Client()
except Exception as e:
    print(f"Gemini client initialization error: {e}")
    print("Please check your GEMINI_API_KEY environment variable.")
    exit()

# Initialize the Google Cloud TTS client.
# Google Cloud authentication must be set up.
#KEY_FILE_PATH = "/home/pi/gen-lang-client-0646446881-b7293f1594b8.json"
#credentials = service_account.Credentials.from_service_account_file(KEY_FILE_PATH)
try:
    tts_client = texttospeech.TextToSpeechClient()
except Exception as e:
    print(f"TTS client initialization error: {e}")
    print("Please check your Google Cloud authentication setup.")
    exit()


# ----------------------------------------------------
# 2. Main Logic Functions
# ----------------------------------------------------

def generate(prompt: str):
    """Generates a text response using Gemini Flash and queues it for TTS."""
    print(f"User Prompt: {prompt}")

    # Step 1: Generate response with Gemini Flash
    try:
        print("-> 1. Generating response with Gemini Flash...")
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        gemini_text = response.text.strip()
        print(f"-> Gemini Response: {gemini_text}")
        need_to_tts_queue.appendleft(gemini_text)
        return gemini_text

    except Exception as e:
        print(f"Error occurred during Gemini API call: {e}")
        raise # Re-raise exception for the speak function to catch

def ttsfy():
    """Converts the text from the queue to an audio file and queues the filename for playback."""
    global tts_counter
    
    # Step 2: TTS (Text-to-Speech) Conversion and File Saving
    if not need_to_tts_queue:
        return 
        
    try:
        print("-> 2. Converting to speech and saving audio file...")
        # Process the oldest item in the queue (rightmost)
        text_to_synthesize = need_to_tts_queue.pop()
        
        synthesis_input = texttospeech.SynthesisInput(text=text_to_synthesize)

        # Voice configuration (Using Korean voice setup)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR", 
            name="ko-KR-Chirp3-HD-Despina"  # Example of a standard Korean voice
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        tts_response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Save the audio file with a unique name
        output_filename = f"gemini_response_audio_{tts_counter}.mp3"
        tts_counter += 1

        with open(output_filename, "wb") as out:
            out.write(tts_response.audio_content)
        print(f"-> Audio file saved: {output_filename}")
        need_to_say_queue.appendleft(output_filename)

    except Exception as e:
        print(f"Error occurred during TTS API call: {e}")
        # If TTS fails, the text is lost from the queue. Consider logging.
        raise # Re-raise exception

def play():
    """Plays the audio file from the queue using mpg123."""
    if not need_to_say_queue:
        return

    # Step 3: Voice Playback via Raspberry Pi Speaker
    try:
        print("-> 3. Playing audio...")
        # Get the oldest file (rightmost) from the queue
        output_filename = need_to_say_queue.pop()
        
        # Use mpg123 as the modern alternative to omxplayer for MP3 playback.
        # The '-q' flag is for quiet output (no messages displayed).
        os.system(f"mpg123 -q {output_filename}")
        
        # We can remove the time.sleep(1) because mpg123 blocks until playback is done.
        print("-> Playback finished.")
        
        # Clean up the played file to save disk space
        os.remove(output_filename)
        print(f"-> Cleaned up file: {output_filename}")

    except Exception as e:
        print(f"Error during audio playback: {e}")
        print("Please check if mpg123 is installed and the speaker is properly connected.")
        raise # Re-raise exception

prev_answer = ""    

def speak(prompt:str):
    """
    Implements a robust 'do-while' loop logic to ensure the full process 
    (Generate, TTS, Play) is attempted at least once and repeated on failure.
    """
    global prev_answer

    while True: 
        try:
            answer = generate(prompt)
            ttsfy()
            play()
            prev_answer = answer
            # If all steps succeed, break the loop
            break 
        except Exception as e:
            # If any step fails, the loop continues for retry (if desired, though this is simple retry)
            print(f"Full speak sequence failed. Retrying... Error: {e.args}")
            time.sleep(2) # Wait a moment before retrying

# ----------------------------------------------------
# 4. MoodBot Logic and Prompts (English)
# ----------------------------------------------------

# English Prompts for MoodBot Logic
init_prompt = "The user's current emotional state is %s. Generate a single, short, casual response sentence that a common person would say upon recognizing this emotion. Return only the sentence, in Korean."
continue_same_emotion_prompt = "Your previous response was '%s'. Generate the next casual sentence as if the same speaker is continuing the conversation. Return only the sentence, in Korean."
continue_diff_emotion_prompt = "The user's emotional state has changed to %s, and your previous response was '%s'. Generate the next casual sentence as if the same speaker is continuing the conversation. Return only the sentence, in Korean."

def moodBot_emotion_alter_speak(emotion:str):
    global init_speak, prev_answer
    if not init_speak:
        full_prompt = continue_diff_emotion_prompt % (emotion, prev_answer)
    else:
        full_prompt = init_prompt % emotion

    speak(full_prompt)
    # The actual prev_answer update logic would go here, retrieving the generated text before ttsfy/play
    # For now, we simulate an update:
    # prev_answer = "Simulated new answer" # Placeholder for actual generated text
    # init_speak = False

def moodBot_consistent_speak():
    global prev_answer
    full_prompt = continue_same_emotion_prompt % prev_answer
    speak(full_prompt)
    # The actual prev_answer update logic would go here


import sys

for line in sys.stdin:
    cmd = line.strip().split()

    if not cmd:
        continue

    if cmd[0] == "CHANGE":
        moodBot_emotion_alter_speak(cmd[1])
    elif cmd[0] == "SAME":
        moodBot_consistent_speak()

# ----------------------------------------------------
# 5. Test Execution
# ----------------------------------------------------

#if __name__ == "__main__":
    # English prompt test for the full loop.
 #   test_prompt = "only return hello."

    # Simple test execution (simulates the old logic)
  #  speak(test_prompt)

    # Example of calling MoodBot logic (assuming the emotion variable is available)
    # moodBot_emotion_alter_speak("joy")
    # time.sleep(5)
    # moodBot_consistent_speak()
