import os
import subprocess
import tempfile
import yt_dlp
from pathlib import Path

class VideoProcessor:
    def __init__(self):
        self.temp_dir = Path("/tmp")
        
    def download_video(self, url, max_resolution="480p"):
        """Download video in low resolution using yt-dlp"""
        try:
            # Create unique filename
            video_id = f"video_{os.urandom(8).hex()}"
            output_path = self.temp_dir / f"{video_id}.%(ext)s"
            
            # Enhanced yt-dlp options for better compatibility
            ydl_opts = {
                'format': f'best[height<={max_resolution[:-1]}]/worst[height<={max_resolution[:-1]}]/best/worst',
                'outtmpl': str(output_path),
                'no_warnings': True,
                'extractaudio': False,
                'audioformat': 'mp3',
                'ignoreerrors': True,
                # Add headers to avoid 403 errors
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                # TikTok specific options
                'extractor_args': {
                    'tiktok': {
                        'webpage_url_basename': 'video'
                    }
                },
                # Retry options
                'retries': 3,
                'fragment_retries': 3,
                # Skip unavailable fragments
                'skip_unavailable_fragments': True,
            }
            
            # Add cookies support for better success rate
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Extract info first to validate URL
                    info = ydl.extract_info(url, download=False)
                    if info is None:
                        raise Exception("Could not extract video information")
                    
                    # Now download
                    ydl.download([url])
            except Exception as e:
                # Try with different format if first attempt fails
                print(f"First download attempt failed: {e}")
                ydl_opts['format'] = 'worst/best'
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            # Find the downloaded file
            for file in self.temp_dir.glob(f"{video_id}.*"):
                if file.suffix in ['.mp4', '.webm', '.mkv', '.avi', '.mov']:
                    print(f"Successfully downloaded: {file}")
                    return str(file)
            
            raise Exception("Downloaded video file not found")
            
        except Exception as e:
            raise Exception(f"Failed to download video: {str(e)}")
    
    def extract_frames(self, video_path, interval=1.5):
        """Extract frames every 1.5 seconds"""
        try:
            frames_dir = self.temp_dir / f"frames_{os.urandom(8).hex()}"
            frames_dir.mkdir(exist_ok=True)
            
            # Use ffmpeg to extract frames
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', f'fps=1/{interval}',
                '-q:v', '2',  # Good quality
                '-s', '512x512',  # Resize for GPT-4V (cheaper)
                '-y',  # Overwrite output files
                str(frames_dir / 'frame_%03d.jpg')
            ]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Return list of frame paths
            frame_files = sorted(list(frames_dir.glob('frame_*.jpg')))
            if not frame_files:
                raise Exception("No frames were extracted")
                
            print(f"Extracted {len(frame_files)} frames")
            return [str(f) for f in frame_files]
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to extract frames: {e.stderr}")
        except Exception as e:
            raise Exception(f"Frame extraction error: {str(e)}")
    
    def extract_audio(self, video_path):
        """Extract audio from video"""
        try:
            audio_path = self.temp_dir / f"audio_{os.urandom(8).hex()}.wav"
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # Audio codec
                '-ar', '16000',  # Sample rate for Whisper
                '-ac', '1',  # Mono
                '-y',  # Overwrite output files
                str(audio_path)
            ]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Extracted audio: {audio_path}")
            return str(audio_path)
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to extract audio: {e.stderr}")
        except Exception as e:
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
