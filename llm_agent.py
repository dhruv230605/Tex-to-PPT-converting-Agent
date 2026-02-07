import json
from openai import OpenAI
import re


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
            text = text.split("```", 1)[1]
            if text.lstrip().startswith("json"):
                text = text.lstrip()[4:]
            if "```" in text:
                text = text.rsplit("```", 1)[0]

        text = text.strip()

        # Escape single backslashes used in LaTeX math so JSON loads
        text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)

        return json.loads(text)


class SlidePlanner(BaseLLMAgent):
    """Produces an initial slide plan (JSON) from a paper section."""

    def plan(self, paper_title: str, section_title: str, section_text: str, figures: list):
        planning_prompt = f"""
You are an expert academic slide designer.

Goal:
Create high-quality, self-contained slides from a research paper section.
Slides should be readable without oral explanation.

Guidelines:
- Use as many slides as needed
- Slides may be content-dense
- Prefer structured bullet points
- Preserve technical correctness
- Use figures only if helpful
- Do NOT include LaTeX commands
- Output ONLY valid JSON (no explanations)

Paper title:
{paper_title}

Section title:
{section_title}

Section content:
{section_text}

Available figures:
{figures}

JSON schema:
{{
  "slides": [
    {{
      "title": "...",
      "bullets": ["...", "..."],
      "figures": ["..."]
    }}
  ]
}}
"""

        draft = self._call_llm(
            system_prompt="You plan academic presentation slides.",
            user_prompt=planning_prompt,
        )

        try:
            return self._safe_json_load(draft)
        except Exception:
            raise RuntimeError("Failed to parse JSON from planning step.\n\nRaw LLM output:\n" + draft)


class SlideRefiner(BaseLLMAgent):
    """Takes a draft slide plan (JSON string or dict) and returns an improved plan."""

    def refine(self, draft_plan: str):
        # Accept dicts as well as raw strings
        if isinstance(draft_plan, dict):
            draft_text = json.dumps(draft_plan)
        else:
            draft_text = str(draft_plan)

        reflection_prompt = f"""
You are a reflection and optimization agent.

Improve the slide plan below to maximize slide quality.

Check for:
1. Missing important ideas
2. Poor slide ordering or structure
3. Overloaded or unclear bullets
4. Redundant content
5. Incorrect or unnecessary figures
6. Academic clarity and precision

Revise the plan if needed.

Output ONLY improved JSON using the SAME schema.
Do NOT add explanations.

Draft slide plan:
{draft_text}
"""

        refined = self._call_llm(
            system_prompt="You critique and refine academic slide plans.",
            user_prompt=reflection_prompt,
        )

        try:
            return self._safe_json_load(refined)
        except Exception:
            raise RuntimeError("Failed to parse JSON from reflection step.\n\nRaw LLM output:\n" + refined)

