import json
from openai import OpenAI
import re


class SlidePlanningAgent:
    def __init__(self, api_key, model="gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    # ----------------------------
    # Low-level LLM call
    # ----------------------------
    def _call_llm(self, system_prompt, user_prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.25,
        )
        return response.choices[0].message.content.strip()

    # ----------------------------
    # Robust JSON loader
    # - removes ```json fences
    # - escapes LaTeX backslashes
    # ----------------------------
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

        # 🔑 CRITICAL FIX:
        # Escape single backslashes used in LaTeX math: \( \) \_
        # This makes the string valid JSON
        text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)

        return json.loads(text)

    # ----------------------------
    # Planner + Reflection Agent
    # ----------------------------
    def plan_and_refine(
        self,
        paper_title: str,
        section_title: str,
        section_text: str,
        figures: list,
    ):
        # ---------- STEP 1: PLANNING ----------
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

        # ---------- STEP 2: REFLECTION ----------
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
{draft}
"""

        refined = self._call_llm(
            system_prompt="You critique and refine academic slide plans.",
            user_prompt=reflection_prompt,
        )

        try:
            return self._safe_json_load(refined)
        except Exception as e:
            raise RuntimeError(
                "❌ Failed to parse JSON from reflection step.\n\n"
                "Raw LLM output:\n"
                f"{refined}"
            ) from e
