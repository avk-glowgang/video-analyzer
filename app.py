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
        
        # Rest of your code stays the same...
        video_path = video_proc.download_video(video_url)
        frames = video_proc.extract_frames(video_path, interval=1.5)
        audio_path = video_proc.extract_audio(video_path)
        transcript = ai_anal.transcribe_audio(audio_path)
        visual_analysis = ai_anal.analyze_frames(frames, transcript)
        final_analysis = ai_anal.combine_analysis(transcript, visual_analysis)
        
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
