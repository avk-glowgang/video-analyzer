import os
import subprocess
import tempfile
import yt_dlp
from pathlib import Path
import json
import random

class VideoProcessor:
    def __init__(self):
        self.temp_dir = Path("/tmp")
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
        ]
    
    def download_video(self, url):
        """Robust video download with multiple fallback methods"""
        try:
            print(f"Attempting to download: {url}")
            
            # Create unique filename
            video_id = f"video_{os.urandom(8).hex()}"
            output_template = str(self.temp_dir / f"{video_id}.%(ext)s")
            
            print(f"Output template: {output_template}")
            
            # Randomize user agent
            user_agent = random.choice(self.user_agents)
            
            # Base options for all platforms
            base_opts = {
                'outtmpl': output_template,
                'no_warnings': False,
                'verbose': True,
                'http_headers': {
                    'User-Agent': user_agent,
                    'Referer': 'https://www.google.com/',
                    'Accept-Language': 'en-US,en;q=0.9'
                },
                'http_client': 'curl_cffi',
                'impersonate': 'chrome110',
                'extractor_args': {
                    'youtube': {'skip': ['dash', 'hls']}
                },
                'throttled_rate': '500K',
            }
            
            # Platform-specific strategies
            if "youtube.com" in url or "youtu.be" in url:
                strategy = {
                    'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
                    'cookiefile': '/tmp/cookies.txt'
                }
            elif "tiktok.com" in url:
                strategy = {
                    'format': 'best',
                    'extractor_args': {
                        'tiktok': {'skip_dash_manifest': True}
                    }
                }
            elif "instagram.com" in url:
                strategy = {
                    'format': 'best',
                    'cookiefile': '/tmp/cookies.txt'
                }
            else:  # Generic fallback
                strategy = {
                    'format': 'bestvideo+bestaudio/best',
                    'cookiefile': '/tmp/cookies.txt'
                }
            
            ydl_opts = {**base_opts, **strategy}
            
            # Add proxy if available
            if proxy_url := os.getenv('PROXY_URL'):
                ydl_opts['proxy'] = proxy_url
                print("Using proxy for download")
            
            print(f"yt-dlp options: {json.dumps(ydl_opts, indent=2)}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    # Extract info first
                    info = ydl.extract_info(url, download=False)
                    print(f"Video title: {info.get('title', 'Unknown')}")
                    print(f"Duration: {info.get('duration', 'Unknown')} seconds")
                    
                    # Download video
                    ydl.download([url])
                    
                    # Find downloaded file
                    video_extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov']
                    for ext in video_extensions:
                        candidate = self.temp_dir / f"{video_id}{ext}"
                        if candidate.exists():
                            print(f"Found video file: {candidate}")
                            return str(candidate)
                    
                    raise Exception("No video file found after download")
                    
                except Exception as e:
                    # Fallback to worst quality if initial fails
                    print(f"Primary download failed: {str(e)}")
                    print("Attempting fallback download...")
                    try:
                        ydl_opts['format'] = 'worst'
                        with yt_dlp.YoutubeDL(ydl_opts) as fallback_ydl:
                            fallback_ydl.download([url])
                        
                        for ext in video_extensions:
                            candidate = self.temp_dir / f"{video_id}{ext}"
                            if candidate.exists():
                                print(f"Fallback video file: {candidate}")
                                return str(candidate)
                        
                        raise Exception("Fallback download failed")
                    except Exception as fallback_e:
                        raise Exception(f"All download attempts failed: {str(fallback_e)}")
            
        except Exception as e:
            raise Exception(f"Video download failed: {str(e)}")
    
    def extract_frames(self, video_path, interval=1.5):
        """Extract frames every 1.5 seconds"""
        try:
            print(f"Extracting frames from: {video_path}")
            
            if not os.path.exists(video_path):
                raise Exception(f"Video file does not exist: {video_path}")
            
            frames_dir = self.temp_dir / f"frames_{os.urandom(8).hex()}"
            frames_dir.mkdir(exist_ok=True)
            print(f"Frames directory: {frames_dir}")
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', f'fps=1/{interval},scale=512:512',
                '-q:v', '2',
                '-y',
                str(frames_dir / 'frame_%03d.jpg')
            ]
            
            print(f"FFmpeg command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(f"FFmpeg stdout: {result.stdout[:200]}...")
            
            if result.returncode != 0:
                print(f"FFmpeg stderr: {result.stderr}")
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            frame_files = sorted(list(frames_dir.glob('frame_*.jpg')))
            print(f"Extracted {len(frame_files)} frames")
            
            if not frame_files:
                raise Exception("No frames were extracted")
                
            # Limit to 100 frames maximum
            if len(frame_files) > 100:
                frame_files = frame_files[:100]
                print(f"Limited to first 100 frames")
                
            return [str(f) for f in frame_files]
            
        except Exception as e:
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
            print(f"Audio extraction stderr: {result.stderr[:500]}")
            
            if result.returncode != 0:
                raise Exception(f"Audio extraction failed: {result.stderr}")
            
            if not os.path.exists(audio_path):
                raise Exception("Audio file was not created")
                
            print(f"Audio extracted successfully: {audio_path}")
            return str(audio_path)
            
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
                        print(f"Cleaned up directory: {file_path}")
                    else:
                        os.remove(file_path)
                        print(f"Cleaned up file: {file_path}")
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")
