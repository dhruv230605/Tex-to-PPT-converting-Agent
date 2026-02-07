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
    """Produces an initial slide plan (JSON) from a paper section.

    Args:
        perspective: short string describing POV, e.g. 'professor' to produce
        slides tailored for teaching (learning objectives, examples, exercises).
    """

    def plan(
        self,
        paper_title: str,
        section_title: str,
        section_text: str,
        figures: list,
        include_all_figures: bool = True,
        analogy_level: str = "10-year-old",
    ):
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
- Include ALL provided figures unless they are absolutely irrelevant
- Do NOT include LaTeX commands
- Output ONLY valid JSON (no explanations)

Perspective: Professor / Teaching

Include explicit learning objectives, teaching notes, examples, common
misconceptions, and suggested in-class exercises where appropriate. Format
should remain the JSON schema below and avoid explanatory prose outside the JSON.

For hard technical concepts or complex derivations, also generate a separate
"analogy" slide immediately after the technical slide. The analogy slide
should explain the idea at the level of a {analogy_level} using a clear,
concrete metaphor or everyday example. Mark those slides with
"analogy": true and include an "analogy_text" field. Also include
"analogy_color": "#FFDD00" in the analogy slide metadata so executors can
render it in a distinct highlight color that professors can skip or show
as desired.

For professor perspective, include a "Q&A" slide after major sections asking
students questions, encouraging discussion, or prompting them to think about
key ideas. Mark Q&A slides with "qa_slide": true and include a "qa_text" field
with the discussion prompt.

Include references as appropriate (not forced on every slide). Format:
- If the content comes from the paper, cite it as:
  {{"type": "paper", "source": "Paper: [section/page reference]", "text": "Brief note"}}
- If the content is from external material, cite it as:
  {{"type": "external", "source": "[Source name]", "text": "Brief note"}}
- For AI-generated explanations or recommendations, mark as:
  {{"type": "ai_recommendation", "source": "AI-generated", "text": "Brief note"}}
References should appear in smaller text at the bottom of slides in the output.

Paper title:
{paper_title}

Section title:
{section_title}

Section content:
{section_text}

Available figures:
{figures}

JSON schema examples:
{{
  "slides": [
    {{
      "title": "Technical idea",
      "bullets": ["..."],
      "figures": ["fig1.png"],
      "references": [
        {{"type": "paper", "source": "Paper: Section 2", "text": "Main concept introduced here"}}
      ],
      "metadata": {{"analogy": false}}
    }},
    {{
      "title": "Technical idea — Analogy",
      "bullets": ["Simple explanation for kids"],
      "figures": [],
      "analogy": true,
      "analogy_text": "Explain like I'm {analogy_level}: ...",
      "analogy_color": "#FFDD00",
      "references": [],
      "metadata": {{"analogy": true}}
    }},
    {{
      "title": "Questions for Discussion",
      "bullets": ["What would happen if...?", "How does this relate to...?"],
      "qa_slide": true,
      "qa_text": "Pause here and ask students to share their understanding.",
      "references": [],
      "metadata": {{"qa_slide": true, "skip_color": "#E8F4F8"}}
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

    def refine(self, draft_plan: str, include_all_figures: bool = True, analogy_level: str = "10-year-old"):
        # Accept dicts as well as raw strings
        if isinstance(draft_plan, dict):
            draft_text = json.dumps(draft_plan)
        else:
            draft_text = str(draft_plan)

        # Optimize for professor teaching POV
        perspective_block = (
            "\n\nPerspective: Professor / Teaching\n\n"
            "Emphasize clarity for learners, ensure learning objectives are clear,"
            " and suggest pedagogical adjustments."
        )

        figures_block = "\n\nInclude ALL provided figures unless they are absolutely irrelevant.\n" if include_all_figures else "\n\nDo not force inclusion of all figures; include only helpful ones.\n"

        analogy_block = (
            f"\n\nFor any hard technical concept, add an analogy slide explaining the idea at the level of a {analogy_level}.\n"
            "Mark analogy slides with \"analogy\": true, include an \"analogy_text\" field, and set \"analogy_color\": \"#FFDD00\" in metadata.\n"
            "Place each analogy slide immediately after the technical slide it explains.\n"
        )

        qa_block = (
            "\n\nFor professor perspective, after major sections, insert a \"Q&A\" slide with questions for discussion.\n"
            "Mark Q&A slides with \"qa_slide\": true and include a \"qa_text\" field with the discussion prompt.\n"
        )

        references_block = (
            "\n\nInclude references as appropriate (not on every slide). For each reference:\n"
            "- If from the paper, use {\"type\": \"paper\", \"source\": \"Paper: [section]\", \"text\": \"...\"}\n"
            "- If external source, use {\"type\": \"external\", \"source\": \"[name]\", \"text\": \"...\"}\n"
            "- If AI-generated, use {\"type\": \"ai_recommendation\", \"source\": \"AI-generated\", \"text\": \"...\"}\n"
            "References will appear in smaller text at the bottom of slides.\n"
        )

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

{figures_block}
{analogy_block}
{qa_block}
{references_block}

Output ONLY improved JSON using the SAME schema.
Do NOT add explanations.

Draft slide plan:
{draft_text}
{perspective_block}
"""

        refined = self._call_llm(
            system_prompt="You critique and refine academic slide plans.",
            user_prompt=reflection_prompt,
        )

        try:
            return self._safe_json_load(refined)
        except Exception:
            raise RuntimeError("Failed to parse JSON from reflection step.\n\nRaw LLM output:\n" + refined)

