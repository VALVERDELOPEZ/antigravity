import os
import json
from openai import OpenAI

class STEPPSEvaluator:
    """
    Evaluates content based on Jonah Berger's STEPPS framework.
    Required by the PRD for Quality Gate.
    """
    
    def __init__(self, api_key=None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def evaluate(self, content):
        """
        Scores content from 0 to 10 on the 6 pulses.
        """
        prompt = f"""
        Evaluate the following content according to Jonah Berger's STEPPS framework:
        
        Content: "{content}"
        
        Provide a JSON response with scores (0-10) for:
        - social_currency
        - triggers
        - emotion
        - public
        - practical_value
        - stories
        - total_score (average)
        - feedback (briefly how to improve)
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a scientific evaluator of viral content."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)

if __name__ == "__main__":
    evaluator = STEPPSEvaluator()
    sample = "You won't believe how this simple Python script automated my entire income in 30 days. No fluff, just pure logic."
    rating = evaluator.evaluate(sample)
    print(json.dumps(rating, indent=2))
