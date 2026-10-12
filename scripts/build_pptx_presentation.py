#!/usr/bin/env python3
"""
build_pptx_presentation.py
Generates the authoritative, publication-grade PowerPoint presentation (.pptx)
for PharmaPath: A Multi-Omics Biological Database for Network Pharmacology.

Follows the mandatory topic sequence:
1. Abstract
2. Intro
3. Literature review
4. Methodology
5. Analysis
6. Discussion
7. Conclusion
8. References

Includes real high-resolution screenshots from the live platform, custom dark obsidian
glassmorphic theme styling, 16:9 widescreen layout, and extensive oral defense speaker notes.
"""

import os
import shutil
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ==============================================================================
# THEME PALETTE (Dark Obsidian Glassmorphic)
# ==============================================================================
COLOR_BG = RGBColor(7, 9, 14)          # Obsidian background #07090e
COLOR_CARD_BG = RGBColor(14, 18, 28)   # Glass card background #0e121c
COLOR_CARD_BORDER = RGBColor(38, 48, 68) # Card subtle border #263044
COLOR_CONTAINER_BG = RGBColor(4, 6, 10)# Container background #04060a

COLOR_ORANGE = RGBColor(255, 128, 0)   # Primary brand #ff8000
COLOR_ORANGE_LIGHT = RGBColor(255, 166, 77) # #ffa64d
COLOR_CYAN = RGBColor(0, 210, 255)     # Secondary accent #00d2ff
COLOR_GREEN = RGBColor(16, 185, 129)   # Pass/success green #10b981
COLOR_RED = RGBColor(239, 68, 68)      # Warning/fail red #ef4444
COLOR_PURPLE = RGBColor(168, 85, 247)  # AI/GNN purple #a855f7

COLOR_TEXT_PRIMARY = RGBColor(255, 255, 255)
COLOR_TEXT_BODY = RGBColor(209, 213, 219)
COLOR_TEXT_MUTED = RGBColor(156, 163, 175)

FONT_HEADING = "Arial"
FONT_BODY = "Arial"
FONT_MONO = "Courier New"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "reports", "ppt_assets")
CROPS_DIR = os.path.join(ASSETS_DIR, "crops")
OUTPUT_PPTX_REPORTS = os.path.join(BASE_DIR, "reports", "PharmaPath_Final_Presentation.pptx")
OUTPUT_PPTX_ROOT = os.path.join(BASE_DIR, "PharmaPath_Final_Presentation.pptx")


def set_slide_background(slide):
    """Fills slide background with dark obsidian color."""
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5)
    )
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = COLOR_BG
    bg_shape.line.fill.background()
    return bg_shape


def add_header(slide, topic_num_text, topic_title, slide_title_lead, slide_title_highlight, subtitle_text):
    """Adds a standard structured header with topic badge, title with accent, and subtitle."""
    # Top bar badge (Topic Pill)
    pill = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.42), Inches(3.6), Inches(0.32)
    )
    pill.fill.solid()
    pill.fill.fore_color.rgb = RGBColor(28, 22, 14)
    pill.line.color.rgb = COLOR_ORANGE
    pill.line.width = Pt(1)
    tf_pill = pill.text_frame
    tf_pill.word_wrap = False
    tf_pill.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_pill = tf_pill.paragraphs[0]
    p_pill.text = f"{topic_title.upper()}"
    p_pill.font.name = FONT_HEADING
    p_pill.font.size = Pt(9.5)
    p_pill.font.bold = True
    p_pill.font.color.rgb = COLOR_ORANGE_LIGHT
    p_pill.alignment = PP_ALIGN.CENTER

    # Right branding badge
    brand = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.5), Inches(0.42), Inches(2.03), Inches(0.32)
    )
    brand.fill.solid()
    brand.fill.fore_color.rgb = RGBColor(16, 24, 38)
    brand.line.color.rgb = COLOR_CYAN
    brand.line.width = Pt(1)
    tf_brand = brand.text_frame
    tf_brand.word_wrap = False
    tf_brand.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_brand = tf_brand.paragraphs[0]
    p_brand.text = f"PHARMAPATH · {topic_num_text}"
    p_brand.font.name = FONT_HEADING
    p_brand.font.size = Pt(9.5)
    p_brand.font.bold = True
    p_brand.font.color.rgb = COLOR_CYAN
    p_brand.alignment = PP_ALIGN.CENTER

    # Main Slide Title
    tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.78), Inches(11.7), Inches(0.65))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    
    run_lead = p_title.add_run()
    run_lead.text = slide_title_lead + " "
    run_lead.font.name = FONT_HEADING
    run_lead.font.size = Pt(24)
    run_lead.font.bold = True
    run_lead.font.color.rgb = COLOR_TEXT_PRIMARY

    run_hl = p_title.add_run()
    run_hl.text = slide_title_highlight
    run_hl.font.name = FONT_HEADING
    run_hl.font.size = Pt(24)
    run_hl.font.bold = True
    run_hl.font.color.rgb = COLOR_ORANGE

    # Subtitle
    tb_sub = slide.shapes.add_textbox(Inches(0.8), Inches(1.36), Inches(11.7), Inches(0.35))
    tf_sub = tb_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_top = tf_sub.margin_right = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = subtitle_text
    p_sub.font.name = FONT_BODY
    p_sub.font.size = Pt(12)
    p_sub.font.color.rgb = COLOR_TEXT_MUTED


def add_footer(slide, topic_name):
    """Adds standard footer to slide."""
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(7.08), Inches(11.73), Inches(0.25))
    tf = tb.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = f"PharmaPath: Multi-Omics Biological Database for Network Pharmacology  |  Topic: {topic_name}  |  https://pharmapath-website.vercel.app"
    p.font.name = FONT_BODY
    p.font.size = Pt(9)
    p.font.color.rgb = RGBColor(100, 110, 125)


def add_screenshot_frame(slide, image_path, top_title, caption_text, badge_text="LIVE SYSTEM", left=Inches(6.8), top=Inches(1.85), width=Inches(5.73), height=Inches(5.0)):
    """Creates a macOS-style screenshot frame with dark header, image, and caption bar."""
    # Outer frame
    frame = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    frame.fill.solid()
    frame.fill.fore_color.rgb = COLOR_CONTAINER_BG
    frame.line.color.rgb = COLOR_CARD_BORDER
    frame.line.width = Pt(1)

    # Frame header
    header_height = Inches(0.35)
    f_header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, header_height)
    f_header.fill.solid()
    f_header.fill.fore_color.rgb = RGBColor(18, 24, 38)
    f_header.line.fill.background()
    tf_h = f_header.text_frame
    tf_h.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_h.margin_left = Inches(0.15)
    p_h = tf_h.paragraphs[0]
    p_h.text = f"● ● ●   {top_title}"
    p_h.font.name = FONT_HEADING
    p_h.font.size = Pt(9.5)
    p_h.font.color.rgb = COLOR_TEXT_MUTED

    # Caption footer
    caption_height = Inches(0.38)
    caption_top = top + height - caption_height
    f_cap = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, caption_top, width, caption_height)
    f_cap.fill.solid()
    f_cap.fill.fore_color.rgb = RGBColor(12, 16, 26)
    f_cap.line.color.rgb = COLOR_CARD_BORDER
    f_cap.line.width = Pt(0.75)
    tf_c = f_cap.text_frame
    tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_c.margin_left = Inches(0.15)
    p_c = tf_c.paragraphs[0]
    p_c.text = caption_text
    p_c.font.name = FONT_BODY
    p_c.font.size = Pt(9.5)
    p_c.font.bold = True
    p_c.font.color.rgb = COLOR_ORANGE_LIGHT

    # Real Screenshot Image
    img_top = top + header_height
    img_height = height - header_height - caption_height
    if os.path.exists(image_path):
        slide.shapes.add_picture(image_path, left + Inches(0.05), img_top + Inches(0.05), width - Inches(0.1), img_height - Inches(0.1))
    else:
        # Fallback placeholder if missing
        ph = slide.shapes.add_textbox(left, img_top, width, img_height)
        ph.text_frame.text = f"Image Not Found: {os.path.basename(image_path)}"


def add_notes(slide, notes_content):
    """Attaches complete oral presentation script and viva defense context to the slide notes."""
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = notes_content.strip()


def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # Blank slide layout

    print("Building slide deck...")

    # ==========================================================================
    # SLIDE 0: TITLE SLIDE
    # ==========================================================================
    s0 = prs.slides.add_slide(blank_layout)
    set_slide_background(s0)

    # Hero Badge
    hero_badge = s0.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.1), Inches(6.0), Inches(0.38))
    hero_badge.fill.solid()
    hero_badge.fill.fore_color.rgb = RGBColor(28, 22, 14)
    hero_badge.line.color.rgb = COLOR_ORANGE
    hero_badge.line.width = Pt(1.5)
    tf_hb = hero_badge.text_frame
    tf_hb.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_hb = tf_hb.paragraphs[0]
    p_hb.text = "PHARMAPATH · MULTI-OMICS BIOLOGICAL DATABASE DEFENSE"
    p_hb.font.name = FONT_HEADING
    p_hb.font.size = Pt(10)
    p_hb.font.bold = True
    p_hb.font.color.rgb = COLOR_ORANGE_LIGHT
    p_hb.alignment = PP_ALIGN.CENTER

    # Main Title
    tb_t0 = s0.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(11.3), Inches(1.5))
    tf_t0 = tb_t0.text_frame
    tf_t0.word_wrap = True
    p_t0 = tf_t0.paragraphs[0]
    p_t0.text = "PharmaPath: A Multi-Omics Biological Database for Network Pharmacology"
    p_t0.font.name = FONT_HEADING
    p_t0.font.size = Pt(36)
    p_t0.font.bold = True
    p_t0.font.color.rgb = COLOR_TEXT_PRIMARY

    p_t0_sub = tf_t0.add_paragraph()
    p_t0_sub.text = "Computational Discovery Across the Human Interactome Using Metformin, Imatinib, Disease Modules, and Inductive Graph Learning"
    p_t0_sub.font.name = FONT_BODY
    p_t0_sub.font.size = Pt(16)
    p_t0_sub.font.color.rgb = COLOR_TEXT_MUTED
    p_t0_sub.space_before = Pt(10)

    # Database Pipeline Strip
    pipe_strip = s0.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(3.45), Inches(11.33), Inches(0.65))
    pipe_strip.fill.solid()
    pipe_strip.fill.fore_color.rgb = COLOR_CARD_BG
    pipe_strip.line.color.rgb = COLOR_CARD_BORDER
    tf_ps = pipe_strip.text_frame
    tf_ps.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_ps = tf_ps.paragraphs[0]
    p_ps.text = "🧬 Integrated Database Pipeline: STRING v12 · ChEMBL 33 · LINCS L1000 · Open Targets · KEGG 2021 · Reactome 2022 · PyTorch Geometric"
    p_ps.font.name = FONT_HEADING
    p_ps.font.size = Pt(11)
    p_ps.font.bold = True
    p_ps.font.color.rgb = COLOR_CYAN

    # 4 Key Metrics Cards
    metrics = [
        ("15,882", "HUMAN PROTEINS (98.03% LCC)", COLOR_ORANGE),
        ("236,712", "STRING V12 HIGH-CONFIDENCE EDGES", COLOR_CYAN),
        ("0.8865", "GRAPHSAGE TEST AUROC (INDUCTIVE)", COLOR_GREEN),
        ("-18.28", "METFORMIN → T2D PROXIMITY Z-SCORE", COLOR_ORANGE_LIGHT)
    ]
    card_w = Inches(2.65)
    card_gap = Inches(0.24)
    card_top = Inches(4.35)
    card_h = Inches(1.4)
    for i, (val, lbl, col) in enumerate(metrics):
        cx = Inches(1.0) + i * (card_w + card_gap)
        c_shape = s0.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, card_top, card_w, card_h)
        c_shape.fill.solid()
        c_shape.fill.fore_color.rgb = COLOR_CARD_BG
        c_shape.line.color.rgb = COLOR_CARD_BORDER
        tf_c = c_shape.text_frame
        tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_val = tf_c.paragraphs[0]
        p_val.text = val
        p_val.font.name = FONT_HEADING
        p_val.font.size = Pt(28)
        p_val.font.bold = True
        p_val.font.color.rgb = col
        p_val.alignment = PP_ALIGN.CENTER
        p_lbl = tf_c.add_paragraph()
        p_lbl.text = lbl
        p_lbl.font.name = FONT_HEADING
        p_lbl.font.size = Pt(8.5)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = COLOR_TEXT_MUTED
        p_lbl.alignment = PP_ALIGN.CENTER

    # Presenter Information / Footer
    tb_pres = s0.shapes.add_textbox(Inches(1.0), Inches(6.15), Inches(11.33), Inches(0.75))
    tf_pres = tb_pres.text_frame
    p_p1 = tf_pres.paragraphs[0]
    p_p1.text = "Senior Bioinformatics & Machine Learning Engineering  |  Biological Database Capstone Examination Defense"
    p_p1.font.name = FONT_HEADING
    p_p1.font.size = Pt(11)
    p_p1.font.bold = True
    p_p1.font.color.rgb = COLOR_TEXT_PRIMARY

    p_p2 = tf_pres.add_paragraph()
    p_p2.text = "Reproducible Master Pipeline: python scripts/run_all.py  |  Live Platform: https://pharmapath-website.vercel.app  |  Automated PyTest Suite (100% Passed)"
    p_p2.font.name = FONT_BODY
    p_p2.font.size = Pt(9.5)
    p_p2.font.color.rgb = COLOR_TEXT_MUTED

    add_notes(s0, """ORAL PRESENTATION SCRIPT - TITLE SLIDE:
Good morning, respected members of the examination committee and faculty. Today, I am proud to present PharmaPath: A Multi-Omics Biological Database for Network Pharmacology.
In contemporary translational pharmacology, complex systemic diseases such as Type 2 Diabetes and Chronic Myeloid Leukemia do not arise from isolated genetic lesions. Instead, they emerge from the systemic disruption of protein-protein communication networks across the human interactome.
PharmaPath connects physical protein-protein interaction networks from STRING v12 with curated pharmacology from ChEMBL, transcriptomic perturbations from LINCS L1000, and human disease genetics from Open Targets.
By deploying diffusion models, degree-matched null permutation tests, and leakage-safe inductive Graph Neural Networks, PharmaPath provides an end-to-end biological database standard that translates multi-omics big data into testable pharmacological hypotheses.
Throughout today's defense, all quantitative findings presented are directly corroborated by live screenshots from our deployed, interactive web discovery platform.""")

    # ==========================================================================
    # SLIDE 1: ABSTRACT (Topic 1 / 8)
    # ==========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    add_header(s1, "TOPIC 1 / 8", "Abstract · Executive Summary", "Drug Action as a", "Network Perturbation", "Connecting physical human interactomes, disease genetics, and inductive AI into a discovery database")

    # Left Card
    c1 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c1.fill.solid()
    c1.fill.fore_color.rgb = COLOR_CARD_BG
    c1.line.color.rgb = COLOR_ORANGE
    c1.line.width = Pt(1.5)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = Inches(0.25)

    p1 = tf1.paragraphs[0]
    p1.text = "Executive Summary & Research Paradigm"
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(15)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_TEXT_PRIMARY

    p1_desc = tf1.add_paragraph()
    p1_desc.text = "Complex human diseases do not emerge from isolated genetic lesions; they arise from perturbed multi-protein communication cascades across the interactome. PharmaPath establishes an end-to-end biological database connecting multi-omics evidence layers to evaluate drug mechanism, disease module localization, and target recovery."
    p1_desc.font.name = FONT_BODY
    p1_desc.font.size = Pt(10.5)
    p1_desc.font.color.rgb = COLOR_TEXT_BODY
    p1_desc.space_before = Pt(6)

    bullets_s1 = [
        ("Contrasting Modalities:", " Evaluates pleiotropic metabolic regulation (Metformin in T2D) vs. precision oncogenic kinase inhibition (Imatinib in CML)."),
        ("Statistical Rigor:", " 1,000 degree-matched null permutations verify that drug-disease proximity reflects authentic biological localization (z = -18.28, p = 0.001)."),
        ("Leakage-Safe GNN:", " Inductive GraphSAGE achieves 0.8865 AUROC and recovers held-out targets without topological edge leakage."),
        ("Interactive Discovery:", " Zero-latency browser studio delivering 6 integrated analytical views with automated PyTest verification.")
    ]
    for b_title, b_text in bullets_s1:
        p_b = tf1.add_paragraph()
        p_b.space_before = Pt(6)
        r_bt = p_b.add_run()
        r_bt.text = "• " + b_title
        r_bt.font.name = FONT_HEADING
        r_bt.font.size = Pt(10)
        r_bt.font.bold = True
        r_bt.font.color.rgb = COLOR_ORANGE_LIGHT
        r_txt = p_b.add_run()
        r_txt.text = b_text
        r_txt.font.name = FONT_BODY
        r_txt.font.size = Pt(9.5)
        r_txt.font.color.rgb = COLOR_TEXT_BODY

    # Math callout
    p_math = tf1.add_paragraph()
    p_math.space_before = Pt(10)
    r_m = p_math.add_run()
    r_m.text = "Closest Distance Metric: ⟨dc(T, S)⟩ = (1/|T|) ∑ min d(t, s) [Guney et al. 2016]"
    r_m.font.name = FONT_MONO
    r_m.font.size = Pt(9)
    r_m.font.bold = True
    r_m.font.color.rgb = COLOR_CYAN

    # Right Screenshot: 01_subnetwork_metformin.png
    add_screenshot_frame(s1, os.path.join(ASSETS_DIR, "01_subnetwork_metformin.png"), "PharmaPath Live Discovery Lab — Subnetwork Canvas", "Real Platform View: 150-Node Metformin RWR Subnetwork (Density = 0.4377, 61 Seed Targets)", "LIVE SYSTEM")
    add_footer(s1, "Abstract")

    add_notes(s1, """ORAL PRESENTATION SCRIPT - ABSTRACT:
To begin with our Abstract:
PharmaPath addresses the fundamental limitation of traditional reductionist pharmacology. When a drug molecule enters a cellular environment, its therapeutic efficacy is determined not merely by binding its primary protein target, but by how the perturbation propagates through interconnected signaling pathways.
In this work, we contrast two distinct pharmacological archetypes:
1. Metformin, a pleiotropic metabolic agent with 61 primary targets across Mitochondrial Complex I and AMPK.
2. Imatinib, a precision targeted tyrosine kinase inhibitor with 10 direct targets including BCR-ABL, KIT, and PDGF receptors.
Using STRING v12's high-confidence physical interactome of 15,882 proteins and 236,712 interactions, we demonstrate that Random Walk with Restart enriches functional density by up to 2.5-fold over naive topological neighborhoods.
Crucially, using 1,000 degree-matched null permutations, we establish that drug-disease proximity is statistically authentic (z = -18.28 for Metformin to Type 2 Diabetes; z = -7.25 for Imatinib to CML), while reciprocal negative controls decisively fail.
On the right, you can see the live interactive subnetwork canvas from our platform, rendering Metformin's 150-node subnetwork with force-directed physics.""")

    # ==========================================================================
    # SLIDE 2: INTRODUCTION (Topic 2 / 8)
    # ==========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "TOPIC 2 / 8", "Introduction · The Problem & Archetypes", "Beyond the", "Single-Target Myth", "Why complex diseases require systemic network-level pharmacological modeling")

    # Left Container
    c2 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c2.fill.solid()
    c2.fill.fore_color.rgb = COLOR_CARD_BG
    c2.line.color.rgb = COLOR_CARD_BORDER
    tf2 = c2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = tf2.margin_top = tf2.margin_bottom = Inches(0.22)

    p2 = tf2.paragraphs[0]
    p2.text = "The Single-Target Bottleneck in Modern Pharmacology"
    p2.font.name = FONT_HEADING
    p2.font.size = Pt(14)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_TEXT_PRIMARY

    p2_desc = tf2.add_paragraph()
    p2_desc.text = "Traditional drug discovery relies on the 'one-drug, one-target, one-disease' paradigm. However, clinical attrition remains >90% because complex disorders emerge from robust, redundant network states that rapidly rewire around single molecular blocks."
    p2_desc.font.name = FONT_BODY
    p2_desc.font.size = Pt(10)
    p2_desc.font.color.rgb = COLOR_TEXT_BODY
    p2_desc.space_before = Pt(4)

    # Sub-cards for the two archetypes
    p2_met = tf2.add_paragraph()
    p2_met.text = "ARCHETYPE A: METFORMIN (T2D) — Pleiotropic Metabolic Regulator"
    p2_met.font.name = FONT_HEADING
    p2_met.font.size = Pt(10.5)
    p2_met.font.bold = True
    p2_met.font.color.rgb = COLOR_ORANGE
    p2_met.space_before = Pt(8)

    p2_met_d = tf2.add_paragraph()
    p2_met_d.text = "• 61 direct targets in interactome LCC: Mitochondrial Complex I subunits (NDUFA/B/C/S) and AMPK heterotrimers (PRKAA1/2, PRKAB1, PRKAG1). Suppresses hepatic gluconeogenesis via cellular energetic stress."
    p2_met_d.font.name = FONT_BODY
    p2_met_d.font.size = Pt(9.5)
    p2_met_d.font.color.rgb = COLOR_TEXT_BODY

    p2_ima = tf2.add_paragraph()
    p2_ima.text = "ARCHETYPE B: IMATINIB (CML) — Precision Kinase Inhibitor"
    p2_ima.font.name = FONT_HEADING
    p2_ima.font.size = Pt(10.5)
    p2_ima.font.bold = True
    p2_ima.font.color.rgb = COLOR_CYAN
    p2_ima.space_before = Pt(8)

    p2_ima_d = tf2.add_paragraph()
    p2_ima_d.text = "• 10 direct targets in interactome LCC: Competitively blocks ATP binding pocket of BCR-ABL1 fusion oncogene, KIT, PDGFRA/B, and CSF1R. Suppresses leukemic myeloblast proliferation with high molecular specificity."
    p2_ima_d.font.name = FONT_BODY
    p2_ima_d.font.size = Pt(9.5)
    p2_ima_d.font.color.rgb = COLOR_TEXT_BODY

    p2_q = tf2.add_paragraph()
    p2_q.text = "The 4 Core Research Questions:"
    p2_q.font.name = FONT_HEADING
    p2_q.font.size = Pt(10.5)
    p2_q.font.bold = True
    p2_q.font.color.rgb = COLOR_TEXT_PRIMARY
    p2_q.space_before = Pt(8)

    p2_ql = tf2.add_paragraph()
    p2_ql.text = "1. Subnetwork Perturbation: What topological modules do drugs diffuse across?\n2. Disease Proximity: Are drug targets closer to disease modules than random expectation?\n3. Network Bottlenecks: Which critical hubs control interactome flux and cross-talk?\n4. Inductive GNN Reach: Can graph machine learning predict novel links without data leakage?"
    p2_ql.font.name = FONT_BODY
    p2_ql.font.size = Pt(9)
    p2_ql.font.color.rgb = COLOR_TEXT_MUTED

    # Right Screenshot: 02_subnetwork_imatinib.png
    add_screenshot_frame(s2, os.path.join(ASSETS_DIR, "02_subnetwork_imatinib.png"), "PharmaPath Real Platform — Imatinib Kinase Network", "Real Platform View: 150-Node Imatinib Kinase Subnetwork (Density = 0.2464, 10 Seed Targets)", "CONFIG-DRIVEN")
    add_footer(s2, "Introduction")

    add_notes(s2, """ORAL PRESENTATION SCRIPT - INTRODUCTION:
Moving to the Introduction:
For decades, the pharmaceutical industry operated under the premise of Paul Ehrlich's 'magic bullet'—designing hyper-selective molecules for single isolated receptors. Yet over 90% of clinical drug candidates fail in Phase II and III trials due to unexpected off-target toxicities or lack of efficacy.
The reason is biological redundancy. Complex polygenic diseases rewiring cellular networks circumvent single-node blockades.
To evaluate this paradigm systematically, PharmaPath selects two archetypal clinical therapies:
Metformin represents pleiotropic systemic regulation. It exerts therapeutic efficacy through 61 interactome targets, primarily the 45 subunits of Mitochondrial Complex I and the heterotrimeric complexes of AMP-activated protein kinase (AMPK).
In stark contrast, Imatinib represents the pinnacle of precision oncology. It was engineered to target the constitutively active BCR-ABL1 tyrosine kinase in Chronic Myeloid Leukemia, alongside a focused set of related receptor tyrosine kinases such as KIT, PDGFRA, and PDGFRB.
On the right, our live platform visualizes the Imatinib subnetwork, highlighting its 10 seed targets and immediate downstream cascade.""")

    # ==========================================================================
    # SLIDE 3: LITERATURE REVIEW (Topic 3 / 8)
    # ==========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "TOPIC 3 / 8", "Literature Review · Systems Pharmacology Foundations", "From Reductionism to", "Systems Medicine", "Connecting empirical biological databases with mathematical network medicine theory")

    # Left Card
    c3 = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c3.fill.solid()
    c3.fill.fore_color.rgb = COLOR_CARD_BG
    c3.line.color.rgb = COLOR_CARD_BORDER
    tf3 = c3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_right = tf3.margin_top = tf3.margin_bottom = Inches(0.22)

    p3 = tf3.paragraphs[0]
    p3.text = "Key Scientific Foundations & Conceptual Anchors"
    p3.font.name = FONT_HEADING
    p3.font.size = Pt(14)
    p3.font.bold = True
    p3.font.color.rgb = COLOR_TEXT_PRIMARY

    lit_items = [
        ("Barabási et al. (2011 Nature Reviews Genetics):", " Established that the human interactome is scale-free and that disease-causing mutations cluster into topologically cohesive disease modules rather than distributing uniformly."),
        ("Guney et al. (2016 Nature Communications):", " Formulated the degree-matched closest-distance metric ⟨dc(T,S)⟩, proving that clinically efficacious drugs directly overlap or localize proximate to disease modules (z ≤ -2.0)."),
        ("Menche et al. (2015 Science):", " Derived the interactome module separation metric s_AB, establishing that distinct diseases and drug targets occupy separated topological spheres (s_AB > 0)."),
        ("Hamilton et al. (2017 NeurIPS):", " Formulated GraphSAGE inductive representation learning, enabling neighborhood aggregation on unseen interactome topologies without transductive data leakage.")
    ]
    for lit_title, lit_text in lit_items:
        p_l = tf3.add_paragraph()
        p_l.space_before = Pt(6)
        r_lt = p_l.add_run()
        r_lt.text = "• " + lit_title
        r_lt.font.name = FONT_HEADING
        r_lt.font.size = Pt(9.5)
        r_lt.font.bold = True
        r_lt.font.color.rgb = COLOR_ORANGE_LIGHT
        r_ltx = p_l.add_run()
        r_ltx.text = lit_text
        r_ltx.font.name = FONT_BODY
        r_ltx.font.size = Pt(9)
        r_ltx.font.color.rgb = COLOR_TEXT_BODY

    p3_db = tf3.add_paragraph()
    p3_db.text = "The Multi-Omics Biological Database Ecosystem:"
    p3_db.font.name = FONT_HEADING
    p3_db.font.size = Pt(10)
    p3_db.font.bold = True
    p3_db.font.color.rgb = COLOR_CYAN
    p3_db.space_before = Pt(8)

    p3_dbl = tf3.add_paragraph()
    p3_dbl.text = "• STRING v12 (Physical Scaffold ≥ 700)  • ChEMBL 33 (Curated Targets)\n• LINCS L1000 (Cellular z-scores)        • Open Targets Platform (Genetics)\n• KEGG 2021 & Reactome 2022 (Pathways) • PyTorch Geometric (Inductive AI)"
    p3_dbl.font.name = FONT_MONO
    p3_dbl.font.size = Pt(8.5)
    p3_dbl.font.color.rgb = COLOR_TEXT_MUTED

    # Right Screenshot: tight_protein_modal.png
    add_screenshot_frame(s3, os.path.join(CROPS_DIR, "tight_protein_modal.png"), "PharmaPath Real Platform — Multi-Omics Protein Inspector", "Live Inspector: Multi-Omics Integration (Degree, LINCS Perturbation z, Cluster, PubMed Bridge)", "PROGRAMMATIC API")
    add_footer(s3, "Literature Review")

    add_notes(s3, """ORAL PRESENTATION SCRIPT - LITERATURE REVIEW:
In our Literature Review, we anchor PharmaPath directly upon four foundational pillars of network medicine:
First, Albert-László Barabási's landmark 2011 Nature Reviews Genetics paper demonstrated that cellular networks exhibit scale-free topologies where disease-associated proteins coalesce into localized 'disease modules'.
Second, Emre Guney and colleagues in 2016 introduced the closest-distance metric ⟨dc⟩ in Nature Communications. They proved that a drug's therapeutic efficacy is mediated by its topological proximity to the disease module, and crucially emphasized that any proximity metric must be benchmarked against degree-matched random sets to eliminate degree bias.
Third, Jörg Menche et al. in Science 2015 formulated the interactome separation metric s_AB, quantifying module overlap.
Fourth, Will Hamilton's 2017 GraphSAGE framework provided the computational basis for inductive neighborhood sampling, avoiding the graph leakage that invalidates many transductive link prediction models.
On the right, our live protein modal inspector demonstrates how PharmaPath synthesizes these layers for each node—displaying degree, LINCS expression z-score, Louvain cluster, and dynamic PubMed verification links.""")

    # ==========================================================================
    # SLIDE 4: METHODOLOGY - PIPELINE (Topic 4 / 8)
    # ==========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "TOPIC 4 / 8", "Methodology · Computational Pipeline Architecture", "End-to-End", "Database-to-Discovery Flow", "Six-phase computational protocol ensuring zero data leakage and 100% provenance tracking")

    # Left Container
    c4 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c4.fill.solid()
    c4.fill.fore_color.rgb = COLOR_CARD_BG
    c4.line.color.rgb = COLOR_CARD_BORDER
    tf4 = c4.text_frame
    tf4.word_wrap = True
    tf4.margin_left = tf4.margin_right = tf4.margin_top = tf4.margin_bottom = Inches(0.2)

    phases = [
        ("PHASE 1: Interactome Scaffolding (0.0000% Loss)", "Ingest STRING v12 human interactome (combined_score ≥ 700). Map 19,699 ENSP IDs to HGNC symbols. Extract Largest Connected Component (15,882 nodes, 236,712 edges).", COLOR_ORANGE),
        ("PHASE 2: Dual Subnetwork Extraction (Diffusion)", "Extract 2-hop topological periphery (500 nodes) vs Random Walk with Restart (RWR, r=0.5, 150 nodes) to simulate steady-state network diffusion from seed targets.", COLOR_CYAN),
        ("PHASE 3: Multi-Omics Overlays & ORA (Sanity Passed)", "Overlay LINCS L1000 expression z-scores. Execute Fisher's exact over-representation analysis against KEGG 2021 and Reactome 2022 with Benjamini–Hochberg FDR < 0.05.", COLOR_GREEN),
        ("PHASE 4: Topology & Disease Proximity (1,000 Perms)", "Compute degree, betweenness, Louvain modularity clusters. Run Guney closest-distance test against 1,000 degree-matched null permutations.", COLOR_PURPLE),
        ("PHASE 5: Inductive GNN & Leave-Targets-Out (Zero Leakage)", "Split edges 80/10/10 with complete exclusion from message passing. Train GraphSAGE and GAE. Execute leave-targets-out recovery.", COLOR_RED)
    ]
    for p_title, p_desc, p_col in phases:
        p_hdr = tf4.add_paragraph() if tf4.paragraphs[0].text else tf4.paragraphs[0]
        p_hdr.space_before = Pt(4)
        r_ph = p_hdr.add_run()
        r_ph.text = p_title
        r_ph.font.name = FONT_HEADING
        r_ph.font.size = Pt(10)
        r_ph.font.bold = True
        r_ph.font.color.rgb = p_col
        p_d = tf4.add_paragraph()
        r_pd = p_d.add_run()
        r_pd.text = p_desc
        r_pd.font.name = FONT_BODY
        r_pd.font.size = Pt(8.5)
        r_pd.font.color.rgb = COLOR_TEXT_BODY

    # Right Screenshot: 04_pathways_metformin.png
    add_screenshot_frame(s4, os.path.join(ASSETS_DIR, "04_pathways_metformin.png"), "PharmaPath Real Platform — Biological Sanity Audit Engine", "Automated Verification: Recovering Hallmark Metabolic Cascades (OxPhos FDR = 1.26e-153)", "AUDIT VERIFIED")
    add_footer(s4, "Methodology")

    add_notes(s4, """ORAL PRESENTATION SCRIPT - METHODOLOGY (PIPELINE):
Turning to our Methodology and Data Engineering Protocol:
PharmaPath executes a strict six-phase computational pipeline managed by our master script run_all.py:
In Phase 1, we ingest the complete STRING v12 human physical interaction network, filtering strictly at combined_score ≥ 700 to ensure high-confidence physical binding. We map all Ensembl Protein IDs to standard HGNC gene symbols using a curated NCBI/HGNC dictionary, achieving a 0.0000% mapping loss rate on our drug targets. Extracting the Largest Connected Component yields 15,882 proteins and 236,712 edges.
In Phase 2, we contrast two extraction strategies: standard 2-hop graph extraction vs Random Walk with Restart with restart probability r=0.5.
In Phase 3, we overlay LINCS L1000 expression z-scores and conduct Fisher's exact test over-representation analysis against KEGG 2021 and Reactome 2022 libraries with Benjamini-Hochberg FDR correction.
In Phase 4, we evaluate centrality metrics and disease module proximity.
In Phase 5, we construct inductive Graph Neural Networks using PyTorch Geometric under strict train/val/test splits with zero edge leakage.
On the right, our platform's Biological Sanity Audit Engine demonstrates automated verification of hallmark metabolic cascades.""")

    # ==========================================================================
    # SLIDE 5: METHODOLOGY - INTERACTIVE LAB (Topic 4 / 8 Cont.)
    # ==========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "TOPIC 4 / 8 (CONT)", "Methodology · Interactive Software Engineering", "Interactive", "Discovery Lab Architecture", "Pre-computed multi-omics analytics served via a zero-latency client-side exploration canvas")

    # Left Container
    c5 = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c5.fill.solid()
    c5.fill.fore_color.rgb = COLOR_CARD_BG
    c5.line.color.rgb = COLOR_CARD_BORDER
    tf5 = c5.text_frame
    tf5.word_wrap = True
    tf5.margin_left = tf5.margin_right = tf5.margin_top = tf5.margin_bottom = Inches(0.22)

    p5 = tf5.paragraphs[0]
    p5.text = "Interactive Web Platform Engineering Highlights"
    p5.font.name = FONT_HEADING
    p5.font.size = Pt(14)
    p5.font.bold = True
    p5.font.color.rgb = COLOR_TEXT_PRIMARY

    p5_desc = tf5.add_paragraph()
    p5_desc.text = "To make high-throughput network pharmacology immediately accessible to wet-lab biologists and bioinformaticians, PharmaPath compiles high-performance graph analytics into lightweight JSON data structures served through a responsive modern interface."
    p5_desc.font.name = FONT_BODY
    p5_desc.font.size = Pt(10)
    p5_desc.font.color.rgb = COLOR_TEXT_BODY
    p5_desc.space_before = Pt(4)

    lab_highlights = [
        ("Vis-Network Physics Engine:", " Live force-directed layout with dynamic node sizing (Degree/Betweenness), threshold sliders, and real-time gene search."),
        ("Chart.js Visualizations:", " Interactive pathway horizontal bar charts, scatter plots with 4 topological quadrant tags, and null permutation histograms."),
        ("PubMed Cross-Linking:", " One-click verified bibliographic search for every predicted drug-protein candidate pair."),
        ("Zero-Latency Client-Side Delivery:", " Pre-computed JSON caches allow seamless offline operation and instant client-side filtering (<50ms)."),
        ("100% PyTest Automated Coverage:", " Strict unit and integration tests verify graph connectivity, metric bounds, and data consistency.")
    ]
    for lh_title, lh_text in lab_highlights:
        p_lh = tf5.add_paragraph()
        p_lh.space_before = Pt(5)
        r_lht = p_lh.add_run()
        r_lht.text = "• " + lh_title
        r_lht.font.name = FONT_HEADING
        r_lht.font.size = Pt(9.5)
        r_lht.font.bold = True
        r_lht.font.color.rgb = COLOR_ORANGE_LIGHT
        r_lhtx = p_lh.add_run()
        r_lhtx.text = lh_text
        r_lhtx.font.name = FONT_BODY
        r_lhtx.font.size = Pt(9)
        r_lhtx.font.color.rgb = COLOR_TEXT_BODY

    p5_cmd = tf5.add_paragraph()
    p5_cmd.text = "Deployment: python website/server.py -> http://localhost:8080 (or Vercel static build)"
    p5_cmd.font.name = FONT_MONO
    p5_cmd.font.size = Pt(8.5)
    p5_cmd.font.bold = True
    p5_cmd.font.color.rgb = COLOR_GREEN
    p5_cmd.space_before = Pt(8)

    # Right Screenshot: tight_centrality_studio.png
    add_screenshot_frame(s5, os.path.join(CROPS_DIR, "tight_centrality_studio.png"), "PharmaPath Real Platform — Centrality & Hubs Explorer", "Real Platform View: Degree vs. Betweenness Scatter, Louvain Clusters, & Dual Bridge Identification", "INTERACTIVE LAB")
    add_footer(s5, "Methodology")

    add_notes(s5, """ORAL PRESENTATION SCRIPT - METHODOLOGY (INTERACTIVE LAB):
Continuing our Methodology, let us focus on the Interactive Discovery Lab Architecture:
A major challenge in bioinformatics is that complex network pharmacology pipelines often remain trapped inside proprietary scripts or static Jupyter notebooks.
PharmaPath bridges this gap by providing a fully interactive web platform built with modern HTML5, Vis-Network, and Chart.js.
All heavy graph analytics, including Floyd-Warshall shortest paths, Louvain community detection, and PyTorch Geometric embeddings, are pre-computed and structured into optimized JSON data files.
As a result, the web application runs with sub-50-millisecond response times directly in the browser, requiring zero server-side computation during exploratory sessions.
On the right, you can see our Centrality & Hubs Explorer in action:
The interactive scatter plot categorizes proteins into four topological quadrants (Dual Bridges, Hubs, Bottlenecks, and Standard Nodes).
Beside it, our Louvain Modularity panel reports community clusters and dominant functional pathways, identifying critical dual bridges such as KIT, FLT3, and BCR.""")

    # ==========================================================================
    # SLIDE 6: ANALYSIS - DIFFUSION & DENSITY (Topic 5 / 8)
    # ==========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "TOPIC 5 / 8", "Analysis · Interactome Diffusion & Module Isolation", "Subnetwork Diffusion", "Enriches Functional Modules", "Comparing 2-hop topological periphery with Random Walk with Restart (RWR) concentration")

    # Left Container with Table
    c6 = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c6.fill.solid()
    c6.fill.fore_color.rgb = COLOR_CARD_BG
    c6.line.color.rgb = COLOR_CARD_BORDER
    tf6 = c6.text_frame
    tf6.word_wrap = True
    tf6.margin_left = tf6.margin_right = tf6.margin_top = tf6.margin_bottom = Inches(0.2)

    p6 = tf6.paragraphs[0]
    p6.text = "Quantitative Subnetwork Density Comparison"
    p6.font.name = FONT_HEADING
    p6.font.size = Pt(14)
    p6.font.bold = True
    p6.font.color.rgb = COLOR_TEXT_PRIMARY

    p6_desc = tf6.add_paragraph()
    p6_desc.text = "While 2-hop neighborhoods capture wide peripheral connectivity (500 nodes), Random Walk with Restart (RWR, r=0.5) concentrates densely connected functional complexes, filtering out peripheral interactome noise."
    p6_desc.font.name = FONT_BODY
    p6_desc.font.size = Pt(9.5)
    p6_desc.font.color.rgb = COLOR_TEXT_BODY
    p6_desc.space_before = Pt(4)

    # Mini Table in Slide
    table_shape = s6.shapes.add_table(5, 5, Inches(1.0), Inches(2.9), Inches(5.35), Inches(1.6))
    table = table_shape.table
    table.columns[0].width = Inches(1.85)
    table.columns[1].width = Inches(0.7)
    table.columns[2].width = Inches(0.8)
    table.columns[3].width = Inches(0.9)
    table.columns[4].width = Inches(1.1)

    headers = ["Drug & Algorithm", "Nodes", "Edges", "Density", "Enrichment"]
    rows = [
        ["Metformin · 2-Hop", "500", "21,448", "0.1719", "Baseline"],
        ["Metformin · RWR", "150", "4,891", "0.4377", "2.5× Density"],
        ["Imatinib · 2-Hop", "500", "22,559", "0.1808", "Baseline"],
        ["Imatinib · RWR", "150", "2,754", "0.2464", "1.4× Density"]
    ]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(24, 32, 48)
        cell.text_frame.text = h
        p = cell.text_frame.paragraphs[0]
        p.font.name = FONT_HEADING
        p.font.size = Pt(8.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_CYAN

    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_CARD_BG
            cell.text_frame.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.name = FONT_BODY
            p.font.size = Pt(8.5)
            p.font.color.rgb = COLOR_TEXT_PRIMARY if j != 4 else (COLOR_ORANGE if "2.5×" in val else COLOR_GREEN)
            if j == 4:
                p.font.bold = True

    # Callout text below table
    p6_sub = tf6.add_paragraph()
    p6_sub.text = "\n\n\n\n\n\n\n• Jaccard Overlap: Metformin 2-Hop vs RWR = 0.2621 | Imatinib 2-Hop vs RWR = 0.1344\n• Key Topological Discovery: Metformin achieves a remarkable 0.4377 subnetwork density because mitochondrial Complex I comprises 45 tightly physical-bound NDUF subunits. In contrast, Imatinib's kinase targets branch into divergent downstream cascades (MAPK, PI3K), yielding modular clusters."
    p6_sub.font.name = FONT_BODY
    p6_sub.font.size = Pt(9)
    p6_sub.font.color.rgb = COLOR_TEXT_MUTED
    p6_sub.space_before = Pt(8)

    # Right Screenshot: tight_subnetwork_canvas.png
    add_screenshot_frame(s6, os.path.join(CROPS_DIR, "tight_subnetwork_canvas.png"), "PharmaPath Real Platform — Subnetwork Diffusion & Density Engine", "Real Platform View: RWR Concentrates High-Density Functional Complex (Density = 0.4377 vs 0.1719)", "QUANTITATIVE PROOF")
    add_footer(s6, "Analysis")

    add_notes(s6, """ORAL PRESENTATION SCRIPT - ANALYSIS (DIFFUSION & DENSITY):
Now let us examine our primary Analysis findings, beginning with subnetwork extraction and diffusion:
In graph theory, extracting a naive 2-hop neighborhood captures hundreds of peripheral interactome nodes that are mere bystanders.
To demonstrate this, we compared naive 2-hop extraction against Random Walk with Restart (RWR, r=0.5).
Look at the density table:
For Metformin, 2-hop neighborhood extraction produces a graph density of 0.1719 across 500 nodes. But RWR concentrates the top 150 nodes, driving graph density to 0.4377—a massive 2.5-fold enrichment!
For Imatinib, RWR enriches density from 0.1808 to 0.2464 (a 1.4-fold enrichment).
Why does Metformin exhibit significantly higher subnetwork density than Imatinib?
The biological explanation is elegant: Metformin's 61 targets are dominated by Mitochondrial Complex I, a physical stoichiometric macromolecular machine comprising 45 tightly interconnected NDUF subunits.
Imatinib, on the other hand, targets tyrosine kinases that signal pleiotropically down divergent signaling branches (such as RAS/RAF/MEK/ERK and PI3K/AKT), yielding modular subgraphs rather than a single monolithic complex.
On the right, you can see our live platform's canvas displaying this tightly bound 150-node Metformin subnetwork.""")

    # ==========================================================================
    # SLIDE 7: ANALYSIS - PATHWAYS (Topic 5 / 8 Cont.)
    # ==========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "TOPIC 5 / 8 (CONT)", "Analysis · Biological Validation & Pathway ORA", "Ground-Truth", "Biological Sanity Verified", "Automated statistical verification across KEGG 2021 Human and Reactome 2022 signatures")

    # Left Container
    c7 = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c7.fill.solid()
    c7.fill.fore_color.rgb = COLOR_CARD_BG
    c7.line.color.rgb = COLOR_CARD_BORDER
    tf7 = c7.text_frame
    tf7.word_wrap = True
    tf7.margin_left = tf7.margin_right = tf7.margin_top = tf7.margin_bottom = Inches(0.22)

    p7 = tf7.paragraphs[0]
    p7.text = "Automated Hallmark Sanity Audit Results"
    p7.font.name = FONT_HEADING
    p7.font.size = Pt(14)
    p7.font.bold = True
    p7.font.color.rgb = COLOR_TEXT_PRIMARY

    p7_desc = tf7.add_paragraph()
    p7_desc.text = "Without synthetic parameter adjustments, both drug subnetworks automatically passed stringent over-representation analysis (ORA) tests using Benjamini–Hochberg false discovery rate correction:"
    p7_desc.font.name = FONT_BODY
    p7_desc.font.size = Pt(9.5)
    p7_desc.font.color.rgb = COLOR_TEXT_BODY
    p7_desc.space_before = Pt(4)

    ora_results = [
        ("METFORMIN → TYPE 2 DIABETES (4/5 AUDIT PASSED)", "Top recovered pathways: Oxidative phosphorylation (FDR = 1.26 × 10⁻¹⁵³), Respiratory Electron Transport (FDR = 2.08 × 10⁻¹⁶⁶), AMPK signaling, mTOR signaling, Insulin signaling, FoxO signaling.", COLOR_ORANGE),
        ("IMATINIB → CHRONIC MYELOID LEUKEMIA (5/6 AUDIT PASSED)", "Top recovered pathways: Chronic Myeloid Leukemia (FDR = 1.25 × 10⁻²⁴), Signaling by Receptor Tyrosine Kinases (FDR = 1.46 × 10⁻⁹⁶), Ras signaling (FDR = 2.21 × 10⁻¹¹⁶), PI3K-Akt signaling, MAPK cascades.", COLOR_CYAN)
    ]
    for r_title, r_desc, r_col in ora_results:
        p_r = tf7.add_paragraph()
        p_r.space_before = Pt(8)
        r_rt = p_r.add_run()
        r_rt.text = r_title + "\n"
        r_rt.font.name = FONT_HEADING
        r_rt.font.size = Pt(10)
        r_rt.font.bold = True
        r_rt.font.color.rgb = r_col
        r_rd = p_r.add_run()
        r_rd.text = r_desc
        r_rd.font.name = FONT_BODY
        r_rd.font.size = Pt(9)
        r_rd.font.color.rgb = COLOR_TEXT_BODY

    p7_sig = tf7.add_paragraph()
    p7_sig.text = "Multi-Omics Significance & Provenance:"
    p7_sig.font.name = FONT_HEADING
    p7_sig.font.size = Pt(10)
    p7_sig.font.bold = True
    p7_sig.font.color.rgb = COLOR_GREEN
    p7_sig.space_before = Pt(10)

    p7_sig_t = tf7.add_paragraph()
    p7_sig_t.text = "The astronomical statistical significance (FDR down to 10⁻¹⁶⁶) confirms that the high-confidence STRING v12 physical interactome faithfully preserves native cellular signaling pathways without introducing spurious cross-contamination."
    p7_sig_t.font.name = FONT_BODY
    p7_sig_t.font.size = Pt(9)
    p7_sig_t.font.color.rgb = COLOR_TEXT_MUTED

    # Right Screenshot: tight_pathways_studio.png
    add_screenshot_frame(s7, os.path.join(CROPS_DIR, "tight_pathways_studio.png"), "PharmaPath Real Platform — Pathway Enrichment Studio", "Real Platform View: Top Enriched Pathways Bar Chart (-log10 P-Value) & Ranking Table", "FDR < 0.05")
    add_footer(s7, "Analysis")

    add_notes(s7, """ORAL PRESENTATION SCRIPT - ANALYSIS (BIOLOGICAL VALIDATION & PATHWAYS):
Next in our Analysis is Biological Sanity Validation:
A critical question in computational biology is: 'Does our graph extraction capture genuine molecular biology, or merely mathematical artifacts?'
To resolve this, PharmaPath incorporates an automated Biological Sanity Audit Engine.
We queried each extracted subnetwork against official KEGG 2021 Human and Reactome 2022 libraries using Fisher's exact over-representation test with Benjamini-Hochberg FDR correction.
The results are unambiguous:
For Metformin, the platform automatically recovers Oxidative Phosphorylation with an FDR of 1.26 × 10⁻¹⁵³, and Respiratory Electron Transport at 2.08 × 10⁻¹⁶⁶, alongside AMPK and Insulin signaling.
For Imatinib, the platform automatically identifies Chronic Myeloid Leukemia at an FDR of 1.25 × 10⁻²⁴, Receptor Tyrosine Kinase signaling at 1.46 × 10⁻⁹⁶, and Ras signaling at 2.21 × 10⁻¹¹⁶.
On the right, you can see our platform's Pathway Enrichment Studio rendering the -log10 P-value bar charts and the underlying gene overlap tables.""")

    # ==========================================================================
    # SLIDE 8: ANALYSIS - PROXIMITY (Topic 5 / 8 Cont.)
    # ==========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "TOPIC 5 / 8 (CONT)", "Analysis · Statistical Disease Module Proximity", "Topological Proximity", "Proves Specificity", "1,000 degree-matched null permutations eliminate degree bias artifacts (Guney et al. 2016)")

    # Left Container with Table
    c8 = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c8.fill.solid()
    c8.fill.fore_color.rgb = COLOR_CARD_BG
    c8.line.color.rgb = COLOR_CARD_BORDER
    tf8 = c8.text_frame
    tf8.word_wrap = True
    tf8.margin_left = tf8.margin_right = tf8.margin_top = tf8.margin_bottom = Inches(0.2)

    p8 = tf8.paragraphs[0]
    p8.text = "Disease Module Proximity Benchmark Summary"
    p8.font.name = FONT_HEADING
    p8.font.size = Pt(14)
    p8.font.bold = True
    p8.font.color.rgb = COLOR_TEXT_PRIMARY

    p8_desc = tf8.add_paragraph()
    p8_desc.text = "To evaluate whether drug targets reside closer to disease genes than expected by chance, closest distance ⟨dc(T,S)⟩ was tested against 1,000 degree-matched random node sets:"
    p8_desc.font.name = FONT_BODY
    p8_desc.font.size = Pt(9.5)
    p8_desc.font.color.rgb = COLOR_TEXT_BODY
    p8_desc.space_before = Pt(4)

    # Proximity Table
    t_prox_shape = s8.shapes.add_table(5, 6, Inches(1.0), Inches(2.85), Inches(5.35), Inches(1.65))
    t_prox = t_prox_shape.table
    t_prox.columns[0].width = Inches(1.5)
    t_prox.columns[1].width = Inches(0.7)
    t_prox.columns[2].width = Inches(0.95)
    t_prox.columns[3].width = Inches(0.7)
    t_prox.columns[4].width = Inches(0.65)
    t_prox.columns[5].width = Inches(0.85)

    headers_p = ["Drug → Disease", "Obs dc", "Null Mean±Std", "Z-Score", "P-Val", "Verdict"]
    rows_p = [
        ["Metformin → T2D", "0.213", "1.012 ± 0.044", "-18.28", "0.0010", "PROXIMATE"],
        ["Imatinib → CML", "0.400", "1.228 ± 0.114", "-7.25", "0.0010", "PROXIMATE"],
        ["Metformin → CML", "1.951", "1.097 ± 0.047", "+18.32", "1.0000", "NOT PROX."],
        ["Imatinib → T2D", "1.300", "1.150 ± 0.127", "+1.18", "0.9650", "NOT PROX."]
    ]
    for j, h in enumerate(headers_p):
        cell = t_prox.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(24, 32, 48)
        cell.text_frame.text = h
        p = cell.text_frame.paragraphs[0]
        p.font.name = FONT_HEADING
        p.font.size = Pt(8)
        p.font.bold = True
        p.font.color.rgb = COLOR_CYAN

    for i, row in enumerate(rows_p):
        for j, val in enumerate(row):
            cell = t_prox.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_CARD_BG
            cell.text_frame.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.name = FONT_BODY
            p.font.size = Pt(8)
            if j == 3: # Z-Score
                p.font.bold = True
                p.font.color.rgb = COLOR_GREEN if "-" in val else COLOR_RED
            elif j == 5: # Verdict
                p.font.bold = True
                p.font.color.rgb = COLOR_GREEN if "PROXIMATE" == val else COLOR_RED
            else:
                p.font.color.rgb = COLOR_TEXT_PRIMARY

    # Discussion bullets below table
    p8_sub = tf8.add_paragraph()
    p8_sub.text = "\n\n\n\n\n\n\n• Primary Indications Highly Significant: Both Metformin (z = -18.28) and Imatinib (z = -7.25) reside deep within their disease modules (z ≤ -2.0, empirical p = 0.0010).\n• Reciprocal Negative Controls Fail: Cross-disease pairs yielded positive z-scores (+18.32 and +1.18), proving network localization is disease-specific and not a degree bias artifact."
    p8_sub.font.name = FONT_BODY
    p8_sub.font.size = Pt(9)
    p8_sub.font.color.rgb = COLOR_TEXT_MUTED
    p8_sub.space_before = Pt(8)

    # Right Screenshot: tight_proximity_studio.png
    add_screenshot_frame(s8, os.path.join(CROPS_DIR, "tight_proximity_studio.png"), "PharmaPath Real Platform — Disease Proximity Null Permutations", "Real Platform View: Permutation Null vs. Observed Distance (0.400, z = -7.25, p = 0.0010)", "1,000 PERMUTATIONS")
    add_footer(s8, "Analysis")

    add_notes(s8, """ORAL PRESENTATION SCRIPT - ANALYSIS (DISEASE PROXIMITY):
Now we arrive at one of the most critical methodological contributions of our work: Disease Module Proximity and Degree-Matched Null Permutations.
In network biology, highly connected hub proteins naturally have short topological distances to almost everything in the interactome. If one does not control for node degree, one will mistakenly claim that every drug is 'close' to every disease.
To eliminate this artifact, following Guney et al. (Nature Communications 2016), we implemented a degree-matched null permutation test with 1,000 iterations.
For each permutation, we sampled random sets of proteins that possess identical degree distributions to the true drug targets.
The results confirm authentic biological localization:
1. Metformin to Type 2 Diabetes exhibits an observed distance of 0.213 versus a null mean of 1.012, yielding a massive z-score of -18.28 and empirical p = 0.0010.
2. Imatinib to Chronic Myeloid Leukemia achieves an observed distance of 0.400 versus a null mean of 1.228, yielding a z-score of -7.25 and p = 0.0010.
Crucially, look at our negative controls:
When Metformin was tested against CML, the z-score inverted to +18.32 (p = 1.0000).
When Imatinib was tested against Type 2 Diabetes, the z-score was +1.18 (p = 0.9650).
This reciprocal failure of negative controls proves that our metric is disease-specific.""")

    # ==========================================================================
    # SLIDE 9: DISCUSSION - GNN & TARGET RECOVERY (Topic 6 / 8)
    # ==========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "TOPIC 6 / 8", "Discussion · Graph Neural Networks & AI Discovery", "Inductive AI Enables", "Predictive Reach", "Leakage-safe link prediction and leave-targets-out recovery generate testable hypotheses")

    # Left Container with GNN table
    c9 = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c9.fill.solid()
    c9.fill.fore_color.rgb = COLOR_CARD_BG
    c9.line.color.rgb = COLOR_CARD_BORDER
    tf9 = c9.text_frame
    tf9.word_wrap = True
    tf9.margin_left = tf9.margin_right = tf9.margin_top = tf9.margin_bottom = Inches(0.2)

    p9 = tf9.paragraphs[0]
    p9.text = "Inductive Link Prediction Benchmark (Zero Data Leakage)"
    p9.font.name = FONT_HEADING
    p9.font.size = Pt(13.5)
    p9.font.bold = True
    p9.font.color.rgb = COLOR_TEXT_PRIMARY

    p9_desc = tf9.add_paragraph()
    p9_desc.text = "To ensure zero topological edge leakage, test edges were completely removed from message-passing graphs before inductive aggregation:"
    p9_desc.font.name = FONT_BODY
    p9_desc.font.size = Pt(9.5)
    p9_desc.font.color.rgb = COLOR_TEXT_BODY
    p9_desc.space_before = Pt(4)

    # GNN Table
    t_gnn_shape = s9.shapes.add_table(4, 4, Inches(1.0), Inches(2.75), Inches(5.35), Inches(1.3))
    t_gnn = t_gnn_shape.table
    t_gnn.columns[0].width = Inches(2.1)
    t_gnn.columns[1].width = Inches(1.0)
    t_gnn.columns[2].width = Inches(1.0)
    t_gnn.columns[3].width = Inches(1.25)

    headers_g = ["Model Architecture", "Test AUROC", "Test AP", "Edge Leakage Barrier"]
    rows_g = [
        ["Node2Vec + Logistic Reg.", "0.5000", "0.5000", "Transductive Baseline"],
        ["GraphSAGE (Inductive)", "0.8865", "0.9008", "Zero Edge Leakage"],
        ["Graph Autoencoder (GAE)", "0.8832", "0.8958", "Zero Edge Leakage"]
    ]
    for j, h in enumerate(headers_g):
        cell = t_gnn.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(24, 32, 48)
        cell.text_frame.text = h
        p = cell.text_frame.paragraphs[0]
        p.font.name = FONT_HEADING
        p.font.size = Pt(8)
        p.font.bold = True
        p.font.color.rgb = COLOR_CYAN

    for i, row in enumerate(rows_g):
        for j, val in enumerate(row):
            cell = t_gnn.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_CARD_BG
            cell.text_frame.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.name = FONT_BODY
            p.font.size = Pt(8.5)
            if j in (1, 2) and i == 1:
                p.font.bold = True
                p.font.color.rgb = COLOR_ORANGE
            elif j == 3:
                p.font.color.rgb = COLOR_GREEN if "Zero" in val else COLOR_TEXT_MUTED
            else:
                p.font.color.rgb = COLOR_TEXT_PRIMARY

    # GNN discussion text
    p9_sub = tf9.add_paragraph()
    p9_sub.text = "\n\n\n\n\n• Leave-Targets-Out Cross-Validation: When holding out ground-truth targets from training, GraphSAGE recovered NDUFS7 at Rank #15 / 15,882 (Hits@20 = 50.0%) for Metformin, and CSF1R at Rank #85 / 15,882 for Imatinib.\n• Novel Candidate Hypotheses (PubMed Verified):\n  - Metformin: NDC80 (Rank 1, kinetochore arrest in cancer), UQCR11 & UQCRH (Complex III respiratory chain rewiring).\n  - Imatinib: ATP5F1D (Rank 1, ATP synthase metabolism), CHUK/IKK-α (Rank 2, NF-κB survival), NEDD8 (Rank 3, neddylation)."
    p9_sub.font.name = FONT_BODY
    p9_sub.font.size = Pt(8.5)
    p9_sub.font.color.rgb = COLOR_TEXT_MUTED
    p9_sub.space_before = Pt(6)

    # Right Screenshot: tight_gnn_studio.png
    add_screenshot_frame(s9, os.path.join(CROPS_DIR, "tight_gnn_studio.png"), "PharmaPath Real Platform — GNN Link Prediction Studio", "Real Platform View: Inductive Benchmark, ROC/PR Curves, & Top-20 Novel Candidate Hypotheses", "INDUCTIVE AI")
    add_footer(s9, "Discussion")

    add_notes(s9, """ORAL PRESENTATION SCRIPT - DISCUSSION (GNN & TARGET RECOVERY):
Entering our Discussion, we assess the predictive capabilities of Inductive Graph Neural Networks:
A widespread flaw in published network pharmacology literature is data leakage—models evaluate link prediction on the same interactome edges used to compute node embeddings.
In PharmaPath, we enforce an inductive 80/10/10 edge split with complete exclusion from message passing.
Under this rigorous split, GraphSAGE achieves a test AUROC of 0.8865 and an Average Precision of 0.9008, closely matched by Graph Autoencoder (0.8832 AUROC).
To test real-world target discovery, we executed a Leave-Targets-Out validation experiment.
We hid ground-truth drug targets from training and asked the model to rank all 15,882 interactome proteins.
Remarkably, GraphSAGE prioritized NDUFS7 at Rank #15 out of 15,882 (Hits@20 = 50.0%) for Metformin, and CSF1R at Rank #85 for Imatinib.
Beyond known targets, the model generates novel repurposing hypotheses:
For Metformin, it predicts NDC80, a kinetochore protein, consistent with Metformin's emerging role in mitotic arrest in oncology.
For Imatinib, it prioritizes CHUK (IKK-alpha) and NEDD8, central mediators of NF-kB survival pathways known to mediate TKI resistance.
On the right, our platform displays the ROC and Precision-Recall curves alongside the top-20 ranked candidate hypotheses with direct PubMed search links.""")

    # ==========================================================================
    # SLIDE 10: DISCUSSION - COMBINATION SYNERGY (Topic 6 / 8 Cont.)
    # ==========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "TOPIC 6 / 8 (CONT)", "Discussion · Combination Pharmacology & Synergy", "Distinct Direct Targets,", "Shared Therapeutic Logic", "Menche separation s_AB = +1.3503 paired with 347 shared interactome cross-talk hubs")

    # Left Container
    c10 = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c10.fill.solid()
    c10.fill.fore_color.rgb = COLOR_CARD_BG
    c10.line.color.rgb = COLOR_CARD_BORDER
    tf10 = c10.text_frame
    tf10.word_wrap = True
    tf10.margin_left = tf10.margin_right = tf10.margin_top = tf10.margin_bottom = Inches(0.22)

    p10 = tf10.paragraphs[0]
    p10.text = "Interactome Separation vs. Cross-Talk Bridges"
    p10.font.name = FONT_HEADING
    p10.font.size = Pt(14)
    p10.font.bold = True
    p10.font.color.rgb = COLOR_TEXT_PRIMARY

    p10_desc = tf10.add_paragraph()
    p10_desc.text = "Metformin and Imatinib share 0 direct targets and exhibit an interactome separation of s_AB = +1.3503 (Menche et al. 2015), confirming distinct primary mechanism modules."
    p10_desc.font.name = FONT_BODY
    p10_desc.font.size = Pt(9.5)
    p10_desc.font.color.rgb = COLOR_TEXT_BODY
    p10_desc.space_before = Pt(4)

    # 3 Metric boxes
    p10_m = tf10.add_paragraph()
    p10_m.text = "• Menche Separation: s_AB = +1.3503 (Separated Modules, s > 0)\n• Shared 2-Hop Interactome Hubs: 347 Proteins (Jaccard = 0.5314)\n• Shared Direct Targets: 0 (Target Jaccard = 0.0000)"
    p10_m.font.name = FONT_MONO
    p10_m.font.size = Pt(9.5)
    p10_m.font.bold = True
    p10_m.font.color.rgb = COLOR_CYAN
    p10_m.space_before = Pt(6)

    p10_syn = tf10.add_paragraph()
    p10_syn.text = "Clinical Synergy: Overcoming CML Resistance"
    p10_syn.font.name = FONT_HEADING
    p10_syn.font.size = Pt(11)
    p10_syn.font.bold = True
    p10_syn.font.color.rgb = COLOR_GREEN
    p10_syn.space_before = Pt(8)

    p10_syn_t = tf10.add_paragraph()
    p10_syn_t.text = "1. Eradication of Quiescent Leukemic Stem Cells (LSCs):\nImatinib monotherapy eliminates proliferating blast cells but spares dormant LSCs that depend on oxidative phosphorylation. Metformin selectively inhibits Complex I, depleting ATP pools and forcing resistant LSCs into apoptosis.\n\n2. Shared Signaling Intersections:\nTheir 2-hop neighborhoods intersect at 347 shared proteins, including 22 master hubs: AKT1, TP53, MAPK1, STAT3, and SRC, explaining synthetic lethality.\n\n3. Cardioprotective Counter-Effect:\nMetformin's AMPK activation counters off-target cardiotoxicity induced by ABL kinase inhibitors."
    p10_syn_t.font.name = FONT_BODY
    p10_syn_t.font.size = Pt(9)
    p10_syn_t.font.color.rgb = COLOR_TEXT_BODY
    p10_syn_t.space_before = Pt(4)

    # Right Screenshot: tight_comparison_studio.png
    add_screenshot_frame(s10, os.path.join(CROPS_DIR, "tight_comparison_studio.png"), "PharmaPath Real Platform — Shared Cross-Talk & Synergy Report", "Real Platform View: Shared Cross-Talk Hubs (TP53, RPS27A, UBA52) & Combination Mechanism", "CLINICAL HYPOTHESIS")
    add_footer(s10, "Discussion")

    add_notes(s10, """ORAL PRESENTATION SCRIPT - DISCUSSION (COMBINATION PHARMACOLOGY):
Continuing our Discussion, we investigate Combination Pharmacology and Synergy:
Can two drugs with zero shared targets produce therapeutic synergy?
Using the Menche et al. (Science 2015) separation metric, we find that Metformin and Imatinib exhibit an s_AB separation of +1.3503.
In network medicine, an s_AB > 0 proves that their direct target modules are topologically separated.
Yet, when we look at their 2-hop signaling neighborhoods, they intersect at 347 shared proteins, with a high Jaccard overlap of 0.5314.
Among these 347 shared proteins are 22 master signaling hubs—including AKT1, TP53, MAPK1, and STAT3.
This topological configuration explains the clinical phenomenon of synthetic lethality in Chronic Myeloid Leukemia:
While Imatinib monotherapy eliminates proliferating blast cells, patients frequently relapse due to quiescent leukemic stem cells (LSCs). These dormant LSCs do not depend on BCR-ABL signaling; instead, they rely on oxidative phosphorylation for survival.
By adding Metformin, we selectively inhibit Complex I, starving dormant LSCs of ATP and eliminating the reservoir of disease resistance.
Furthermore, Metformin's activation of AMPK protects cardiomyocytes against off-target BCR-ABL cardiotoxicity.
On the right, our Two-Drug Comparison Studio summarizes this synergy report and highlights shared cross-talk bottlenecks.""")

    # ==========================================================================
    # SLIDE 11: CONCLUSION (Topic 7 / 8)
    # ==========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "TOPIC 7 / 8", "Conclusion · Synthesis & Future Horizons", "Summary of Findings &", "Impact", "A validated, leak-free computational standard for biological database network pharmacology")

    # Left Container
    c11 = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c11.fill.solid()
    c11.fill.fore_color.rgb = COLOR_CARD_BG
    c11.line.color.rgb = COLOR_CARD_BORDER
    tf11 = c11.text_frame
    tf11.word_wrap = True
    tf11.margin_left = tf11.margin_right = tf11.margin_top = tf11.margin_bottom = Inches(0.22)

    p11 = tf11.paragraphs[0]
    p11.text = "Key Project Deliverables & Scientific Contributions"
    p11.font.name = FONT_HEADING
    p11.font.size = Pt(14)
    p11.font.bold = True
    p11.font.color.rgb = COLOR_TEXT_PRIMARY

    contribs = [
        ("Seamless Biological Database Integration:", " Ingested and mapped 15,882 proteins and 236,712 STRING v12 edges with 0.0000% mapping loss, unifying ChEMBL, LINCS, and Open Targets."),
        ("Topological Specificity Over Degree Bias:", " 1,000 degree-matched permutations confirmed authentic disease localization for Metformin (z = -18.28) and Imatinib (z = -7.25) with reciprocal control divergence."),
        ("Leak-Free Inductive Machine Learning:", " GraphSAGE achieved 0.8865 AUROC and prioritized hidden targets (NDUFS7 at #15 / 15,882) without edge contamination."),
        ("Open Interactive Discovery Lab:", " Published a responsive web platform with Vis-Network canvases, Chart.js analytics, and 100% PyTest automated coverage.")
    ]
    for c_title, c_text in contribs:
        p_c = tf11.add_paragraph()
        p_c.space_before = Pt(6)
        r_ct = p_c.add_run()
        r_ct.text = "• " + c_title
        r_ct.font.name = FONT_HEADING
        r_ct.font.size = Pt(9.5)
        r_ct.font.bold = True
        r_ct.font.color.rgb = COLOR_CYAN
        r_cx = p_c.add_run()
        r_cx.text = c_text
        r_cx.font.name = FONT_BODY
        r_cx.font.size = Pt(9)
        r_cx.font.color.rgb = COLOR_TEXT_BODY

    p11_caveat = tf11.add_paragraph()
    p11_caveat.text = "Responsible-AI Caveat & Future Horizons:"
    p11_caveat.font.name = FONT_HEADING
    p11_caveat.font.size = Pt(10)
    p11_caveat.font.bold = True
    p11_caveat.font.color.rgb = COLOR_ORANGE
    p11_caveat.space_before = Pt(10)

    p11_cav_t = tf11.add_paragraph()
    p11_cav_t.text = "GNN predictions represent topological hypotheses and functional associations, not direct biochemical binding proofs. Future work involves single-cell RNA-seq integration, tissue-specific interactomes, and wet-lab surface plasmon resonance (SPR) binding validation."
    p11_cav_t.font.name = FONT_BODY
    p11_cav_t.font.size = Pt(9)
    p11_cav_t.font.color.rgb = COLOR_TEXT_MUTED

    # Right Screenshot: 01_subnetwork_metformin.png
    add_screenshot_frame(s11, os.path.join(ASSETS_DIR, "01_subnetwork_metformin.png"), "PharmaPath Real Platform — Complete Research Discovery Suite", "Live Deployment: Reproducible Computational Discovery (pharmapath-website.vercel.app)", "CAPSTONE COMPLETE")
    add_footer(s11, "Conclusion")

    add_notes(s11, """ORAL PRESENTATION SCRIPT - CONCLUSION:
In Conclusion:
PharmaPath successfully establishes an open, reproducible computational standard for biological database network pharmacology.
We have demonstrated:
1. That Random Walk with Restart enriches subnetwork functional density by up to 2.5-fold compared to naive peripheral neighborhoods.
2. That degree-matched null permutations are essential to separate authentic biological disease proximity from hub bias.
3. That inductive Graph Neural Networks can prioritize hidden targets (NDUFS7 at #15 / 15,882) without topological leakage.
4. That separated interactome modules can share rich cross-talk bridges (347 shared proteins) underpinning clinical synergy.
In the spirit of Responsible AI, we emphasize that computational graph predictions are prioritizations and functional hypotheses, requiring wet-lab biophysical confirmation.
All code, pre-computed databases, and interactive tools are packaged with automated test suites and hosted live at pharmapath-website.vercel.app.""")

    # ==========================================================================
    # SLIDE 12: REFERENCES (Topic 8 / 8)
    # ==========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, "TOPIC 8 / 8", "References · Literature & Project Deliverables", "References &", "Evidence Base", "Primary scientific literature, genomic databases, and PharmaPath documentation")

    # Left Card: Peer-Reviewed Literature
    c12_l = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.85), Inches(5.75), Inches(5.0))
    c12_l.fill.solid()
    c12_l.fill.fore_color.rgb = COLOR_CARD_BG
    c12_l.line.color.rgb = COLOR_CARD_BORDER
    tf12_l = c12_l.text_frame
    tf12_l.word_wrap = True
    tf12_l.margin_left = tf12_l.margin_right = tf12_l.margin_top = tf12_l.margin_bottom = Inches(0.22)

    p12_l_h = tf12_l.paragraphs[0]
    p12_l_h.text = "Primary Peer-Reviewed Literature"
    p12_l_h.font.name = FONT_HEADING
    p12_l_h.font.size = Pt(14)
    p12_l_h.font.bold = True
    p12_l_h.font.color.rgb = COLOR_TEXT_PRIMARY

    refs = [
        ("Guney, E. et al. (2016):", " Network-based in silico drug efficacy screening. Nature Communications, 7, 10331."),
        ("Menche, J. et al. (2015):", " Uncovering disease-disease relationships through the incomplete interactome. Science, 347(6224), 1257601."),
        ("Barabási, A. L. et al. (2011):", " Network medicine: a network-based approach to human disease. Nat Rev Genet, 12(1), 56–68."),
        ("Hamilton, W. et al. (2017):", " Inductive representation learning on large graphs. NeurIPS 2017, 1024–1034."),
        ("Szklarczyk, D. et al. (2023):", " The STRING database in 2023. Nucleic Acids Res, 51(D1), D638–D646."),
        ("Subramanian, A. et al. (2017):", " A Next Generation Connectivity Map: L1000 Platform. Cell, 171(6), 1437–1452.")
    ]
    for r_auth, r_cite in refs:
        p_ref = tf12_l.add_paragraph()
        p_ref.space_before = Pt(6)
        r_ra = p_ref.add_run()
        r_ra.text = "• " + r_auth
        r_ra.font.name = FONT_HEADING
        r_ra.font.size = Pt(9.5)
        r_ra.font.bold = True
        r_ra.font.color.rgb = COLOR_ORANGE_LIGHT
        r_rc = p_ref.add_run()
        r_rc.text = r_cite
        r_rc.font.name = FONT_BODY
        r_rc.font.size = Pt(9)
        r_rc.font.color.rgb = COLOR_TEXT_BODY

    # Right Card: Deliverables & Viva Summary
    c12_r = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.78), Inches(1.85), Inches(5.75), Inches(5.0))
    c12_r.fill.solid()
    c12_r.fill.fore_color.rgb = COLOR_CARD_BG
    c12_r.line.color.rgb = COLOR_CARD_BORDER
    tf12_r = c12_r.text_frame
    tf12_r.word_wrap = True
    tf12_r.margin_left = tf12_r.margin_right = tf12_r.margin_top = tf12_r.margin_bottom = Inches(0.22)

    p12_r_h = tf12_r.paragraphs[0]
    p12_r_h.text = "Database Repositories & Project Deliverables"
    p12_r_h.font.name = FONT_HEADING
    p12_r_h.font.size = Pt(14)
    p12_r_h.font.bold = True
    p12_r_h.font.color.rgb = COLOR_TEXT_PRIMARY

    delivs = [
        ("STRING v12 & ChEMBL 33:", " Physical PPI scaffold (≥700) and curated target bioactivity profiles."),
        ("LINCS L1000 & Open Targets:", " Cellular perturbation signatures and disease genetics GraphQL API."),
        ("Live Interactive Web Application:", " Hosted at https://pharmapath-website.vercel.app with Vis-Network & Chart.js."),
        ("Automated PyTest Testing Suite:", " 100% test pass rate verifying graph connectivity and pipeline reproducibility."),
        ("Comprehensive Technical Documentation:", " Complete Master Defense Viva Documentation, Data Interpretation Guide, and Web Architecture Manual.")
    ]
    for d_title, d_text in delivs:
        p_d = tf12_r.add_paragraph()
        p_d.space_before = Pt(6)
        r_dt = p_d.add_run()
        r_dt.text = "• " + d_title
        r_dt.font.name = FONT_HEADING
        r_dt.font.size = Pt(9.5)
        r_dt.font.bold = True
        r_dt.font.color.rgb = COLOR_CYAN
        r_dx = p_d.add_run()
        r_dx.text = d_text
        r_dx.font.name = FONT_BODY
        r_dx.font.size = Pt(9)
        r_dx.font.color.rgb = COLOR_TEXT_BODY

    p12_close = tf12_r.add_paragraph()
    p12_close.text = "Capstone Defense Ready: Thank you, Examination Committee.\nWe welcome your questions and look forward to the live interactive system demonstration."
    p12_close.font.name = FONT_HEADING
    p12_close.font.size = Pt(10)
    p12_close.font.bold = True
    p12_close.font.color.rgb = COLOR_GREEN
    p12_close.space_before = Pt(14)

    add_footer(s12, "References")

    add_notes(s12, """ORAL PRESENTATION SCRIPT - REFERENCES & DEFENSE CLOSING:
Finally, on Slide 12, we present our References and Evidence Base:
All computational implementations are built directly upon the cited peer-reviewed literature in Nature Communications, Science, Nature Reviews Genetics, and NeurIPS.
All source code, data pipelines, and interactive deployment artifacts are fully documented and reproducible.
Thank you very much, members of the committee, for your time and attention. I am now ready for your questions and would be delighted to demonstrate any feature live on our interactive web platform.""")

    # Save presentation to reports/ and root
    prs.save(OUTPUT_PPTX_REPORTS)
    shutil.copyfile(OUTPUT_PPTX_REPORTS, OUTPUT_PPTX_ROOT)
    print(f"Presentation saved successfully to:")
    print(f"  1. {OUTPUT_PPTX_REPORTS}")
    print(f"  2. {OUTPUT_PPTX_ROOT}")


if __name__ == "__main__":
    build_presentation()
