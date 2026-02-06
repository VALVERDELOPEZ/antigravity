import os
from openai import OpenAI

class Humanizer:
    """
    Fulfills Supervisor Order #1: Implement Humanizer with Double-Prompting.
    Layer 1: Content Generation (Perfect)
    Layer 2: Humanization (Adding 'imperfect' traits)
    """
    
    def __init__(self, api_key=None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def generate_viral_draft(self, topic, language="es"):
        """Generates a high-quality viral post based on STEPPS."""
        system_msg = "You are a master viral marketer. Use Jonah Berger's STEPPS framework."
        if language == "es":
            system_msg += " Generate the response in Spanish."
        else:
            system_msg += " Generate the response in English."

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"Generate a viral post about: {topic}"}
            ]
        )
        return response.choices[0].message.content

    def humanize(self, text, platform="reddit", language="es"):
        """Adds human-mimicry: typos, slang, variadic sentence length."""
        lang_context = "Spanish-speaking" if language == "es" else "English-speaking"
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    f"You are a regular {lang_context} {platform} user. "
                    "Your goal is to REWRITE the following text to look like a real human wrote it. "
                    "Rules: \n"
                    "1. Add 1-2 minor typos (character swaps).\n"
                    "2. Use platform-specific slang.\n"
                    "3. Vary sentence lengths.\n"
                    "4. Remove any 'AI' robotic tone.\n"
                    "5. Keep the core viral hooks intact."
                )},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content

    def process(self, topic):
        print(f"--- Generating Draft for: {topic} ---")
        draft = self.generate_viral_draft(topic)
        print(f"Draft: {draft[:100]}...")
        
        print("\n--- Humanizing ---")
        human_text = self.humanize(draft)
        return human_text

if __name__ == "__main__":
    # Test
    h = Humanizer()
    result = h.process("Why AI agents are better than traditional SaaS in 2026")
    print("\nFINAL VIRAL CONTENT:\n")
    print(result)
