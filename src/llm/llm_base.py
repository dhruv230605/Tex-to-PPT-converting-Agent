import json
import re
from openai import OpenAI


class BaseLLMAgent:
    def __init__(self, api_key, model="gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.25,
        )
        return response.choices[0].message.content.strip()

    def _safe_json_load(self, text: str):
        text = text.strip()

        # Remove Markdown code fences
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) > 1:
                text = parts[1]
            if text.lstrip().startswith("json"):
                text = text.lstrip()[4:]
            if "```" in text:
                text = text.rsplit("```", 1)[0]

        text = text.strip()

        # Escape LaTeX math delimiters and other problematic escapes
        # Convert \( and \) to plain parentheses to avoid JSON escape issues
        text = text.replace(r'\(', '(').replace(r'\)', ')')
        # Convert \[ and \] similarly
        text = text.replace(r'\[', '[').replace(r'\]', ']')
        
        # Escape single backslashes used in LaTeX math so JSON loads
        text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)

        return json.loads(text)

    def _extract_json(self, text: str) -> str:
        if not text or '{' not in text:
            raise ValueError("No JSON object found in text")

        start = text.find('{')
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]

        raise ValueError("Unbalanced JSON braces in text")
