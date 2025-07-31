from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from utils.video_processor import VideoProcessor
from utils.ai_analyzer import AIAnalyzer

load_dotenv()

app = Flask(__name__)

# Initialize processors
video_processor = VideoProcessor()
ai_analyzer = AIAnalyzer()

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Video analyzer is running"})

@app.route('/analyze-video', methods=['POST'])
def analyze_video():
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        
        if not video_url:
            return jsonify({"error": "video_url is required"}), 400
        
        print(f"Starting analysis for: {video_url}")
        
        # Step 1: Download video in low resolution
        print("Downloading video...")
        video_path = video_processor.download_video(video_url)
        
        # Step 2: Extract frames every 1.5 seconds
        print("Extracting frames...")
        frames = video_processor.extract_frames(video_path, interval=1.5)
        
        # Step 3: Extract audio
        print("Extracting audio...")
        audio_path = video_processor.extract_audio(video_path)
        
        # Step 4: Transcribe audio with Whisper
        print("Transcribing audio...")
        transcript = ai_analyzer.transcribe_audio(audio_path)
        
        # Step 5: Analyze frames with GPT-4V
        print("Analyzing frames...")
        visual_analysis = ai_analyzer.analyze_frames(frames, transcript)
        
        # Step 6: Combine everything for final analysis
        print("Creating final analysis...")
        final_analysis = ai_analyzer.combine_analysis(transcript, visual_analysis)
        
        # Step 7: Cleanup temporary files
        print("Cleaning up...")
        all_files = [video_path, audio_path] + frames
        # Also cleanup frame directories
        frame_dirs = list(set([os.path.dirname(f) for f in frames]))
        video_processor.cleanup_files(all_files + frame_dirs)
        
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
