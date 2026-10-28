"""
update_slides.py — Adds Results and Limitations slides to the existing PPTX.
Saves as: Medical-Question-Answering-using-Llama-3-RAG-UPDATED.pptx
Does NOT overwrite the original.

New content:
  Slide 11: Experimental Setup & Evaluation Protocol
  Slide 12: Results — Configuration 1 (RAG v1) & Baseline
  Slide 13: Results — Main Result: RAG v2
  Slide 14: Retrieval & Groundedness Analysis
  Slide 15: Error Analysis — RAG v2
  Slide 16: Limitations & Honest Caveats
  Slide 17: Conclusion
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import copy

SRC = "Medical-Question-Answering-using-Llama-3-RAG.pptx"
DST = "Medical-Question-Answering-using-Llama-3-RAG-UPDATED.pptx"

prs = Presentation(SRC)

# Dimensions (widescreen 13.33 x 7.5 in)
W = prs.slide_width
H = prs.slide_height

# ── Colour palette (matching existing dark navy theme) ───────
NAVY   = RGBColor(0x0D, 0x1B, 0x2A)   # slide background
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = RGBColor(0x00, 0xB4, 0xD8)   # bright cyan accent
GOLD   = RGBColor(0xF4, 0xA2, 0x61)   # orange/gold
GREEN  = RGBColor(0x2D, 0xC6, 0x53)
RED    = RGBColor(0xE6, 0x3B, 0x3B)
LGRAY  = RGBColor(0xB0, 0xBE, 0xC5)


def blank_slide(prs):
    """Add a blank slide using the first available blank layout."""
    blank_layout = prs.slide_layouts[0]  # index 0 = DEFAULT (only 2 layouts exist)
    return prs.slides.add_slide(blank_layout)


def set_bg(slide, colour=NAVY):
    """Fill slide background with a solid colour."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = colour


def add_textbox(slide, text, left, top, width, height,
                font_size=18, bold=False, colour=WHITE,
                align=PP_ALIGN.LEFT, wrap=True, italic=False):
    txb = slide.shapes.add_textbox(left, top, width, height)
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = colour
    run.font.italic = italic
    return txb


def add_label_value(slide, label, value, left, top, width, height,
                    label_size=13, value_size=26,
                    label_colour=LGRAY, value_colour=WHITE):
    """Two-line stat: small label above, large bold value below."""
    txb = slide.shapes.add_textbox(left, top, width, height)
    tf = txb.text_frame
    tf.word_wrap = True
    # Line 1: label
    p1 = tf.paragraphs[0]
    p1.alignment = PP_ALIGN.CENTER
    r1 = p1.add_run()
    r1.text = label
    r1.font.size = Pt(label_size)
    r1.font.color.rgb = label_colour
    # Line 2: value
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    r2.text = value
    r2.font.size = Pt(value_size)
    r2.font.bold = True
    r2.font.color.rgb = value_colour


def add_divider(slide, top, colour=ACCENT):
    """Thin horizontal line."""
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(0.5), top, W - Inches(1), Pt(2)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = colour
    shape.line.fill.background()


def slide_header(slide, label, title, subtitle=None):
    """Standard slide header: small label, large title, optional subtitle."""
    add_textbox(slide, label, Inches(0.5), Inches(0.25), W - Inches(1), Inches(0.35),
                font_size=10, colour=ACCENT, bold=True)
    add_textbox(slide, title, Inches(0.5), Inches(0.55), W - Inches(1), Inches(0.65),
                font_size=28, bold=True, colour=WHITE)
    if subtitle:
        add_textbox(slide, subtitle, Inches(0.5), Inches(1.15), W - Inches(1), Inches(0.45),
                    font_size=13, colour=LGRAY, italic=True)
    add_divider(slide, Inches(1.55))


# ═══════════════════════════════════════════════════════════════
# Slide 11 — Experimental Setup
# ═══════════════════════════════════════════════════════════════
sl = blank_slide(prs)
set_bg(sl)
slide_header(sl,
    "EXPERIMENTAL SETUP",
    "Evaluation Protocol",
    "All results are read-only from saved JSONL files — no re-running of LLM inference for this analysis.")

boxes = [
    ("Dataset", "MedQA (USMLE) test split\n1,273 total questions available\nSample of 300 questions used (seed=42, fixed)"),
    ("Generator", "Llama 3 8B (llama3:latest)\nRunning locally via Ollama\nCPU-only, temperature=0.8 (default)"),
    ("Retriever", "all-MiniLM-L6-v2 embeddings (384-dim)\nFAISS IndexFlatIP, 36,723 chunks\n18 medical textbooks, 300–500 words/chunk"),
    ("Controls", "Baseline: same 300 questions, no retrieval\nRAG v1: original prompt (abstains if unsure)\nRAG v2: forced-choice prompt, tuned on 100-Q val split"),
]

col_w = Inches(2.9)
col_h = Inches(2.0)
col_top = Inches(1.75)
for i, (label, body) in enumerate(boxes):
    col_left = Inches(0.4) + i * (col_w + Inches(0.15))
    box = sl.shapes.add_shape(1, col_left, col_top, col_w, col_h)
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0x14, 0x2A, 0x40)
    box.line.color.rgb = ACCENT

    add_textbox(sl, label, col_left + Inches(0.1), col_top + Inches(0.08),
                col_w - Inches(0.2), Inches(0.3),
                font_size=11, bold=True, colour=ACCENT)
    add_textbox(sl, body, col_left + Inches(0.1), col_top + Inches(0.38),
                col_w - Inches(0.2), col_h - Inches(0.5),
                font_size=11, colour=WHITE)

add_textbox(sl,
    "Validation split (100 questions, seed=42 from dev set) was used exclusively for prompt tuning "
    "before the single, final test run — preventing any leakage from the 300-question test set.",
    Inches(0.5), Inches(3.9), W - Inches(1), Inches(0.5),
    font_size=12, colour=GOLD, italic=True)


# ═══════════════════════════════════════════════════════════════
# Slide 12 — Configuration 1 (RAG v1) & Baseline
# ═══════════════════════════════════════════════════════════════
sl = blank_slide(prs)
set_bg(sl)
slide_header(sl,
    "RESULTS",
    "Configuration 1 — RAG v1 vs. Baseline (No Retrieval)",
    "Original prompt included a hedging clause ('say so rather than guessing') causing 20% abstention.")

stats = [
    ("RAG v1\nAccuracy", "42.67%", WHITE),
    ("RAG v1\nAbstention", "20.33%", RED),
    ("Baseline\nAccuracy", "48.67%", WHITE),
    ("Baseline\nAbstention", "0.67%", GREEN),
    ("Difference\n(RAG − Base)", "−6.00 pp", RED),
]
col_w = Inches(2.3)
col_h = Inches(1.5)
top = Inches(1.8)
for i, (lbl, val, col) in enumerate(stats):
    left = Inches(0.35) + i * (col_w + Inches(0.1))
    box = sl.shapes.add_shape(1, left, top, col_w, col_h)
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0x14, 0x2A, 0x40)
    box.line.color.rgb = ACCENT
    add_label_value(sl, lbl, val,
                    left, top, col_w, col_h,
                    value_colour=col)

# 2x2 table as text
table_text = (
    "2×2 Contingency Table (n=300)\n\n"
    "                    Baseline ✓    Baseline ✗\n"
    "  RAG v1 ✓              95             33\n"
    "  RAG v1 ✗              51            121\n\n"
    "RAG v1 is correct on 33 questions the baseline gets wrong — evidence of real retrieval benefit.\n"
    "Baseline is correct on 51 questions RAG v1 gets wrong — mostly due to abstention inflating errors."
)
add_textbox(sl, table_text,
            Inches(0.5), Inches(3.45), W - Inches(1), Inches(2.8),
            font_size=12, colour=WHITE)

add_textbox(sl,
    "⚠  RAG v1's 6 pp deficit vs. baseline is almost entirely explained by abstention (UNPARSED=61). "
    "On parsed answers only, RAG v1 accuracy was 53.6% — higher than baseline.",
    Inches(0.5), Inches(6.2), W - Inches(1), Inches(0.6),
    font_size=11, colour=GOLD, italic=True)


# ═══════════════════════════════════════════════════════════════
# Slide 13 — Main Result: RAG v2
# ═══════════════════════════════════════════════════════════════
sl = blank_slide(prs)
set_bg(sl)
slide_header(sl,
    "RESULTS · MAIN RESULT",
    "RAG v2 — Forced-Choice Prompt (Final Configuration)",
    "Prompt revised after validation on 100 held-out dev questions. Single test run on 300 questions.")

stats2 = [
    ("RAG v2\nAccuracy", "52.00%", GREEN),
    ("RAG v2\nAbstention", "0%", GREEN),
    ("Baseline\nAccuracy", "48.67%", WHITE),
    ("Gain over\nBaseline", "+3.33 pp", GREEN),
    ("Val accuracy\n(100-Q dev)", "63.00%", ACCENT),
]
col_w = Inches(2.3)
col_h = Inches(1.5)
top = Inches(1.8)
for i, (lbl, val, col) in enumerate(stats2):
    left = Inches(0.35) + i * (col_w + Inches(0.1))
    box = sl.shapes.add_shape(1, left, top, col_w, col_h)
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0x14, 0x2A, 0x40)
    box.line.color.rgb = ACCENT
    add_label_value(sl, lbl, val,
                    left, top, col_w, col_h,
                    value_colour=col)

progression = (
    "Accuracy progression on 300 MedQA test questions (same sample, seed=42):\n\n"
    "  Baseline (no retrieval):    48.67%  ←  control\n"
    "  RAG v1 (original prompt):   42.67%  ←  20.3% abstention dragged accuracy down\n"
    "  RAG v2 (revised prompt):    52.00%  ←  MAIN RESULT  (+3.33 pp over baseline, 0% abstention)"
)
add_textbox(sl, progression,
            Inches(0.5), Inches(3.45), W - Inches(1), Inches(2.0),
            font_size=13, colour=WHITE)

add_textbox(sl,
    "Prompt design: RAG v2 always commits to one answer letter and ends with 'Answer: <letter>'. "
    "It uses retrieved context when helpful, falls back to parametric knowledge when context is off-topic.",
    Inches(0.5), Inches(5.6), W - Inches(1), Inches(0.55),
    font_size=11, colour=LGRAY, italic=True)

add_textbox(sl,
    "⚠  The 3.33 pp gain is within the margin of error for n=300 (~±5.7 pp at 95% CI). "
    "See Limitations slide.",
    Inches(0.5), Inches(6.2), W - Inches(1), Inches(0.55),
    font_size=11, colour=GOLD, italic=True)


# ═══════════════════════════════════════════════════════════════
# Slide 14 — Retrieval & Groundedness Analysis
# ═══════════════════════════════════════════════════════════════
sl = blank_slide(prs)
set_bg(sl)
slide_header(sl,
    "ANALYSIS",
    "Retrieval Quality & Groundedness",
    "Both metrics are keyword/lexical proxies — not human relevance judgments or semantic faithfulness scores.")

# Retrieval box
ret_box = sl.shapes.add_shape(1, Inches(0.4), Inches(1.75), Inches(5.8), Inches(2.7))
ret_box.fill.solid(); ret_box.fill.fore_color.rgb = RGBColor(0x14, 0x2A, 0x40)
ret_box.line.color.rgb = ACCENT

add_textbox(sl, "Retrieval Quality (Hit@k, Precision@k)",
            Inches(0.55), Inches(1.82), Inches(5.5), Inches(0.35),
            font_size=13, bold=True, colour=ACCENT)

ret_body = (
    "Relevant = chunk contains key terms from correct answer text\n"
    "(lowercase, punctuation removed, stopwords excluded)\n\n"
    "  Hit@1   = 0.39    Precision@1 = 0.39\n"
    "  Hit@3   = 0.59    Precision@3 = 0.39\n"
    "  Hit@5   = 0.71    Precision@5 = 0.39\n\n"
    "Hit@k rises with k (39%→71%): more passages = better recall.\n"
    "Precision stays flat: most questions have 0 or 1 keyword-relevant chunk."
)
add_textbox(sl, ret_body, Inches(0.55), Inches(2.18), Inches(5.5), Inches(2.2),
            font_size=12, colour=WHITE)

# Groundedness box
gnd_box = sl.shapes.add_shape(1, Inches(6.4), Inches(1.75), Inches(6.4), Inches(2.7))
gnd_box.fill.solid(); gnd_box.fill.fore_color.rgb = RGBColor(0x14, 0x2A, 0x40)
gnd_box.line.color.rgb = ACCENT

add_textbox(sl, "Groundedness (Lexical Overlap Proxy)",
            Inches(6.55), Inches(1.82), Inches(6.1), Inches(0.35),
            font_size=13, bold=True, colour=ACCENT)

gnd_body = (
    "A sentence is grounded if ≥50% of its content words\n"
    "appear in the concatenated top-5 retrieved chunks.\n\n"
    "  All 300 answers:       0.64 avg grounded fraction\n"
    "  Correct answers:       0.67\n"
    "  Incorrect answers:     0.72\n\n"
    "Incorrect answers are MORE lexically grounded — the model\n"
    "faithfully copies language from off-target retrieved chunks."
)
add_textbox(sl, gnd_body, Inches(6.55), Inches(2.18), Inches(6.1), Inches(2.2),
            font_size=12, colour=WHITE)

add_textbox(sl,
    "Key finding: The retriever is casting a wide net (Hit@5=71%), but precision is low and "
    "groundedness does not separate correct from incorrect — the model uses context regardless of its relevance.",
    Inches(0.4), Inches(4.6), W - Inches(0.8), Inches(0.55),
    font_size=12, colour=GOLD, italic=True)


# ═══════════════════════════════════════════════════════════════
# Slide 15 — Error Analysis (RAG v2)
# ═══════════════════════════════════════════════════════════════
sl = blank_slide(prs)
set_bg(sl)
slide_header(sl,
    "ERROR ANALYSIS",
    "RAG v2 — Error Buckets (144 errors / 300 questions)",
    "Same bucketing rules applied to both RAG v1 and RAG v2 for comparability.")

# Bucket boxes
buckets_v2 = [
    ("Parse\nFailure", "0", "0.0%", GREEN,
     "RAG v2 forced-choice prompt\neliminates all abstention."),
    ("Retrieval\nMiss", "49", "34.0%",  GOLD,
     "No top-5 chunk contained\nkey terms from correct answer.\nRetriever limitation."),
    ("Model Ignored\nContext", "95", "66.0%", RED,
     "Relevant chunk was retrieved\nbut model still answered wrong.\nPrimary error mode."),
    ("Other", "0", "0.0%", LGRAY,
     "No ambiguous cases —\nall errors cleanly categorised."),
]

col_w = Inches(2.9)
col_h = Inches(2.8)
top = Inches(1.75)
for i, (label, count, pct, col, note) in enumerate(buckets_v2):
    left = Inches(0.35) + i * (col_w + Inches(0.15))
    box = sl.shapes.add_shape(1, left, top, col_w, col_h)
    box.fill.solid(); box.fill.fore_color.rgb = RGBColor(0x14, 0x2A, 0x40)
    box.line.color.rgb = col

    add_textbox(sl, label, left + Inches(0.1), top + Inches(0.08),
                col_w - Inches(0.2), Inches(0.4),
                font_size=12, bold=True, colour=col)
    add_textbox(sl, count, left + Inches(0.1), top + Inches(0.5),
                col_w - Inches(0.2), Inches(0.55),
                font_size=32, bold=True, colour=col, align=PP_ALIGN.CENTER)
    add_textbox(sl, f"of errors: {pct}", left + Inches(0.1), top + Inches(1.08),
                col_w - Inches(0.2), Inches(0.3),
                font_size=11, colour=LGRAY, align=PP_ALIGN.CENTER)
    add_textbox(sl, note, left + Inches(0.1), top + Inches(1.45),
                col_w - Inches(0.2), Inches(1.2),
                font_size=11, colour=WHITE)

# RAG v1 comparison
v1_compare = (
    "RAG v1 error buckets (172 errors):   Parse failure=61 (35.5%)  |  Retrieval miss=36 (20.9%)  |  Model ignored context=75 (43.6%)\n"
    "RAG v2 improvement:  Parse failures eliminated entirely.  Retrieval misses up slightly (more questions now parsed → more exposed).  "
    "Model-ignored-context remains the dominant failure — the key direction for future work."
)
add_textbox(sl, v1_compare,
            Inches(0.4), Inches(4.7), W - Inches(0.8), Inches(0.75),
            font_size=11, colour=LGRAY, italic=True)


# ═══════════════════════════════════════════════════════════════
# Slide 16 — Limitations
# ═══════════════════════════════════════════════════════════════
sl = blank_slide(prs)
set_bg(sl)
slide_header(sl,
    "LIMITATIONS",
    "Honest Caveats",
    "Presented transparently — these boundaries define where the results can and cannot be generalized.")

limitations = [
    ("Statistical margin of error",
     "The 3.33 pp gain of RAG v2 over baseline is within the margin of error for n=300 "
     "(±5.7 pp at 95% CI using a two-proportion z-test). "
     "A larger sample is needed before claiming a statistically significant improvement."),
    ("Forced-choice prompt confound",
     "Part of RAG v2's gain may come from the forced-choice prompt itself — not from retrieval. "
     "A fair no-context forced-choice control would isolate the prompt effect. "
     "This experiment was not run."),
    ("Groundedness is a lexical proxy",
     "Groundedness scores measure keyword overlap between generated text and retrieved chunks. "
     "They do NOT measure semantic faithfulness, factual correctness, or clinical safety. "
     "Incorrect answers scored 0.72 — higher than correct ones (0.67) — showing the proxy does not separate quality."),
    ("Retrieval metrics are keyword-based",
     "Hit@k and Precision@k measure whether key terms from the correct answer appear in retrieved text. "
     "This is NOT human relevance judgment. A chunk can score as relevant by term-matching "
     "without providing the reasoning needed to answer the question."),
]

top_y = Inches(1.75)
box_h = Inches(1.15)
gap = Inches(0.1)

for i, (title, body) in enumerate(limitations):
    left = Inches(0.4)
    top = top_y + i * (box_h + gap)
    box = sl.shapes.add_shape(1, left, top, W - Inches(0.8), box_h)
    box.fill.solid(); box.fill.fore_color.rgb = RGBColor(0x14, 0x2A, 0x40)
    box.line.color.rgb = GOLD

    add_textbox(sl, f"⚠  {title}",
                left + Inches(0.1), top + Inches(0.07),
                W - Inches(1.1), Inches(0.3),
                font_size=13, bold=True, colour=GOLD)
    add_textbox(sl, body,
                left + Inches(0.1), top + Inches(0.38),
                W - Inches(1.1), box_h - Inches(0.45),
                font_size=11, colour=WHITE)


# ═══════════════════════════════════════════════════════════════
# Slide 17 — Conclusion
# ═══════════════════════════════════════════════════════════════
sl = blank_slide(prs)
set_bg(sl)
slide_header(sl,
    "CONCLUSION",
    "Summary & Future Directions",
    "End-to-end RAG pipeline with Llama 3, evaluated on MedQA (USMLE), 300-question test set.")

conclusions = [
    ("✅  End-to-end RAG pipeline built and verified",
     "Llama 3 + FAISS retrieval over 36,723 textbook chunks. All phases run locally, CPU-only, "
     "with full reproducibility (fixed seeds, resumable evaluation)."),
    ("✅  Prompt engineering matters",
     "RAG v1's hedging prompt caused 20.3% abstention and masked a 53.6% parsed accuracy. "
     "RAG v2's forced-choice prompt eliminated abstention and raised overall accuracy to 52.0% (+3.33 pp over baseline)."),
    ("✅  Retrieval reaches relevant content 71% of the time",
     "Hit@5 = 0.71 — for 71% of questions, at least one of the top-5 chunks contains a key term from the correct answer. "
     "66% of remaining errors are 'model ignored context' — the generator does not exploit what the retriever found."),
    ("🔭  Primary direction for future work",
     "Reduce 'model ignored context' errors (66% of all v2 errors) via re-ranking, context compression, "
     "or fine-tuning the generator to better exploit retrieved evidence."),
]

top_y = Inches(1.75)
box_h = Inches(1.1)
gap = Inches(0.08)

for i, (title, body) in enumerate(conclusions):
    left = Inches(0.4)
    top = top_y + i * (box_h + gap)
    box = sl.shapes.add_shape(1, left, top, W - Inches(0.8), box_h)
    box.fill.solid(); box.fill.fore_color.rgb = RGBColor(0x14, 0x2A, 0x40)
    box.line.color.rgb = ACCENT if i < 3 else GOLD

    add_textbox(sl, title,
                left + Inches(0.1), top + Inches(0.07),
                W - Inches(1.1), Inches(0.3),
                font_size=13, bold=True, colour=ACCENT if i < 3 else GOLD)
    add_textbox(sl, body,
                left + Inches(0.1), top + Inches(0.38),
                W - Inches(1.1), box_h - Inches(0.45),
                font_size=11, colour=WHITE)


# ── Save ─────────────────────────────────────────────────────
prs.save(DST)
print(f"Saved: {DST}")
print(f"Total slides: {len(prs.slides)}")
