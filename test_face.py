import cv2

import numpy as np

import time

from collections import Counter

from keras.models import load_model



emotion_model_path = "./models/emotion_model.hdf5"

face_cascade_path = "./models/haarcascade_frontalface_default.xml"



labels = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]



face_cascade = cv2.CascadeClassifier(face_cascade_path)

emotion_classifier = load_model(emotion_model_path, compile=False)

emotion_target_size = emotion_classifier.input_shape[1:3]



def clamp(v, lo, hi):

    return max(lo, min(hi, v))



def preprocess_gray_face(gray_face, target_size):

    gray_face = cv2.resize(gray_face, target_size, interpolation=cv2.INTER_AREA)

    gray_face = gray_face.astype("float32") / 255.0

    gray_face = (gray_face - 0.5) * 2.0

    gray_face = np.expand_dims(gray_face, 0)

    gray_face = np.expand_dims(gray_face, -1)

    return gray_face



def detect_emotion_10s(picam2, window_sec=5, show_gui=True):
    start_time = time.time()
    emotion_records = []

    while time.time() - start_time < window_sec:
        frame = picam2.capture_array()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        display_text = "detecting..."

        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda r: r[2] * r[3])

            x1 = clamp(x, 0, gray.shape[1] - 1)
            y1 = clamp(y, 0, gray.shape[0] - 1)
            x2 = clamp(x + w, 0, gray.shape[1])
            y2 = clamp(y + h, 0, gray.shape[0])

            if (x2 - x1) > 10 and (y2 - y1) > 10:
                gray_face = gray[y1:y2, x1:x2]
                inp = preprocess_gray_face(gray_face, emotion_target_size)
                preds = emotion_classifier.predict(inp, verbose=0)[0]
                idx = int(np.argmax(preds))
                conf = float(preds[idx])

                display_text = f"{labels[idx]} {conf:.2f}"

                if conf > 0.4:
                    emotion_records.append(labels[idx])



            cv2.rectangle(rgb, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(rgb, display_text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        remaining = int(window_sec - (time.time() - start_time))
        cv2.putText(rgb, f"Time left: {remaining}s", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        if show_gui:
            cv2.imshow("Emotion Detection", rgb)
          
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    if emotion_records:
        return Counter(emotion_records).most_common(1)[0][0]

    return "neutral"
