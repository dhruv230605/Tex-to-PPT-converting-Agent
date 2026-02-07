import argparse
import os
import subprocess
from pathlib import Path
from src.parser.latex_parser import parse_latex
from src.llm.slide_planner import SlidePlanner
from src.llm.slide_refiner import SlideRefiner
from src.llm.style_agent import StyleAgent
from src.executors.pptx_executor import generate_pptx, export_to_pdf

# Optionally load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; environment variables can be set otherwise
    pass

def main():
    parser = argparse.ArgumentParser("LaTeX → PowerPoint LLM Agent (PPTX-first)")
    parser.add_argument("--input", required=True, help="Main .tex file (root of paper)")
    parser.add_argument("--api-key", required=False, help="OpenAI API key (or set OPENAI_API_KEY in env or .env)")
    parser.add_argument("--use-reflection", action="store_true", help="Enable LLM-driven reflection loop (may modify slide plans); requires API key")
    parser.add_argument("--template", required=False, help="Optional .pptx template file to apply (masters/layouts/styles)")
    parser.add_argument("--out", required=True, help="Output .pptx file path")
    parser.add_argument("--rounds", type=int, default=2, help="Number of refinement rounds (default: 2)")
    parser.add_argument("--export-pdf", action="store_true", help="Optionally export generated PPTX to PDF using LibreOffice headless if available")
    args = parser.parse_args()

    # Resolve API key: CLI arg > environment variable
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OpenAI API key required via --api-key or OPENAI_API_KEY env var")

    metadata, sections = parse_latex(args.input)
    planner = SlidePlanner(api_key=api_key)
    refiner = SlideRefiner(api_key=api_key)

    slide_plans = []
    style_agent = StyleAgent()
    for sec in sections:
        draft = planner.plan(
            paper_title=metadata.get("title", ""),
            section_title=sec.get("title", ""),
            section_text=sec.get("content", ""),
            figures=sec.get("figures", []),
            include_all_figures=True,
            analogy_level="10-year-old",
        )

        refined = refiner.refine(
            draft_plan=draft,
            include_all_figures=True,
            analogy_level="10-year-old",
            rounds=args.rounds,
        )

        # StyleAgent: optionally run LLM-driven reflection then deterministic optimization
        if args.use_reflection:
            styled = style_agent.reflect_and_optimize(refined, api_key=api_key, max_rounds=args.rounds)
        else:
            styled = style_agent.optimize_plan(refined)
        # styled is a dict with 'slides' key; preserve as a plan dict
        slide_plans.append({'slides': styled['slides'], 'style_critiques': styled.get('style_critiques', [])})

    image_base = str(Path(args.input).parent)

    out_path = Path(args.out)
    if out_path.suffix.lower() != ".pptx":
        out_path = out_path.with_suffix('.pptx')

    generate_pptx(metadata, slide_plans, image_base, str(out_path), template_path=args.template)
    print("✅ PPTX generated:", str(out_path))

    if args.export_pdf:
        pdf_path = export_to_pdf(str(out_path))
        if pdf_path:
            print("✅ Exported to PDF:", pdf_path)
        else:
            print("⚠️ LibreOffice not found or export failed; PPTX retained at:", str(out_path))

if __name__ == "__main__":
    main()
