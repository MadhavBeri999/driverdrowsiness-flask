import cv2
import mediapipe as mp
import math
import threading
import json
import time
import requests
from playsound import playsound


# ------------------- Utility Functions -------------------
def euclidean_dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def compute_EAR(eye_landmarks):
    A = euclidean_dist(eye_landmarks[1], eye_landmarks[5])
    B = euclidean_dist(eye_landmarks[2], eye_landmarks[4])
    C = euclidean_dist(eye_landmarks[0], eye_landmarks[3])
    return (A + B) / (2.0 * C)


def compute_MAR(mouth_landmarks):
    A = euclidean_dist(mouth_landmarks[2], mouth_landmarks[10])
    B = euclidean_dist(mouth_landmarks[4], mouth_landmarks[8])
    C = euclidean_dist(mouth_landmarks[0], mouth_landmarks[6])
    return (A + B) / (2.0 * C)


def play_alert(sound_file):
    threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()


# ------------------- Helper to Send Alert to Flask -------------------
def send_alert_to_backend(alert_type: str):
    """
    Send alert data to Flask backend when threshold exceeded.
    Now it automatically uses the latest registered user (no hardcoded ID).
    """
    try:
        payload = {"alert_type": alert_type}  # ✅ no user_id needed
        res = requests.post("http://127.0.0.1:5000/log_alert", json=payload, timeout=2)
        if res.status_code == 200:
            print(f"[detect_drowsiness] ✅ Logged {alert_type} alert to backend.")
        else:
            print(f"[detect_drowsiness] ⚠️ Backend responded with {res.status_code}")
    except Exception as e:
        print(f"[detect_drowsiness] ❌ Failed to log alert: {e}")


# ------------------- Load Config -------------------
with open("alert_config.json", "r") as f:
    alert_sounds = json.load(f)

sleep_alert = alert_sounds["sleep_alert"]
yawn_alert = alert_sounds["yawn_alert"]
headtilt_alert = alert_sounds["headtilt_alert"]

# ------------------- Thresholds -------------------
EAR_THRESH = 0.21
MAR_THRESH = 0.6
EYE_CLOSED_SEC = 2
EYE_FPS = 30
EYE_CONSEC_FRAMES = EYE_CLOSED_SEC * EYE_FPS
YAWN_CONSEC_FRAMES = 15
YAWN_ALERT_COUNT = 2
HEAD_TILT_ANGLE_THRESH = 25  # degrees

# ------------------- Counters & Timers -------------------
ear_counter = 0
yawn_frame_counter = 0
yawn_event_counter = 0
yawn_in_progress = False
head_tilt_start = None
head_tilt_active = False

sleep_alert_counter = 0
yawn_alert_counter = 0
headtilt_alert_counter = 0

alert_message = ""
alert_color = (0, 0, 0)
alert_bg = (0, 0, 0)
alert_end_time = 0

# ------------------- Landmark Indices -------------------
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
MOUTH_IDX = [61, 81, 311, 291, 78, 308, 402, 14, 178, 88, 95]

# ------------------- Mediapipe Setup -------------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)
mp_drawing = mp.solutions.drawing_utils


# ------------------- MAIN DETECTION FUNCTION -------------------
def gen_frames():
    """Generator function for Flask video streaming."""
    global ear_counter, yawn_frame_counter, yawn_event_counter, yawn_in_progress
    global head_tilt_start, head_tilt_active
    global alert_message, alert_color, alert_bg, alert_end_time
    global sleep_alert_counter, yawn_alert_counter, headtilt_alert_counter

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam (check camera index).")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    landmarks = [
                        (int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark
                    ]

                    left_eye = [landmarks[i] for i in LEFT_EYE_IDX]
                    right_eye = [landmarks[i] for i in RIGHT_EYE_IDX]
                    mouth = [landmarks[i] for i in MOUTH_IDX]

                    ear = (compute_EAR(left_eye) + compute_EAR(right_eye)) / 2.0
                    mar = compute_MAR(mouth)

                    # ------------------- Eyes Closed Detection -------------------
                    if ear < EAR_THRESH:
                        ear_counter += 1
                        if ear_counter >= EYE_CONSEC_FRAMES:
                            play_alert(sleep_alert)
                            sleep_alert_counter += 1
                            send_alert_to_backend(
                                "sleep"
                            )  # ✅ auto send to latest user
                            alert_message = "DROWSY! Eyes Closed"
                            alert_color = (255, 255, 255)
                            alert_bg = (0, 0, 255)
                            alert_end_time = time.time() + 5
                            ear_counter = 0
                    else:
                        ear_counter = 0

                    # ------------------- Yawning Detection -------------------
                    if mar > MAR_THRESH:
                        yawn_frame_counter += 1
                        if (
                            yawn_frame_counter >= YAWN_CONSEC_FRAMES
                            and not yawn_in_progress
                        ):
                            yawn_event_counter += 1
                            yawn_in_progress = True
                    else:
                        yawn_frame_counter = 0
                        yawn_in_progress = False

                    if yawn_event_counter >= YAWN_ALERT_COUNT:
                        play_alert(yawn_alert)
                        yawn_alert_counter += 1
                        send_alert_to_backend("yawn")  # ✅ auto send to latest user
                        alert_message = "ALERT! Too Many Yawns"
                        alert_color = (255, 255, 255)
                        alert_bg = (255, 0, 0)
                        alert_end_time = time.time() + 5
                        yawn_event_counter = 0

                    # ------------------- Head Tilt Detection -------------------
                    left_ear_pos = landmarks[234]
                    right_ear_pos = landmarks[454]

                    dx = right_ear_pos[0] - left_ear_pos[0]
                    dy = right_ear_pos[1] - left_ear_pos[1]
                    angle = math.degrees(math.atan2(dy, dx))

                    if abs(angle) > HEAD_TILT_ANGLE_THRESH:
                        if head_tilt_start is None:
                            head_tilt_start = time.time()
                        elif (
                            time.time() - head_tilt_start > 1.0 and not head_tilt_active
                        ):
                            play_alert(headtilt_alert)
                            headtilt_alert_counter += 1
                            send_alert_to_backend(
                                "head_tilt"
                            )  # ✅ auto send to latest user
                            alert_message = "HEAD TILT DETECTED!"
                            alert_color = (0, 0, 0)
                            alert_bg = (0, 255, 255)
                            alert_end_time = time.time() + 5
                            head_tilt_active = True
                    else:
                        head_tilt_start = None
                        head_tilt_active = False

                    # Draw landmarks
                    mp_drawing.draw_landmarks(
                        frame, face_landmarks, mp_face_mesh.FACEMESH_TESSELATION
                    )

            # ------------------- Show Alerts -------------------
            if alert_message and time.time() < alert_end_time:
                (text_w, text_h), _ = cv2.getTextSize(
                    alert_message, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3
                )
                x, y = 30, 50
                cv2.rectangle(
                    frame, (x - 10, y - 40), (x + text_w + 10, y + 10), alert_bg, -1
                )
                cv2.putText(
                    frame,
                    alert_message,
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.5,
                    alert_color,
                    3,
                )

            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )

    finally:
        cap.release()
        cv2.destroyAllWindows()
