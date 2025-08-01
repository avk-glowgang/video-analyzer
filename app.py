from flask import Flask, request, jsonify
import os
import logging
import traceback
import time

# Remove dotenv for Railway; keep for local if you want:
if os.environ.get("RAILWAY_ENVIRONMENT"):
    # Running on Railway, skip dotenv
    pass
else:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("video-analyzer")

# Lazy initialization
video_processor = None
ai_analyzer = None

def get_processors():
    global video_processor, ai_analyzer
    if video_processor is None:
        from utils.video_processor import VideoProcessor
        from utils.ai_analyzer import AIAnalyzer
        video_processor = VideoProcessor()
        ai_analyzer = AIAnalyzer()
    return video_processor, ai_analyzer

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Video analyzer is running"})

@app.route('/test', methods=['GET'])
def test_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Video Analyzer Test</title></head>
    <body>
        <h1>Video Analyzer Test</h1>
        <form id="testForm">
            <input type="text" id="video_url" placeholder="Enter video URL">
            <button type="submit">Analyze</button>
        </form>
        <div id="results"></div>
        <script>
        document.getElementById('testForm').addEventListener('submit', async e => {
            e.preventDefault();
            const url = document.getElementById('video_url').value;
            const resDiv = document.getElementById('results');
            resDiv.textContent = 'Processing...';
            const res = await fetch('/analyze-video', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({video_url: url})
            });
            const data = await res.json();
            resDiv.textContent = JSON.stringify(data, null, 2);
        });
        </script>
    </body>
    </html>
    '''

@app.route('/analyze-video', methods=['POST'])
def analyze_video():
    try:
        video_proc, ai_anal = get_processors()
        data = request.get_json()
        video_url = data.get('video_url')
        if not video_url:
            return jsonify({"error": "video_url is required"}), 400
        
        logger.info(f"Starting analysis for: {video_url}")

        # Download & process video
        video_path = video_proc.download_video(video_url)
        frames = video_proc.extract_frames(video_path, interval=1.5)
        audio_path = video_proc.extract_audio(video_path)
        transcript = ai_anal.transcribe_audio(audio_path)
        visual_analysis = ai_anal.analyze_frames(frames, transcript)
        final_analysis = ai_anal.combine_analysis(transcript, visual_analysis)

        # Cleanup
        video_proc.cleanup_files([video_path, audio_path] + frames)

        return jsonify({
            "success": True,
            "transcript": transcript,
            "visual_analysis": visual_analysis,
            "final_analysis": final_analysis
        })

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)

