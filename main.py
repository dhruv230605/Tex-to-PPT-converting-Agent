import argparse
from pathlib import Path
from latex_parser import parse_latex
from llm_agent import SlidePlanningAgent
from pptx_executor import generate_pptx
from beamer_executor import generate_beamer

def main():
    parser = argparse.ArgumentParser("LaTeX → Slides LLM Agent")
    parser.add_argument("--input", required=True, help="Main .tex file")
    parser.add_argument("--api-key", required=True, help="OpenAI API key")
    parser.add_argument("--format", choices=["pptx", "beamer"], default="pptx")
    parser.add_argument("--out", required=True, help="Output file")
    args = parser.parse_args()

    metadata, sections = parse_latex(args.input)
    agent = SlidePlanningAgent(api_key=args.api_key)

    slide_plans = []
    for sec in sections:
        plan = agent.plan_and_refine(
            paper_title=metadata["title"],
            section_title=sec["title"],
            section_text=sec["content"],
            figures=sec["figures"]
        )
        slide_plans.append(plan)

    image_base = str(Path(args.input).parent)

    if args.format == "pptx":
        generate_pptx(metadata, slide_plans, image_base, args.out)
    else:
        generate_beamer(metadata, slide_plans, image_base, args.out)

    print("✅ Slides generated:", args.out)

if __name__ == "__main__":
    main()
