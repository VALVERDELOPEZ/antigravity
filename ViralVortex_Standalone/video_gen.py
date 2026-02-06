import os
import time
from dotenv import load_dotenv
import fal_client

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

class VideoGenerator:
    """
    Integrates Wan 2.1 Video Generation via fal.ai.
    """
    
    def __init__(self, fal_key=None):
        self.api_key = fal_key or os.getenv("FAL_KEY")
        if self.api_key:
            os.environ["FAL_KEY"] = self.api_key

    def generate_video(self, prompt, duration="5s"):
        """
        Triggers a video generation task using Wan 2.1.
        """
        print(f"🎬 [FAL.AI] Generating Wan 2.1 Video: '{prompt}'")
        
        if not self.api_key:
            print("⚠️ FAL_KEY not found. Running in MOCK mode.")
            time.sleep(3)
            return {
                "video_url": "https://storage.googleapis.com/falserverless/model_tests/wan/test_video.mp4",
                "status": "success",
                "model": "wan-2.1"
            }
            
        try:
            handler = fal_client.submit(
                "fal-ai/wan/v2.1/text-to-video",
                arguments={
                    "prompt": prompt,
                    "aspect_ratio": "16:9",
                    "num_frames": 81 # Standard for ~5s
                }
            )
            
            result = handler.get()
            return {
                "video_url": result['video']['url'],
                "status": "success",
                "model": "wan-2.1"
            }
        except Exception as e:
            print(f"❌ Error in Wan 2.1 Generation: {str(e)}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    vg = VideoGenerator()
    # Test call
    res = vg.generate_video("A cinematic neon vortex in a dark void, digital art style.")
    print(res)
