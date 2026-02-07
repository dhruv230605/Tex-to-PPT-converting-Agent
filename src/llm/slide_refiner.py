import json
from src.llm.slide_critic import SlideCritic
from src.llm.llm_base import BaseLLMAgent


class SlideRefiner(BaseLLMAgent):
    """Orchestrates multiple rounds of critique using `SlideCritic`.

    Keeps the public `refine()` API compatible with the original implementation.
    """

    def __init__(self, api_key, model="gpt-4o-mini"):
        super().__init__(api_key=api_key, model=model)
        self.critic = SlideCritic(api_key=api_key, model=model)

    def refine(self, draft_plan: str, include_all_figures: bool = True, analogy_level: str = "10-year-old", rounds: int = 2):
        if isinstance(draft_plan, dict):
            current_plan = draft_plan
            current_text = json.dumps(draft_plan)
        else:
            current_text = str(draft_plan)
            current_plan = self._safe_json_load(current_text)

        critique_history = []

        for round_num in range(1, rounds + 1):
            current_text = json.dumps(current_plan)

            # Call critic for a single round
            result_text = self.critic.critique_once(current_text, include_all_figures=include_all_figures, analogy_level=analogy_level)

            # Attempt to extract and parse JSON
            try:
                json_part = self.critic._extract_json(result_text) if isinstance(result_text, str) else result_text
            except Exception:
                # fallback: try loading whole text
                json_part = result_text

            try:
                current_plan = self._safe_json_load(json_part) if isinstance(json_part, str) else json_part
            except Exception as e:
                raise RuntimeError(f"Failed to parse JSON from reflection round {round_num}: {e}\n\nRaw output:\n{result_text}")

            critique_history.append(f"Round {round_num}: refined")

        return current_plan
