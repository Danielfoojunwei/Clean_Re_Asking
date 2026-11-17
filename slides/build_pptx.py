"""Builds Epistemics_Sprint_Slides.pptx: each slide of slides.html as a full-slide image, with that slide's spoken script
from SCRIPT.md in the speaker notes. Run after build_slides.py and build_script.py:
    node render_pngs.js <png_dir> && python3 build_pptx.py <png_dir>"""
import re, sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches

HERE = Path(__file__).resolve().parent
png_dir = Path(sys.argv[1])
script = (HERE / "SCRIPT.md").read_text()
notes = {}
for sec in re.split(r"\n## ", script)[1:]:
    head = sec.split("\n")[0]
    m = re.match(r"Slide (\d+): (.*)", head)
    if not m:
        continue
    body = "\n\n".join(l for l in sec.split("\n")[1:] if l.strip() and not l.startswith("**One line"))
    notes[int(m.group(1))] = f"{m.group(2)}\n\n{body}"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
blank = prs.slide_layouts[6]
pngs = sorted(png_dir.glob("slide-*.png"), key=lambda q: int(q.stem.split("-")[1]))
for k, png in enumerate(pngs, start=1):
    sl = prs.slides.add_slide(blank)
    sl.shapes.add_picture(str(png), 0, 0, width=prs.slide_width, height=prs.slide_height)
    sl.notes_slide.notes_text_frame.text = notes.get(k, "")
prs.core_properties.title = "Clean Re-asking: Why Pushback Benchmarks Disagree and How It Happens"
prs.core_properties.author = "Daniel Foo"
out = HERE / "Epistemics_Sprint_Slides.pptx"
prs.save(out)
print(out.name, len(pngs), "slides,", sum(1 for k in notes if k <= len(pngs)), "with speaker notes")
