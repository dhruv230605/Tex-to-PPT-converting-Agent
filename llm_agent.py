"""
Adapter module to preserve public API of the original `llm_agent` while
distributing responsibilities across smaller agents.

Public exports:
- `SlidePlanner`
- `SlideRefiner`
- `StyleAgent`

Existing code that does `from llm_agent import SlidePlanner, SlideRefiner` will
continue to work.
"""

from src.llm.slide_planner import SlidePlanner
from src.llm.slide_refiner import SlideRefiner
from src.llm.style_agent import StyleAgent

__all__ = ["SlidePlanner", "SlideRefiner", "StyleAgent"]
