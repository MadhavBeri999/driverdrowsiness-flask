from flask import Flask, render_template, Response
from detection.detect_drowsiness import gen_frames  # Updated import from detection folder

app = Flask(__name__)

# ------------------- Routes -------------------

@app.route('/')
def home():
    """Render the main dashboard page."""
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src of <img> tag."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# Optional: Add a simple test route for API health check
@app.route('/health')
def health_check():
    return {"status": "OK"}, 200


# ------------------- Main -------------------
if __name__ == '__main__':
    # Run Flask app with debug on and allow reloader
    app.run(host='0.0.0.0', port=5000, debug=True)
