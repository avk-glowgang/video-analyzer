from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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
                
                resultsDiv.innerHTML = '<p><strong>Processing...</strong> This may take 30-90 seconds. Please wait...</p>';
                
                try {
                    const response = await fetch('/analyze-video', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({video_url: url})
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        resultsDiv.innerHTML = `
                            <h3>Analysis Complete!</h3>
                            <h4>Transcript:</h4>
                            <p>${data.transcript}</p>
                            
                            <h4>Visual Analysis:</h4>
                            <p>${data.visual_analysis}</p>
                            
                            <h4>Final Analysis & Creative Variations:</h4>
                            <pre>${data.final_analysis}</pre>
                        `;
                    } else {
                        resultsDiv.innerHTML = '<p style="color: red;">Error: ' + (data.error || 'Unknown error') + '</p>';
                    }
                } catch (error) {
                    resultsDiv.innerHTML = '<p style="color: red;">Network Error: ' + error.message + '</p>';
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
        
        print(f"Starting analysis for: {video_url}")
        
        # Download and process
        video_path = video_proc.download_video(video_url)
        frames = video_proc.extract_frames(video_path, interval=1.5)
        audio_path = video_proc.extract_audio(video_path)
        transcript = ai_anal.transcribe_audio(audio_path)
        visual_analysis = ai_anal.analyze_frames(frames, transcript)
        final_analysis = ai_anal.combine_analysis(transcript, visual_analysis)
        
        # Cleanup
        all_files = [video_path, audio_path] + frames
        frame_dirs = list(set([os.path.dirname(f) for f in frames]))
        video_proc.cleanup_files(all_files + frame_dirs)
        
        return jsonify({
            "success": True,
            "transcript": transcript,
            "visual_analysis": visual_analysis,
            "final_analysis": final_analysis,
            "video_url": video_url
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
