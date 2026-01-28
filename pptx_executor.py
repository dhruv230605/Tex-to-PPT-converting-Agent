from pptx import Presentation
from pptx.util import Inches
import os

def generate_pptx(metadata, slide_plans, image_base, out_file):
    prs = Presentation()

    # Title slide
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = metadata["title"]
    slide.placeholders[1].text = metadata["author"]

    if metadata["abstract"]:
        s = prs.slides.add_slide(prs.slide_layouts[1])
        s.shapes.title.text = "Abstract"
        s.shapes.placeholders[1].text = metadata["abstract"]

    for plan in slide_plans:
        for slide_plan in plan["slides"]:
            s = prs.slides.add_slide(prs.slide_layouts[1])
            s.shapes.title.text = slide_plan["title"]

            tf = s.shapes.placeholders[1].text_frame
            tf.clear()

            for i, bullet in enumerate(slide_plan["bullets"]):
                p = tf.add_paragraph() if i else tf.paragraphs[0]
                p.text = bullet
                p.level = 0

            for fig in slide_plan.get("figures", []):
                fig_path = os.path.join(image_base, fig)
                if os.path.exists(fig_path):
                    img_slide = prs.slides.add_slide(prs.slide_layouts[6])
                    img_slide.shapes.add_picture(
                        fig_path, Inches(1), Inches(1), height=Inches(5)
                    )

    prs.save(out_file)
