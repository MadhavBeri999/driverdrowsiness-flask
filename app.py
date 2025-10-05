from flask import Flask, render_template, Response, jsonify
from detection.detect_drowsiness import gen_frames  # only gen_frames
from state import alert_counts  # single source of truth for counters

app = Flask(__name__)

# ------------------- Routes -------------------

@app.route('/')
def home():
    """Render the main dashboard page."""
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_alert_counts')
def get_alert_counts():
    """Provides real-time alert counts to frontend (for counters)."""
    return jsonify(alert_counts)


@app.route('/health')
def health_check():
    return {"status": "OK"}, 200


# ------------------- Main -------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
