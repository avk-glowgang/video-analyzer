import os
import base64
from openai import OpenAI

class AIAnalyzer:
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")  # Reads from Railway variable
        if not api_key:
            raise Exception("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio using OpenAI Whisper"""
        try:
            with open(audio_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            raise Exception(f"Audio transcription failed: {str(e)}")
    
    def encode_image(self, image_path):
        """Encode image to base64 for GPT-4V"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Image encoding failed: {str(e)}")
    
    def analyze_frames(self, frame_paths, transcript):
        """Analyze video frames with GPT-4V"""
        try:
            selected_frames = frame_paths[:6]  # Limit to first 6 frames
            
            # Prepare images for API
            image_messages = []
            for frame_path in selected_frames:
                base64_image = self.encode_image(frame_path)
                image_messages.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "low"
                    }
                })
            
            prompt = f"""Analyze these video frames along with the transcript. Focus on:

1. Visual hooks and attention-grabbing elements
2. Text overlays, graphics, or on-screen elements  
3. Gestures, expressions, props, and visual storytelling
4. Scene changes and visual flow

Transcript: "{transcript}"

Provide a detailed visual analysis focusing on what makes this video engaging."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use gpt-4o-mini for vision+chat
                messages=[
                    {
                        "role": "user", 
                        "content": [{"type": "text", "text": prompt}] + image_messages
                    }
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Frame analysis failed: {str(e)}")
    
    def combine_analysis(self, transcript, visual_analysis):
        """Combine transcript and visual analysis for final insights"""
        try:
            prompt = f"""Based on the following transcript and visual analysis of a video, provide:

1. A comprehensive summary of the video content
2. Key engaging elements (both audio and visual)
3. 5 creative variations or twists on this concept for new videos
4. Specific recommendations for recreating similar content

TRANSCRIPT:
{transcript}

VISUAL ANALYSIS:
{visual_analysis}

Format your response with clear sections."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Combined analysis failed: {str(e)}")
