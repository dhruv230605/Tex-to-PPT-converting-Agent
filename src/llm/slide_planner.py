from src.llm.llm_base import BaseLLMAgent


class SlidePlanner(BaseLLMAgent):
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
should be the JSON schema and avoid explanatory prose outside the JSON.

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

Paper title:
{paper_title}

Section title:
{section_title}

Section content:
{section_text}

Available figures:
{figures}

Output: JSON slide plan following the expected schema.
"""

        draft = self._call_llm(
            system_prompt="You plan academic presentation slides.",
            user_prompt=planning_prompt,
        )

        try:
            return self._safe_json_load(draft)
        except Exception:
            raise RuntimeError("Failed to parse JSON from planning step.\n\nRaw LLM output:\n" + draft)
