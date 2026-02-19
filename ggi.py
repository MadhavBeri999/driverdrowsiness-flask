import cv2
import mediapipe as mp
import math
import threading
import json
import time
from playsound import playsound


# ------------------- Utility Functions -------------------
def euclidean_dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def compute_EAR(eye_landmarks):
    # Vertical distances
    A = euclidean_dist(eye_landmarks[1], eye_landmarks[5])
    B = euclidean_dist(eye_landmarks[2], eye_landmarks[4])
    # Horizontal distance
    C = euclidean_dist(eye_landmarks[0], eye_landmarks[3])
    return (A + B) / (2.0 * C)


def compute_MAR(mouth_landmarks):
    # Vertical distances
    A = euclidean_dist(mouth_landmarks[2], mouth_landmarks[10])  # Upper/lower lip
    B = euclidean_dist(mouth_landmarks[4], mouth_landmarks[8])  # Upper/lower lip
    # Horizontal distance
    C = euclidean_dist(mouth_landmarks[0], mouth_landmarks[6])  # Left/right corner
    return (A + B) / (2.0 * C)


def play_alert(sound_file, alert_type=None):
    """
    Play the alert sound in a separate thread to avoid blocking the video stream.
    Includes a cooldown check to prevent overlapping sounds.
    """
    global last_alert_time
    current_time = time.time()

    # Check cooldown if alert_type is provided
    if alert_type and (
        current_time - last_alert_time.get(alert_type, 0) < ALERT_COOLDOWN
    ):
        return

    if sound_file:
        if alert_type:
            last_alert_time[alert_type] = current_time
        threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()


# ------------------- Load Config -------------------
try:
    with open("alert_config.json", "r") as f:
        alert_config = json.load(f)
except FileNotFoundError:
    alert_config = {
        "sleep_alert": "sleep",
        "yawn_alert": "yawn",
        "headtilt_alert": "headtilt",
    }

# ------------------- Thresholds -------------------
EAR_THRESH = 0.21
MAR_THRESH = 0.6
EYE_CLOSED_SEC = 1.5  # Trigger alert after 1.5 seconds of closed eyes
HEAD_TILT_ANGLE_THRESH = 25  # degrees
YAWN_CONSEC_FRAMES = 15
YAWN_ALERT_COUNT = 2

# ------------------- Counters & State -------------------
ear_counter = 0
yawn_frame_counter = 0
yawn_event_counter = 0
yawn_in_progress = False
head_tilt_start = None
head_tilt_active = False  # New: track if head tilt alert is already active

# Cooldown Tracker (Type: timestamp)
last_alert_time = {"sleep": 0, "yawn": 0, "headtilt": 0}
ALERT_COOLDOWN = 5  # seconds before the same sound can play again

alert_message = ""
alert_color = (0, 0, 255)
alert_bg = (255, 255, 255)
alert_end_time = 0

# ------------------- Landmark Indices -------------------
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
MOUTH_IDX = [61, 81, 311, 291, 78, 308, 402, 14, 178, 88, 95]

# ------------------- Mediapipe Setup -------------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
mp_drawing = mp.solutions.drawing_utils
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)


# ------------------- Main Execution -------------------
def main():
    global ear_counter, yawn_frame_counter, yawn_event_counter, yawn_in_progress
    global head_tilt_start, alert_message, alert_color, alert_bg, alert_end_time

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Starting Round 1 Demo: Smart Transportation Safety Framework")
    print("Press 'q' to quit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Flip the frame horizontally for a later selfie-view display
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Convert normalized landmarks to pixel coordinates
                landmarks = [
                    (int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark
                ]

                # Extract eye and mouth landmarks
                left_eye = [landmarks[i] for i in LEFT_EYE_IDX]
                right_eye = [landmarks[i] for i in RIGHT_EYE_IDX]
                mouth = [landmarks[i] for i in MOUTH_IDX]

                # Compute metrics
                ear = (compute_EAR(left_eye) + compute_EAR(right_eye)) / 2.0
                mar = compute_MAR(mouth)

                # --- 1. Drowsiness Detection (EAR) ---
                if ear < EAR_THRESH:
                    ear_counter += 1
                    if ear_counter > (EYE_CLOSED_SEC * 30):
                        alert_message = "DROWSY! EYES CLOSED"
                        alert_bg = (0, 0, 255)  # Red
                        alert_color = (255, 255, 255)  # White
                        alert_end_time = time.time() + 3
                        play_alert(alert_config.get("sleep_alert"), "sleep")
                        ear_counter = 0
                else:
                    ear_counter = 0

                # --- 2. Yawn Detection (MAR) ---
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
                    alert_message = "ALERT! Too Many Yawns"
                    alert_bg = (255, 0, 0)  # Red (Matches user's request)
                    alert_color = (255, 255, 255)
                    alert_end_time = time.time() + 5
                    play_alert(alert_config.get("yawn_alert"), "yawn")
                    yawn_event_counter = 0

                # --- 3. Head Tilt Detection ---
                left_ear = landmarks[234]
                right_ear = landmarks[454]
                dy = right_ear[1] - left_ear[1]
                dx = right_ear[0] - left_ear[0]
                angle = math.degrees(math.atan2(dy, dx))

                if abs(angle) > HEAD_TILT_ANGLE_THRESH:
                    if head_tilt_start is None:
                        head_tilt_start = time.time()
                    elif time.time() - head_tilt_start > 1.5:
                        if not head_tilt_active:
                            alert_message = "HEAD TILT - PAY ATTENTION!"
                            alert_bg = (0, 255, 255)  # Cyan
                            alert_color = (0, 0, 0)
                            alert_end_time = time.time() + 2
                            play_alert(alert_config.get("headtilt_alert"), "headtilt")
                            head_tilt_active = True
                else:
                    head_tilt_start = None
                    head_tilt_active = False

                # Visualizing landmarks for the mentors
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing.DrawingSpec(
                        color=(0, 255, 0), thickness=1, circle_radius=1
                    ),
                )

        # Draw UI Overlay
        if alert_message and time.time() < alert_end_time:
            cv2.rectangle(frame, (0, 0), (w, 60), alert_bg, -1)
            cv2.putText(
                frame,
                alert_message,
                (10, 45),
                cv2.FONT_HERSHEY_DUPLEX,
                1.2,
                alert_color,
                2,
            )
        else:
            alert_message = ""  # Reset message after timer expires

        # Display Frame
        cv2.imshow("Smart Transportation Safety Framework - Round 1", frame)

        if cv2.waitKey(5) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
