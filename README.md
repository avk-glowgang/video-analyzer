# Video Analyzer

This application analyzes videos from various platforms (YouTube, TikTok, Instagram) using AI to provide:
- Audio transcriptions
- Visual analysis of key frames
- Creative variations and recommendations

## Setup
1. Set environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `PROXY_URL`: (Optional) Proxy URL for bypassing restrictions
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python app.py`

## Endpoints
- `/`: Health check
- `/test`: Testing UI
- `/analyze-video`: POST endpoint for video analysis

## Deployment
Deploy to Railway with:
- Python 3.11
- FFmpeg installed
- Port 8000 exposed
