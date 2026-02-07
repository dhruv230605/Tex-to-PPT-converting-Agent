from src.llm.llm_base import BaseLLMAgent


class SlideCritic(BaseLLMAgent):
    """Performs a single critique/refinement pass over a slide plan."""

    def critique_once(self, current_plan_text: str, include_all_figures: bool = True, analogy_level: str = "10-year-old") -> str:
        figures_block = "\n\nInclude ALL provided figures unless they are absolutely irrelevant.\n" if include_all_figures else "\n\nInclude only helpful figures.\n"

        analogy_block = (
            f"\n\nFor any hard technical concept, add an analogy slide explaining the idea at the level of a {analogy_level}.\n"
            "Mark analogy slides with \"analogy\": true and include an \"analogy_text\" field."
        )

        reflection_prompt = f"""
You are a reflection and optimization agent.

Your goal: Improve the slide plan below to maximize slide quality AND aesthetic appeal.

Check for:
1. Missing important ideas
2. Poor slide ordering or structure
3. Overloaded or unclear bullets
4. Redundant content
5. Incorrect or unnecessary figures
6. Academic clarity and precision
7. Visual appeal and hierarchy
8. Analogy slide distinctiveness
9. Color harmony
10. Typography hierarchy

{figures_block}
{analogy_block}

Output ONLY improved JSON using the same schema (no extra prose).

Draft slide plan:
{current_plan_text}
"""

        result = self._call_llm(
            system_prompt="You critique and refine academic slide plans.",
            user_prompt=reflection_prompt,
        )

        try:
            return self._extract_json(result)
        except Exception:
            return result
