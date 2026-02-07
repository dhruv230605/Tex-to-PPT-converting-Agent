import re
import json
from copy import deepcopy

from src.llm.slide_critic import SlideCritic


class StyleAgent:
    """Deterministic helper for slide styling and sanitization.

    Provides utilities to enforce default style metadata, remove emojis,
    and convert a few common unicode tokens to LaTeX-friendly forms.
    """

    GREEK_MAP = {
        'α': '\\alpha',
        'β': '\\beta',
        'γ': '\\gamma',
        'ε': '\\epsilon',
        'λ': '\\lambda',
    }

    @staticmethod
    def strip_emojis(text: str) -> str:
        if not text:
            return ''
        # remove most common emoji ranges (simple heuristic)
        return re.sub(r'[\U0001F300-\U0001F6FF\U0001F900-\U0001F9FF\u2600-\u26FF]+', '', text)

    @classmethod
    def convert_greek(cls, text: str) -> str:
        if not text:
            return ''
        for k, v in cls.GREEK_MAP.items():
            text = text.replace(k, v)
        return text

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        text = cls.strip_emojis(text)
        text = cls.convert_greek(text)
        # collapse whitespace
        return ' '.join(text.split())

    @staticmethod
    def ensure_style_metadata(slide: dict):
        slide.setdefault('background_color', '#FFFFFF')
        slide.setdefault('text_color', '#333333')
        slide.setdefault('accent_color', '#2E7D32')
        slide.setdefault('visual_type', 'technical')
        slide.setdefault('visual_emphasis', [])
        return slide

    @classmethod
    def _split_to_bullets(cls, text: str, max_chars: int = 180):
        """Convert long paragraph text into a list of bullets by sentence.

        max_chars is a heuristic target for per-bullet length; sentences
        longer than that will be further chunked.
        """
        if not text:
            return []
        # naive sentence split
        parts = re.split(r'(?<=[\.\?!])\s+', text.strip())
        bullets = []
        for s in parts:
            s = s.strip()
            if not s:
                continue
            if len(s) <= max_chars:
                bullets.append(s)
            else:
                # chunk long sentence into smaller pieces
                for i in range(0, len(s), max_chars):
                    bullets.append(s[i:i+max_chars].strip())
        return bullets

    @classmethod
    def optimize_plan(cls, plan):
        """Take a single refined plan (dict or list) and return an optimized
        plan with styling metadata and text-length fixes applied.

        Returns a dict with keys: 'slides' (list) and 'style_critiques' (list).
        """
        slides = []
        critiques = []

        # normalize incoming plan to iterable of slides
        if isinstance(plan, dict):
            candidates = plan.get('slides') or plan.get('pages') or plan.get('frames') or []
            if not candidates:
                for k in ('plan', 'slides_plan', 'content'):
                    if isinstance(plan.get(k), list):
                        candidates = plan.get(k)
                        break
        elif isinstance(plan, list):
            candidates = plan
        else:
            candidates = []

        for s in candidates:
            if isinstance(s, str):
                slide = {'title': cls.sanitize_text(s), 'bullets': []}
            elif isinstance(s, dict):
                slide = {k: v for k, v in s.items()}
            else:
                slide = {'title': cls.sanitize_text(str(s)), 'bullets': []}

            # Ensure styling metadata exists
            cls.ensure_style_metadata(slide)

            # Sanitize textual fields (accept lists by joining)
            for text_key in ('title', 'text', 'content', 'body', 'summary', 'notes'):
                if slide.get(text_key):
                    val = slide[text_key]
                    if isinstance(val, (list, tuple)):
                        val = ' '.join(str(x) for x in val)
                    slide[text_key] = cls.sanitize_text(val)

            # If bullets missing but there is long text, convert to bullets
            bullets = slide.get('bullets') or []
            if not bullets:
                for k in ('text', 'content', 'body', 'summary', 'notes'):
                    val = slide.get(k)
                    if val:
                        if isinstance(val, (list, tuple)):
                            bullets = list(val)
                        else:
                            # if long, split into bullets
                            if len(val) > 220:
                                bullets = cls._split_to_bullets(val)
                                critiques.append(f"Converted long {k} to {len(bullets)} bullets for slide: {slide.get('title')}")
                            else:
                                bullets = [val]
                        break

            # If bullets present but each bullet is very long, try to split
            new_bullets = []
            for b in bullets:
                if isinstance(b, str) and len(b) > 200:
                    split = cls._split_to_bullets(b)
                    new_bullets.extend(split)
                    critiques.append(f"Split long bullet into {len(split)} smaller bullets on slide: {slide.get('title')}")
                else:
                    new_bullets.append(b)

            slide['bullets'] = new_bullets

            # If slide still has too many characters overall, mark it for splitting
            total_chars = sum(len(str(x)) for x in slide.get('bullets', [])) + len(str(slide.get('title', '')))
            if total_chars > 700:
                # naive split: keep first half bullets, move rest to a follow-up slide
                mid = max(1, len(slide['bullets']) // 2)
                first = {**slide, 'bullets': slide['bullets'][:mid]}
                second = {**slide, 'bullets': slide['bullets'][mid:], 'title': (slide.get('title') + ' (cont.)')}
                slides.append(first)
                slides.append(second)
                critiques.append(f"Split slide '{slide.get('title')}' into two for readability")
            else:
                slides.append(slide)

        return {'slides': slides, 'style_critiques': critiques}

    @classmethod
    def reflect_and_optimize(cls, plan, api_key: str = None, max_rounds: int = 2, analogy_level: str = "10-year-old", include_all_figures: bool = True):
        """Run an LLM-driven reflection loop over `plan`, then apply deterministic optimizations.

        If `api_key` is not provided, falls back to `optimize_plan` only.

        Returns the same dict shape as `optimize_plan` but with additional
        entries in `style_critiques` summarizing LLM feedback and iteration info.
        """
        # No API key -> deterministic path only
        if not api_key:
            result = cls.optimize_plan(plan)
            result['style_critiques'].append('Reflection skipped (no api_key)')
            return result

        critic = SlideCritic(api_key=api_key)

        # Normalize initial plan text
        try:
            current_plan_json = plan if isinstance(plan, (dict, list)) else json.loads(json.dumps(plan))
        except Exception:
            current_plan_json = plan

        aggregated_llm_critiques = []

        last_text = json.dumps(current_plan_json, sort_keys=True)

        for round_i in range(1, max_rounds + 1):
            prompt_text = json.dumps(current_plan_json, indent=2)
            try:
                critique_raw = critic.critique_once(prompt_text, include_all_figures=include_all_figures, analogy_level=analogy_level)
            except Exception as e:
                aggregated_llm_critiques.append(f"LLM critique failed on round {round_i}: {e}")
                break

            # Try to parse JSON response
            parsed = None
            try:
                parsed = critic._safe_json_load(critique_raw)
            except Exception:
                # If the critic returned raw text without clean JSON, keep that as a critique and stop
                aggregated_llm_critiques.append(f"Round {round_i} raw critique: {critique_raw}")
                break

            # Compare normalized text to see if changed
            try:
                parsed_text = json.dumps(parsed, sort_keys=True)
            except Exception:
                aggregated_llm_critiques.append(f"Round {round_i} returned non-serializable plan")
                break

            if parsed_text == last_text:
                aggregated_llm_critiques.append(f"Converged after {round_i} round(s)")
                current_plan_json = parsed
                break

            aggregated_llm_critiques.append(f"Applied LLM suggestions from round {round_i}")
            current_plan_json = parsed
            last_text = parsed_text

        # Finally apply deterministic optimize_plan for text sanitization and bullet splitting
        final = cls.optimize_plan(current_plan_json)
        # Prefix LLM critiques for clarity
        final['style_critiques'] = (aggregated_llm_critiques or []) + final.get('style_critiques', [])
        return final
