from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
import os
import subprocess
import shutil
from typing import Optional
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import os
import subprocess
import shutil
from typing import Optional, Iterable


def _strip_latex(text: str) -> str:
    """Remove LaTeX commands and escape sequences from text."""
    if not text:
        return ''
    # Remove \thanks{...} and similar commands
    text = re.sub(r'\\[a-zA-Z]+\*?\{[^}]*\}', '', text)
    # Remove other LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?', '', text)
    # Replace \' and \" escape sequences (e.g., \\'e -> e)
    text = re.sub(r"\\['\"`^~]([a-zA-Z])", r'\1', text)
    # Remove remaining backslashes and braces
    text = text.replace('\\', '').replace('{', '').replace('}', '')
    # Clean up whitespace and line breaks
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _hex_to_rgb(hex_color: str):
    if not hex_color:
        return None
    s = hex_color.lstrip('#')
    if len(s) == 3:
        s = ''.join([c * 2 for c in s])
    try:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        return RGBColor(r, g, b)
    except Exception:
        return None


def _apply_background(slide, hex_color: str):
    rgb = _hex_to_rgb(hex_color)
    if not rgb:
        return
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = rgb


def _safe_text_frame_set(shape, text: str, font_size: Optional[int] = None):
    try:
        tf = shape.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = str(text)
        if font_size:
            run.font.size = Pt(font_size)
        return True
    except Exception:
        return False


def generate_pptx(metadata, slide_plans, image_base, out_file, template_path: str = None):
    """Generate a PPTX file from structured slide plans.

    This function is defensive: it supports multiple slide-plan shapes
    and falls back to plain text when styling or fields are missing.
    """

    if template_path and os.path.exists(template_path):
        try:
            prs = Presentation(template_path)
        except Exception:
            prs = Presentation()
    else:
        prs = Presentation()

    # Title slide (improved styling)
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = metadata.get('title', '')
    author = metadata.get('author', '')
    accent = metadata.get('accent_color') or '#2E7D32'

    # Accent bar at the top
    try:
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.22))
        bar.fill.solid()
        rgb = _hex_to_rgb(accent)
        if rgb:
            bar.fill.fore_color.rgb = rgb
        bar.line.fill.background()
    except Exception:
        pass

    if title:
        try:
            slide.shapes.title.text = title
            # style title
            title_tf = slide.shapes.title.text_frame
            for p in title_tf.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(44)
                    r.font.bold = True
        except Exception:
            _safe_text_frame_set(slide.shapes[0], title, font_size=44)
    if author:
        try:
            # Clean LaTeX commands from author text
            clean_author = _strip_latex(author)
            # placeholder 1 is usually subtitle/author
            slide.placeholders[1].text = clean_author
            try:
                ph = slide.placeholders[1]
                # Reduce font size and set word wrap to prevent overlap
                for p in ph.text_frame.paragraphs:
                    p.word_wrap = True
                    for r in p.runs:
                        r.font.size = Pt(12)
                        r.font.italic = True
            except Exception:
                pass
        except Exception:
            pass

    # NOTE: Abstract intentionally NOT included in slides

    def _iter_slides(plans):
        for plan in plans:
            if isinstance(plan, dict):
                slides = plan.get('slides') or plan.get('pages') or plan.get('frames') or []
                if not slides:
                    # sometimes a dict contains the list under other keys
                    for k in ('plan', 'slides_plan', 'content'):
                        if isinstance(plan.get(k), list):
                            slides = plan.get(k)
                            break
            elif isinstance(plan, list):
                slides = plan
            else:
                slides = []

            for s in slides:
                yield s

    for slide_obj in _iter_slides(slide_plans):
        # Normalize slide data
        if isinstance(slide_obj, str):
            slide_data = {'title': slide_obj, 'bullets': []}
        elif isinstance(slide_obj, dict):
            slide_data = slide_obj
        else:
            slide_data = {'title': str(slide_obj)}

        title_text = slide_data.get('title', '')
        visual_type = slide_data.get('visual_type')
        style = slide_data.get('style', {}) or {}

        # Create slide (use a title+content layout by default)
        s = prs.slides.add_slide(prs.slide_layouts[1])
        if title_text:
            try:
                s.shapes.title.text = title_text
            except Exception:
                _safe_text_frame_set(s.shapes[0], title_text, font_size=28)

        # Apply simple styling if present
        bg = style.get('background_color') or slide_data.get('background_color') or metadata.get('background_color')
        if bg:
            _apply_background(s, bg)

        # Analogy slide: render prominent analogy_text with accent and friendly layout
        if slide_data.get('analogy') or slide_data.get('analogy_text'):
            analogy_text = slide_data.get('analogy_text') or slide_data.get('text') or ''
            try:
                # Title: "Analogy: {short title}"
                short_title = slide_data.get('analogy_title') or (slide_data.get('title') or '').strip()
                # Avoid duplicate "Analogy:" prefix if already present
                if short_title.startswith('Analogy:'):
                    title_str = short_title
                elif short_title:
                    # keep only first 6 words for short title
                    short_title = ' '.join(short_title.split()[:6])
                    title_str = f"Analogy: {short_title}"
                else:
                    title_str = "Analogy"

                s.shapes.title.text = title_str
                # Apply Comic Sans MS, size 28, white color, bold to title
                try:
                    for p in s.shapes.title.text_frame.paragraphs:
                        for r in p.runs:
                            r.font.name = 'Comic Sans MS'
                            r.font.size = Pt(28)
                            r.font.bold = True
                            r.font.color.rgb = RGBColor(255,255,255)
                except Exception:
                    pass

                # Background color is light otange here
                try:
                    _apply_background(s, "#FFA46B")
                except Exception:
                    pass
            except Exception:
                pass

            try:
                ph = s.shapes.placeholders[1]
                _safe_text_frame_set(ph, analogy_text, font_size=20)
            except Exception:
                _safe_text_frame_set(s.shapes[1], analogy_text, font_size=20)

            continue

        # Q&A slides
        if slide_data.get('qa_slide') or slide_data.get('qa_text'):
            qa_text = slide_data.get('qa_text') or slide_data.get('text') or ''
            try:
                s.shapes.title.text = 'Q&A'
                try:
                    for p in s.shapes.title.text_frame.paragraphs:
                        for r in p.runs:
                            r.font.name = 'Comic Sans MS'
                            r.font.size = Pt(28)
                            r.font.bold = True
                            r.font.color.rgb = RGBColor(255,255,255)
                except Exception:
                    pass
                _apply_background(s, '#FFA46B')
            except Exception:
                pass

            try:
                ph = s.shapes.placeholders[1]
                _safe_text_frame_set(ph, qa_text, font_size=20)
            except Exception:
                _safe_text_frame_set(s.shapes[1], qa_text, font_size=20)
            continue

        # References slide (if provided as array)
        refs = slide_data.get('references') or (slide_data.get('bullets') if slide_data.get('type') == 'references' else None)
        if refs:
            try:
                ph = s.shapes.placeholders[1]
                tf = ph.text_frame
                tf.clear()
                for i, r in enumerate(refs):
                    text = r if isinstance(r, str) else r.get('text') or str(r)
                    p = tf.add_paragraph() if i else tf.paragraphs[0]
                    p.text = text
                    p.level = 0
                    # small font for references
                    for run in p.runs:
                        run.font.size = Pt(10)
                        run.font.italic = False
                continue
            except Exception:
                pass

        # Regular bullet slides: fall back to content/text when bullets missing
        bullets = slide_data.get('bullets') or []
        if not bullets:
            # try other fields
            for k in ('text', 'content', 'body', 'summary', 'notes'):
                if slide_data.get(k):
                    val = slide_data.get(k)
                    if isinstance(val, (list, tuple)):
                        bullets = list(val)
                    else:
                        bullets = [str(val)]
                    break

        # Fill content placeholder
        try:
            ph = s.shapes.placeholders[1]
            tf = ph.text_frame
            tf.clear()
            for i, b in enumerate(bullets):
                p = tf.add_paragraph() if i else tf.paragraphs[0]
                p.text = str(b)
                p.level = 0
                # styling bullets
                for run in p.runs:
                    run.font.size = Pt(20)
                p.space_after = Pt(6)
                # highlight emphasized bullets
                emphasis = slide_data.get('visual_emphasis') or style.get('visual_emphasis') or []
                if isinstance(emphasis, Iterable) and i in emphasis:
                    for run in p.runs:
                        run.font.bold = True
                        rgb = _hex_to_rgb(style.get('accent_color') or accent)
                        if rgb:
                            run.font.color.rgb = rgb
        except Exception:
            # best-effort fallback: try first shape
            try:
                _safe_text_frame_set(s.shapes[1], "\\n".join([str(x) for x in bullets]))
            except Exception:
                pass

        # Figures/images
        for fig in slide_data.get('figures', []):
            fig_name = None
            if isinstance(fig, str):
                fig_name = fig
            elif isinstance(fig, dict):
                fig_name = fig.get('path') or fig.get('file') or fig.get('src') or fig.get('name')

            if not fig_name:
                continue

            # Try to resolve the figure path by testing common extensions and folders
            def _resolve_fig(name):
                # ignore URLs
                if isinstance(name, str) and name.startswith(('http://', 'https://')):
                    return None

                candidates = []
                base_no_ext, ext = os.path.splitext(name)
                
                # If name already includes extension
                if ext:
                    # Skip PDFs - python-pptx can't embed them directly
                    if ext.lower() == '.pdf':
                        return None
                    candidates.append(os.path.join(image_base, name))
                else:
                    # No extension: try common image formats (PNG/JPG first, skip PDF)
                    for e in ('.png', '.jpg', '.jpeg', '.svg'):
                        candidates.append(os.path.join(image_base, base_no_ext + e))

                # Also try common subfolders
                for folder in ('Figures', 'figures', 'vis', 'images'):
                    if ext:
                        candidates.append(os.path.join(image_base, folder, name))
                    else:
                        for e in ('.png', '.jpg', '.jpeg', '.svg'):
                            candidates.append(os.path.join(image_base, folder, base_no_ext + e))

                # Deduplicate while preserving order
                seen = set()
                for c in candidates:
                    if c and c not in seen:
                        seen.add(c)
                        if os.path.exists(c):
                            return c
                return None

            fig_path = _resolve_fig(fig_name)
            if fig_path:
                try:
                    img_slide = prs.slides.add_slide(prs.slide_layouts[6])
                    img_slide.shapes.add_picture(fig_path, Inches(1), Inches(1), height=Inches(5))
                except Exception:
                    pass

    # Save the presentation
    prs.save(out_file)
