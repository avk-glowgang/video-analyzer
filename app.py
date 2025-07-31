from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import logging
import traceback
import time

load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("video-analyzer")

# Don't initialize these at startup - initialize them when needed
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
    <head>
        <title>Video Analyzer Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            input[type="text"] { padding: 10px; margin: 10px 0; width: 500px; }
            button { padding: 10px 20px; background: #007cba; color: white; border: none; cursor: pointer; }
            button:hover { background: #005a87; }
            #results { margin-top: 20px; padding: 20px; background: #f5f5f5; border-radius: 5px; }
            pre { white-space: pre-wrap; word-wrap: break-word; }
            .loader { border: 5px solid #f3f3f3; border-top: 5px solid #3498db; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite; margin: 20px auto; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .progress { width: 100%; background-color: #ddd; border-radius: 5px; margin: 10px 0; }
            .progress-bar { height: 20px; background-color: #4CAF50; border-radius: 5px; width: 0%; transition: width 0.5s; }
        </style>
    </head>
    <body>
        <h1>Video Analyzer Test</h1>
        <form id="testForm">
            <label for="video_url">YouTube/TikTok/Instagram URL:</label><br>
            <input type="text" id="video_url" name="video_url" placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ"><br><br>
            <button type="submit">Analyze Video</button>
        </form>
        
        <div id="results"></div>
        
        <script>
            document.getElementById('testForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const url = document.getElementById('video_url').value;
                const resultsDiv = document.getElementById('results');
                
                if (!url) {
                    resultsDiv.innerHTML = '<p style="color: red;">Please enter a video URL</p>';
                    return;
                }
                
                resultsDiv.innerHTML = `
                    <div style="text-align:center">
                        <p><strong>Processing...</strong> This may take 1-3 minutes. Please wait...</p>
                        <div class="loader"></div>
                        <div class="progress">
                            <div class="progress-bar" id="progressBar"></div>
                        </div>
                        <p id="statusText">Starting analysis...</p>
                    </div>
                `;
                
                const progressBar = document.getElementById('progressBar');
                const statusText = document.getElementById('statusText');
                
                const updateProgress = (step, total) => {
                    const percent = Math.min(100, Math.round((step / total) * 100));
                    progressBar.style.width = `${percent}%`;
                };
                
                const steps = [
                    "Downloading video",
                    "Extracting frames",
                    "Extracting audio",
                    "Transcribing audio",
                    "Analyzing visuals",
                    "Generating insights"
                ];
                
                try {
                    const response = await fetch('/analyze-video', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({video_url: url})
                    });
                    
                    // Update progress as we go
                    for (let i = 0; i < steps.length; i++) {
                        statusText.textContent = steps[i];
                        updateProgress(i + 1, steps.length);
                        await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate progress
                    }
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        resultsDiv.innerHTML = `
                            <h3>Analysis Complete!</h3>
                            <h4>Transcript:</h4>
                            <p>${data.transcript || 'No transcript available'}</p>
                            
                            <h4>Visual Analysis:</h4>
                            <p>${data.visual_analysis || 'No visual analysis available'}</p>
                            
                            <h4>Final Analysis & Creative Variations:</h4>
                            <pre>${data.final_analysis || 'No final analysis'}</pre>
                        `;
                    } else {
                        resultsDiv.innerHTML = `<p style="color: red;">Error: ${data.error || 'Unknown error'}</p>`;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = `<p style="color: red;">Network Error: ${error.message}</p>`;
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/analyze-video', methods=['POST'])
def analyze_video():
    try:
        # Initialize processors only when needed
        video_proc, ai_anal = get_processors()
        
        data = request.get_json()
        video_url = data.get('video_url')
        
        if not video_url:
            return jsonify({"error": "video_url is required"}), 400
        
        logger.info(f"Starting analysis for: {video_url}")
        
        # Download and process
        logger.info("Downloading video...")
        start_time = time.time()
        video_path = video_proc.download_video(video_url)
        logger.info(f"Video downloaded in {time.time()-start_time:.2f}s")
        
        logger.info("Extracting frames...")
        start_time = time.time()
        frames = video_proc.extract_frames(video_path, interval=1.5)
        logger.info(f"Extracted {len(frames)} frames in {time.time()-start_time:.2f}s")
        
        logger.info("Extracting audio...")
        start_time = time.time()
        audio_path = video_proc.extract_audio(video_path)
        logger.info(f"Audio extracted in {time.time()-start_time:.2f}s")
        
        logger.info("Transcribing audio...")
        start_time = time.time()
        transcript = ai_anal.transcribe_audio(audio_path)
        logger.info(f"Audio transcribed in {time.time()-start_time:.2f}s")
        
        logger.info("Analyzing frames...")
        start_time = time.time()
        visual_analysis = ai_anal.analyze_frames(frames, transcript)
        logger.info(f"Visual analysis completed in {time.time()-start_time:.2f}s")
        
        logger.info("Combining analyses...")
        start_time = time.time()
        final_analysis = ai_anal.combine_analysis(transcript, visual_analysis)
        logger.info(f"Analysis combined in {time.time()-start_time:.2f}s")
        
        # Cleanup
        all_files = [video_path, audio_path] + frames
        frame_dirs = list(set([os.path.dirname(f) for f in frames]))
        video_proc.cleanup_files(all_files + frame_dirs)
        logger.info("Temporary files cleaned up")
        
        return jsonify({
            "success": True,
            "transcript": transcript,
            "visual_analysis": visual_analysis,
            "final_analysis": final_analysis,
            "video_url": video_url
        })
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "error": f"Video analysis failed: {str(e)}",
            "details": "This usually happens when platforms block our servers. Try a different video URL."
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
