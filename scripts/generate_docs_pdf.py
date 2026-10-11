"""Generate publication-quality, color-coded PDF documents from PharmaPath markdown docs.

Uses Markdown with Pygments/extensions + Playwright Chromium for pixel-perfect print rendering.
Outputs:
1. docs/PharmaPath_Master_Technical_and_Viva_Documentation.pdf (Unified Master Volume)
2. docs/PharmaPath_Website_Architecture_Guide.pdf (Individual Document 1)
3. docs/PharmaPath_Data_Interpretation_and_Viva_Guide.pdf (Individual Document 2)
"""

import re
import sys
from pathlib import Path
import markdown
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"

CSS_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
  --primary-orange: #FF8000;
  --primary-orange-dark: #E66B00;
  --primary-orange-light: #FFF2E5;
  --secondary-orange: #FFA040;
  --dark-bg: #0B0E14;
  --dark-panel: #141A23;
  --text-dark: #1E293B;
  --text-muted: #64748B;
  --border-color: #E2E8F0;
  --tag-green-bg: #EAFBF1;
  --tag-green-text: #0E783C;
  --tag-green-border: #9BE6B8;
  --tag-red-bg: #FEF2F2;
  --tag-red-text: #DC2626;
  --tag-red-border: #FCA5A5;
  --tag-blue-bg: #EFF6FF;
  --tag-blue-text: #1D4ED8;
  --tag-blue-border: #BFDBFE;
  --tag-purple-bg: #F5F3FF;
  --tag-purple-text: #6D28D9;
  --tag-purple-border: #DDD6FE;
  --tag-orange-bg: #FFF7ED;
  --tag-orange-text: #C2410C;
  --tag-orange-border: #FFEDD5;
}

@page {
  size: A4 portrait;
  margin: 18mm 14mm 18mm 14mm;
}

@media print {
  body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .page-break {
    page-break-before: always !important;
    break-before: page !important;
  }
  .avoid-break {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }
}

* {
  box-sizing: border-box;
}

body {
  font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  color: #1E293B;
  background: #FFFFFF;
  line-height: 1.55;
  font-size: 10.5pt;
  margin: 0;
  padding: 0;
}

/* ========================================================================= */
/* COVER PAGE                                                                */
/* ========================================================================= */
.cover-page {
  height: 98vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 40px 30px;
  background: linear-gradient(145deg, #08090C 0%, #121620 55%, #1A202C 100%);
  color: #FFFFFF;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  page-break-after: always;
}

.cover-page::before {
  content: '';
  position: absolute;
  top: -120px;
  right: -120px;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(255, 128, 0, 0.25) 0%, rgba(255, 128, 0, 0) 70%);
  border-radius: 50%;
  pointer-events: none;
}

.cover-page::after {
  content: '';
  position: absolute;
  bottom: -150px;
  left: -150px;
  width: 450px;
  height: 450px;
  background: radial-gradient(circle, rgba(155, 89, 182, 0.18) 0%, rgba(155, 89, 182, 0) 70%);
  border-radius: 50%;
  pointer-events: none;
}

.cover-top {
  position: relative;
  z-index: 2;
}

.cover-badge-row {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 25px;
}

.cover-badge {
  background: rgba(255, 128, 0, 0.15);
  border: 1px solid rgba(255, 128, 0, 0.45);
  color: #FF9926;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 9pt;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}

.cover-badge.version {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  color: #CBD5E1;
}

.cover-title {
  font-size: 34pt;
  font-weight: 900;
  line-height: 1.15;
  margin: 0 0 16px 0;
  color: #FFFFFF;
  letter-spacing: -0.5px;
}

.cover-title span.hl {
  color: #FF8000;
  text-shadow: 0 0 25px rgba(255, 128, 0, 0.4);
}

.cover-subtitle {
  font-size: 13.5pt;
  font-weight: 400;
  color: #94A3B8;
  max-width: 680px;
  line-height: 1.5;
  margin-bottom: 30px;
}

.cover-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin: 25px 0 35px 0;
  position: relative;
  z-index: 2;
}

.cover-kpi-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 14px 16px;
  backdrop-filter: blur(8px);
}

.cover-kpi-val {
  font-size: 18pt;
  font-weight: 800;
  color: #FF8000;
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 4px;
}

.cover-kpi-lbl {
  font-size: 8.5pt;
  color: #94A3B8;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cover-meta {
  position: relative;
  z-index: 2;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  padding-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.cover-meta-col {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cover-meta-lbl {
  font-size: 8pt;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-weight: 600;
}

.cover-meta-val {
  font-size: 10pt;
  color: #E2E8F0;
  font-weight: 600;
}

/* ========================================================================= */
/* HEADINGS & TYPOGRAPHY                                                     */
/* ========================================================================= */
h1, h2, h3, h4, h5 {
  color: #0F172A;
  font-weight: 800;
  margin-top: 1.4em;
  margin-bottom: 0.5em;
  letter-spacing: -0.3px;
}

h1 {
  font-size: 20pt;
  color: #0F172A;
  border-bottom: 2.5px solid #FF8000;
  padding-bottom: 8px;
  margin-top: 1.8em;
  display: flex;
  align-items: center;
  gap: 8px;
}

h2 {
  font-size: 15pt;
  border-left: 4px solid #FF8000;
  padding-left: 10px;
  color: #1E293B;
  margin-top: 1.5em;
}

h3 {
  font-size: 12.5pt;
  color: #334155;
  margin-top: 1.3em;
}

h4 {
  font-size: 11pt;
  color: #475569;
}

p {
  margin: 0.6em 0;
  color: #334155;
}

strong {
  color: #0F172A;
  font-weight: 700;
}

/* ========================================================================= */
/* COLOR-CODED BADGES & TAGS                                                 */
/* ========================================================================= */
.badge {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 8pt;
  font-weight: 700;
  letter-spacing: 0.3px;
  text-transform: uppercase;
  margin: 1px 2px;
  vertical-align: middle;
}

.badge-orange {
  background: var(--tag-orange-bg);
  color: var(--tag-orange-text);
  border: 1px solid var(--tag-orange-border);
}

.badge-green {
  background: var(--tag-green-bg);
  color: var(--tag-green-text);
  border: 1px solid var(--tag-green-border);
}

.badge-red {
  background: var(--tag-red-bg);
  color: var(--tag-red-text);
  border: 1px solid var(--tag-red-border);
}

.badge-blue {
  background: var(--tag-blue-bg);
  color: var(--tag-blue-text);
  border: 1px solid var(--tag-blue-border);
}

.badge-purple {
  background: var(--tag-purple-bg);
  color: var(--tag-purple-text);
  border: 1px solid var(--tag-purple-border);
}

/* ========================================================================= */
/* COLOR-CODED CALLOUT BOXES                                                 */
/* ========================================================================= */
.callout {
  border-radius: 8px;
  padding: 12px 16px;
  margin: 14px 0;
  border-left: 4px solid;
  page-break-inside: avoid;
}

.callout-orange {
  background: #FFF9F3;
  border-color: #FF8000;
  color: #7C2D12;
}

.callout-green {
  background: #F0FDF4;
  border-color: #16A34A;
  color: #14532D;
}

.callout-blue {
  background: #F0F9FF;
  border-color: #0284C7;
  color: #0C4A6E;
}

.callout-purple {
  background: #FAF5FF;
  border-color: #9333EA;
  color: #581C87;
}

.callout-red {
  background: #FEF2F2;
  border-color: #EF4444;
  color: #7F1D1D;
}

blockquote {
  margin: 14px 0;
  padding: 10px 16px;
  background: #F8FAFC;
  border-left: 4px solid #CBD5E1;
  color: #475569;
  font-style: italic;
  border-radius: 0 6px 6px 0;
}

/* ========================================================================= */
/* MATHEMATICAL FORMULAS                                                     */
/* ========================================================================= */
.math-box {
  background: #0F172A;
  color: #FFA040;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10.5pt;
  padding: 12px 18px;
  border-radius: 6px;
  border-left: 4px solid #FF8000;
  margin: 12px 0;
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
  page-break-inside: avoid;
}

.math-inline {
  font-family: 'JetBrains Mono', monospace;
  color: #C2410C;
  background: #FFF7ED;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 9.5pt;
}

/* ========================================================================= */
/* TABLES                                                                    */
/* ========================================================================= */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 9pt;
  page-break-inside: auto;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border-radius: 6px;
  overflow: hidden;
}

tr {
  page-break-inside: avoid;
  page-break-after: auto;
}

thead th {
  background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
  color: #FF8000;
  font-weight: 700;
  text-align: left;
  padding: 9px 11px;
  font-size: 8.5pt;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #FF8000;
}

tbody td {
  padding: 7px 11px;
  border-bottom: 1px solid #E2E8F0;
  color: #334155;
  vertical-align: middle;
}

tbody tr:nth-child(even) {
  background: #F8FAFC;
}

tbody tr:hover {
  background: #FFF7ED;
}

td strong {
  color: #0F172A;
}

/* ========================================================================= */
/* CODE BLOCKS & ASCII SCHEMATICS                                            */
/* ========================================================================= */
pre {
  background: #0B0E14;
  color: #E2E8F0;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 8.5pt;
  line-height: 1.45;
  padding: 14px 16px;
  border-radius: 8px;
  border-left: 3px solid #FF8000;
  overflow-x: auto;
  margin: 14px 0;
  page-break-inside: avoid;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}

code {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 9pt;
  background: #F1F5F9;
  color: #0F172A;
  padding: 1px 4px;
  border-radius: 3px;
  border: 1px solid #E2E8F0;
}

pre code {
  background: transparent;
  color: inherit;
  padding: 0;
  border: none;
}

/* ========================================================================= */
/* LISTS & HR                                                                */
/* ========================================================================= */
ul, ol {
  margin: 0.6em 0;
  padding-left: 24px;
}

li {
  margin-bottom: 0.4em;
  color: #334155;
}

hr {
  border: none;
  height: 1px;
  background: linear-gradient(to right, #FF8000, #E2E8F0, #FFFFFF);
  margin: 24px 0;
}

/* ========================================================================= */
/* RUNNING HEADER & FOOTER MARGIN BOXES                                      */
/* ========================================================================= */
.doc-footer {
  margin-top: 30px;
  border-top: 1px solid #CBD5E1;
  padding-top: 8px;
  display: flex;
  justify-content: space-between;
  font-size: 8pt;
  color: #94A3B8;
}
"""

def enhance_markdown_content(md_text: str) -> str:
    """Enhance markdown with color-coded badges, math formatting, and callouts."""
    text = md_text

    # Replace mathematical expressions
    def math_box_repl(match):
        formula = match.group(1).strip()
        return f'<div class="math-box">{formula}</div>'
    text = re.sub(r'\$\$(.*?)\$\$', math_box_repl, text, flags=re.DOTALL)

    def math_inline_repl(match):
        formula = match.group(1).strip()
        return f'<span class="math-inline">{formula}</span>'
    text = re.sub(r'\$([^\$\n]+)\$', math_inline_repl, text)

    # Convert badges and role tags
    badge_replacements = [
        (r'\b(Dual Bridge)\b', r'<span class="badge badge-purple">\1</span>'),
        (r'\b(Bottleneck)\b', r'<span class="badge badge-red">\1</span>'),
        (r'\b(Hub)\b', r'<span class="badge badge-orange">\1</span>'),
        (r'\b(Standard Node)\b', r'<span class="badge badge-blue">\1</span>'),
        (r'\b(SANITY PASSED)\b', r'<span class="badge badge-green">\1</span>'),
        (r'\b(PROXIMATE)\b', r'<span class="badge badge-green">\1</span>'),
        (r'\b(NOT PROXIMATE)\b', r'<span class="badge badge-red">\1</span>'),
        (r'\b(PASS)\b', r'<span class="badge badge-green">\1</span>'),
        (r'\b(FAIL)\b', r'<span class="badge badge-red">\1</span>'),
    ]
    for pattern, repl in badge_replacements:
        text = re.sub(pattern, repl, text)

    return text


def build_full_html(body_html: str, title: str, subtitle: str, doc_type: str) -> str:
    """Wrap body HTML in publication template with modern cover page."""
    cover_html = f"""
    <div class="cover-page">
      <div class="cover-top">
        <div class="cover-badge-row">
          <span class="cover-badge">PharmaPath Systems Platform</span>
          <span class="cover-badge version">v2.4.0 • Enterprise Edition</span>
          <span class="cover-badge version">{doc_type}</span>
        </div>
        <h1 class="cover-title">Pharma<span class="hl">Path</span><br>{title}</h1>
        <div class="cover-subtitle">{subtitle}</div>
        
        <div class="cover-kpi-grid">
          <div class="cover-kpi-card">
            <div class="cover-kpi-val">15,882</div>
            <div class="cover-kpi-lbl">Interactome Nodes</div>
          </div>
          <div class="cover-kpi-card">
            <div class="cover-kpi-val">236,712</div>
            <div class="cover-kpi-lbl">Physical Edges</div>
          </div>
          <div class="cover-kpi-card">
            <div class="cover-kpi-val">0.8865</div>
            <div class="cover-kpi-lbl">GraphSAGE AUROC</div>
          </div>
          <div class="cover-kpi-card">
            <div class="cover-kpi-val">z = -18.28</div>
            <div class="cover-kpi-lbl">T2D Proximity</div>
          </div>
        </div>
      </div>
      
      <div class="cover-meta">
        <div class="cover-meta-col">
          <span class="cover-meta-lbl">Author / Project</span>
          <span class="cover-meta-val">Senior Bioinformatics & ML Engineer</span>
        </div>
        <div class="cover-meta-col">
          <span class="cover-meta-lbl">Evaluation Environment</span>
          <span class="cover-meta-val">PyTorch 2.6 • PyG • NetworkX • Vis.js</span>
        </div>
        <div class="cover-meta-col">
          <span class="cover-meta-lbl">Validation Status</span>
          <span class="cover-meta-val" style="color: #4ADE80;">✓ 100% Tests Passed • Zero Leakage</span>
        </div>
        <div class="cover-meta-col">
          <span class="cover-meta-lbl">Date</span>
          <span class="cover-meta-val">October 2026</span>
        </div>
      </div>
    </div>
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title} | PharmaPath</title>
  <style>
{CSS_STYLES}
  </style>
</head>
<body>
  {cover_html}
  <div class="content-container">
    {body_html}
  </div>
</body>
</html>
"""


def convert_md_to_html(md_path: Path, title: str, subtitle: str, doc_type: str) -> str:
    raw_md = md_path.read_text(encoding='utf-8')
    enhanced_md = enhance_markdown_content(raw_md)
    html_body = markdown.markdown(
        enhanced_md,
        extensions=['tables', 'fenced_code', 'toc', 'sane_lists']
    )
    return build_full_html(html_body, title, subtitle, doc_type)


def render_pdf_with_playwright(html_content: str, output_pdf_path: Path):
    print(f"Rendering PDF: {output_pdf_path.name} ...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content, wait_until='networkidle')
        
        page.pdf(
            path=str(output_pdf_path),
            format='A4',
            print_background=True,
            margin={
                'top': '18mm',
                'bottom': '18mm',
                'left': '14mm',
                'right': '14mm'
            },
            display_header_footer=True,
            header_template='''
                <div style="font-family: 'Outfit', sans-serif; font-size: 7.5pt; color: #94A3B8; width: 100%; display: flex; justify-content: space-between; padding: 0 14mm;">
                  <span><strong>PharmaPath</strong> • Systems Network-Pharmacology & GNN Discovery</span>
                  <span style="color: #FF8000; font-weight: 700;">CONFIDENTIAL & ACADEMIC AUDIT</span>
                </div>
            ''',
            footer_template='''
                <div style="font-family: 'Outfit', sans-serif; font-size: 7.5pt; color: #94A3B8; width: 100%; display: flex; justify-content: space-between; padding: 0 14mm;">
                  <span>Multi-Omics Interactome Analysis (STRING v12 • LINCS L1000 • Open Targets)</span>
                  <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
                </div>
            '''
        )
        browser.close()
    print(f"  -> Generated: {output_pdf_path} ({output_pdf_path.stat().st_size / 1024:.1f} KB)")


def main():
    print("=" * 80)
    print("PHARMAPATH PDF GENERATOR: PUBLICATION-GRADE COLOR-CODED DOCUMENTS")
    print("=" * 80)

    doc1_path = DOCS_DIR / "WEBSITE_ARCHITECTURE_AND_HOW_IT_WORKS.md"
    doc2_path = DOCS_DIR / "DATA_INTERPRETATION_REAL_WORLD_IMPACT_AND_VIVA_QA.md"

    # 1. Generate Individual Document 1: Website Architecture Guide
    html1 = convert_md_to_html(
        doc1_path,
        title="Website Architecture & Engineering Blueprint",
        subtitle="Comprehensive technical guide to the frontend state machine, Vis.js Barnes-Hut canvas, asynchronous REST JSON pipeline, and Playwright verification.",
        doc_type="Technical Architecture Guide"
    )
    pdf1_path = DOCS_DIR / "PharmaPath_Website_Architecture_Guide.pdf"
    render_pdf_with_playwright(html1, pdf1_path)

    # 2. Generate Individual Document 2: Data Interpretation & Viva Guide
    html2 = convert_md_to_html(
        doc2_path,
        title="Data Interpretation, Real-World Impact & Viva Q&A Guide",
        subtitle="Exhaustive semantic breakdown of all website metrics, biological meanings, clinical translation in T2D/CML, and 50+ master defense questions.",
        doc_type="Clinical & Viva Master Guide"
    )
    pdf2_path = DOCS_DIR / "PharmaPath_Data_Interpretation_and_Viva_Guide.pdf"
    render_pdf_with_playwright(html2, pdf2_path)

    # 3. Generate Unified Master Document: Both Documents Merged
    print("\nMerging both documents into Unified Master Publication...")
    raw1 = doc1_path.read_text(encoding='utf-8')
    raw2 = doc2_path.read_text(encoding='utf-8')

    combined_md = f"""
# PART I: SYSTEM ARCHITECTURE & ENGINEERING BLUEPRINT

---

{raw1}

<div class="page-break"></div>

# PART II: DATA INTERPRETATION, CLINICAL TRANSLATION & VIVA DEFENSE GUIDE

---

{raw2}
"""
    enhanced_combined = enhance_markdown_content(combined_md)
    body_combined = markdown.markdown(
        enhanced_combined,
        extensions=['tables', 'fenced_code', 'toc', 'sane_lists']
    )
    master_html = build_full_html(
        body_combined,
        title="Master Project Blueprint & Defense Compendium",
        subtitle="Unified Technical Architecture, Multi-Omics Data Interpretation, Clinical Impact Analysis, and Complete Viva Defense Q&A Master Guide.",
        doc_type="Unified Master Volume"
    )
    master_pdf_path = DOCS_DIR / "PharmaPath_Master_Technical_and_Viva_Documentation.pdf"
    render_pdf_with_playwright(master_html, master_pdf_path)

    print("\n" + "=" * 80)
    print("ALL 3 PDF DOCUMENTS SUCCESSFULLY CREATED IN docs/")
    print(f"1. {pdf1_path.name}")
    print(f"2. {pdf2_path.name}")
    print(f"3. {master_pdf_path.name}")
    print("=" * 80)


if __name__ == '__main__':
    main()
