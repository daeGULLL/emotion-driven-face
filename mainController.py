from test_face import detect_emotion_10s
#from arduino_comm import send_eyebrow_angle
import time
import subprocess
import atexit
import os
import sys
import serial
from picamera2 import Picamera2
from libcamera import Transform

def get_emotion():
    return "angry"

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=0.1)

def send_eyebrow_angle(angle: int):
    angle = max(0, min(180, angle))
    ser.write(f"{angle}\n".encode())
    print("angle sent!")

MOUTH_LED_BIN = "./mouthLED.exe"

EMOTION_DEBOUNCE_TIME = 0.3
POLL_INTERVAL = 0.1

EYEBROW_ANGLE = {
    "neutral": 90,
    "happy" : 120,
    "sad" : 60,
    "angry" : 160,
    "fear" : 130,
    "surprise" : 20,
    "disgust" : 70,
}

EYEBROW_STEP = 2
EYEBROW_STEP_DELAY = 0.02

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "BGR888"},
    #transform=Transform(rotation=180)
)
picam2.configure(config)
picam2.start()

if not os.path.exists(MOUTH_LED_BIN) :
    raise RuntimeError("mouthLED binary not found")

proc = subprocess.Popen(
    [MOUTH_LED_BIN],
    stdin = subprocess.PIPE,
    text = True,
    bufsize = 1
)

tts_proc = subprocess.Popen(
    ["/home/pi/.venv/bin/python", "/home/pi/ai_speak_module.py"],
    stdin=subprocess.PIPE,
    text=True,
    bufsize=1
)

def speak_emotion_change(emotion: str):
    tts_proc.stdin.write(f"CHANGE {emotion}\n")
    tts_proc.stdin.flush()

def speak_emotion_same():
    tts_proc.stdin.write("SAME\n")
    tts_proc.stdin.flush()

def cleanup() :
    try :
        picam2.stop()
        if proc.poll() is None :
            proc.terminate()
            proc.wait(timeout = 1)
    except Exception :
        pass

atexit.register(cleanup)

def animate_patterns(emotion : str) :
    if proc.poll() is not None :
        print("[ERROR] mouthLED process is not running")
        return
    try :
        proc.stdin.write(emotion + "\n")
        proc.stdin.flush()
    except BrokenPipeError :
        print("[ERROR] Broken pipe to mouthLED")

def main_loop() :
    last_emotion = None
    last_change_time = 0.0
    current_eyebrow_angle = EYEBROW_ANGLE["neutral"]
    is_initial_run = True

    while True :
        emotion = detect_emotion_10s(picam2, window_sec=1) or "neutral"
        now = time.time()
        if emotion != last_emotion and (now - last_change_time) > EMOTION_DEBOUNCE_TIME:
            print(f"[EMOTION] {last_emotion} -> {emotion}")
            animate_patterns(emotion)

            target_angle = EYEBROW_ANGLE.get(emotion, EYEBROW_ANGLE[emotion])
            send_eyebrow_angle(target_angle)
            
            speak_emotion_change(emotion)

            last_emotion = emotion
            last_change_time = now
            is_initial_run = False
        elif emotion == last_emotion and not is_initial_run:
            print(f"[EMOTION] Consistent: {emotion}")
            speak_emotion_same()

            last_change_time = now

        time.sleep(POLL_INTERVAL)



if __name__ == "__main__":
 #   if not hasattr(ai_speak_module, 'prev_answer'):
 #       ai_speak_module.prev_answer = ""
  #      ai_speak_module.init_speak = True

    try :
        main_loop()
    except KeyboardInterrupt :
        print("\n[INFO] Interrupted by user")
        sys.exit(0)
