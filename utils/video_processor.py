import os
import subprocess
import tempfile
import yt_dlp
from pathlib import Path
import json

class VideoProcessor:
    def __init__(self):
        self.temp_dir = Path("/tmp")
        
    def download_video(self, url, max_resolution="480p"):
        """Download video with extensive debugging"""
        try:
            print(f"Attempting to download: {url}")
            
            # Create unique filename
            video_id = f"video_{os.urandom(8).hex()}"
            output_template = str(self.temp_dir / f"{video_id}.%(ext)s")
            
            print(f"Output template: {output_template}")
            
            # Simple, robust yt-dlp options
            ydl_opts = {
                'format': 'worst[ext=mp4]/worst',  # Get worst quality to ensure it works
                'outtmpl': output_template,
                'no_warnings': False,  # Show warnings for debugging
                'verbose': True,  # Enable verbose logging
            }
            
            print(f"yt-dlp options: {ydl_opts}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    # First, extract info to see if URL is valid
                    print("Extracting video info...")
                    info = ydl.extract_info(url, download=False)
                    print(f"Video title: {info.get('title', 'Unknown')}")
                    print(f"Video duration: {info.get('duration', 'Unknown')} seconds")
                    
                    # Now download
                    print("Starting download...")
                    ydl.download([url])
                    print("Download completed")
                    
                except Exception as download_error:
                    print(f"Download error: {download_error}")
                    raise download_error
            
            # Find the downloaded file with extensive search
            print(f"Looking for files in: {self.temp_dir}")
            all_files = list(self.temp_dir.glob(f"{video_id}*"))
            print(f"Found files: {all_files}")
            
            video_extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv', '.3gp']
            for file in all_files:
                print(f"Checking file: {file}")
                if file.suffix.lower() in video_extensions:
                    print(f"Successfully found video file: {file}")
                    return str(file)
            
            # If no video found, list all files for debugging
            all_temp_files = list(self.temp_dir.glob("*"))
            print(f"All files in temp directory: {all_temp_files}")
            
            raise Exception(f"No video file found. Expected pattern: {video_id}*, Found files: {all_files}")
            
        except Exception as e:
            print(f"Full error details: {str(e)}")
            raise Exception(f"Failed to download video: {str(e)}")
    
    def extract_frames(self, video_path, interval=1.5):
        """Extract frames every 1.5 seconds"""
        try:
            print(f"Extracting frames from: {video_path}")
            
            # Verify video file exists
            if not os.path.exists(video_path):
                raise Exception(f"Video file does not exist: {video_path}")
            
            frames_dir = self.temp_dir / f"frames_{os.urandom(8).hex()}"
            frames_dir.mkdir(exist_ok=True)
            print(f"Frames directory: {frames_dir}")
            
            # Simple ffmpeg command
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', f'fps=1/{interval},scale=512:512',
                '-q:v', '2',
                '-y',
                str(frames_dir / 'frame_%03d.jpg')
            ]
            
            print(f"FFmpeg command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(f"FFmpeg stdout: {result.stdout}")
            print(f"FFmpeg stderr: {result.stderr}")
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            # Check for extracted frames
            frame_files = sorted(list(frames_dir.glob('frame_*.jpg')))
            print(f"Extracted {len(frame_files)} frames")
            
            if not frame_files:
                raise Exception("No frames were extracted")
                
            return [str(f) for f in frame_files]
            
        except Exception as e:
            print(f"Frame extraction error: {str(e)}")
            raise Exception(f"Frame extraction error: {str(e)}")
    
    def extract_audio(self, video_path):
        """Extract audio from video"""
        try:
            print(f"Extracting audio from: {video_path}")
            
            if not os.path.exists(video_path):
                raise Exception(f"Video file does not exist: {video_path}")
            
            audio_path = self.temp_dir / f"audio_{os.urandom(8).hex()}.wav"
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                '-y', str(audio_path)
            ]
            
            print(f"Audio extraction command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(f"Audio extraction stderr: {result.stderr}")
            
            if result.returncode != 0:
                raise Exception(f"Audio extraction failed: {result.stderr}")
            
            if not os.path.exists(audio_path):
                raise Exception("Audio file was not created")
                
            print(f"Audio extracted successfully: {audio_path}")
            return str(audio_path)
            
        except Exception as e:
            print(f"Audio extraction error: {str(e)}")
            raise Exception(f"Audio extraction error: {str(e)}")
    
    def cleanup_files(self, file_paths):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    if os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                    print(f"Cleaned up: {file_path}")
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")
