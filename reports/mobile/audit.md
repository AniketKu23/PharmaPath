# PharmaPath Mobile UX & Usability Audit (Phase 1 Baseline)

**Date**: 2026-10-12  
**Auditor**: Senior Front-End / Bioinformatics UX Engineer  
**Scope**: Streamlit Web Application (`app/streamlit_app.py` and `app/pages/*.py`)  
**Target Viewports Audited**:
1. Mobile Narrow: **360 × 640 px** (Android base, e.g., Samsung Galaxy S-series / Moto G)
2. Mobile Standard (iPhone): **390 × 844 px** (Apple iPhone 12 / 13 / 14)
3. Mobile Large (Max): **430 × 932 px** (Apple iPhone 14 / 15 / 16 Pro Max)
4. Tablet Portrait: **768 × 1024 px** (Apple iPad Mini / Air portrait)
5. Desktop Baseline: **1280 × 800 px** (Laptop reference baseline)

**Baseline Screenshot Repository**: `reports/mobile/before/` (35 captures across all 7 pages and 5 viewports).  
**Empirical Diagnostics Log**: `reports/mobile/before/audit_metrics.json`.

---

## 1. Executive Summary

An empirical front-end audit was executed across all 7 core pages of the PharmaPath platform using automated Playwright browser tests and manual visual inspection. While the desktop experience at 1280×800 is fully functional, the current presentation layer suffers from critical mobile usability failures on screen widths under 768px.

### Key Metrics Summary
| Metric / Check | Desktop (1280px) | Tablet (768px) | Mobile (360–430px) | Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Interactive Tap Targets < 44×44 px** | 92.9% | 100.0% | **95.5% – 100.0%** | **Major** |
| **PyVis Canvas Touch Scroll Hijacking** | N/A (Mouse) | Problematic | **Severe Trapping** | **Blocker** |
| **PyVis Graph Height vs Viewport** | 83.7% | 65.4% | **104.7% (Taller than screen)** | **Blocker** |
| **Initial Sidebar Overlay Block** | Clean | Clean | **Blocks 85% of Screen** | **Blocker** |
| **Sidebar Filter Discoverability** | Fully Visible | Hidden Hamburger | **Hidden / Unnoticed** | **Major** |
| **4-Column Metric Grids** | Clean row | Squeezed row | **Vertical Scroll Wall (4 stacked)** | **Major** |
| **ASCII Architecture Diagram Overflow** | Fits (646px) | Fits (646px) | **Horizontal Blowout (>360px)** | **Major** |
| **Dataframe Mobile Usability** | Full table | Horizontal scroll | **Illegible / virtual scroll traps**| **Major** |
| **iOS Auto-Zoom on Form Inputs (<16px font)** | N/A | None | **Triggered on input focus** | **Minor** |

---

## 2. Findings Grouped by Severity

### 🔴 Blocker Issues (Must Fix for Mobile Usability)

#### 1. PyVis Subnetwork Iframe Scroll Hijacking & Touch Trapping (`1_Drug_Explorer.py`)
- **Location**: `app/pages/1_Drug_Explorer.py:95` (`components.html(html_graph, height=670, scrolling=False)`)
- **Problem**: 
  - On touch devices, Vis.js captures all `touchstart`, `touchmove`, and `touchend` events inside the iframe canvas for panning and pinching. 
  - Because the iframe width is 100% and height is fixed at 670px (which exceeds the entire 640px height of a 360×640 phone), a user scrolling down the page with their thumb touches inside the graph canvas. The page scroll instantly freezes, and the graph pans indefinitely. The user cannot scroll past the graph without finding a tiny border margin.
  - Furthermore, Vis.js hover tooltips (`title` attribute) fail on touchscreens; mobile users cannot inspect node annotations (degree, betweenness, expression $z$-score).
- **Impact**: Mobile users become physically trapped on the graph and cannot view the Node Inspector table below it.

#### 2. Initial Sidebar State Overlaying Mobile Screen (`streamlit_app.py`)
- **Location**: `app/streamlit_app.py:22` (`initial_sidebar_state="expanded"`)
- **Problem**: 
  - On viewports < 640px, Streamlit renders the sidebar as an absolute drawer overlaying the screen. With `initial_sidebar_state="expanded"`, loading the web app on a phone immediately covers 85% of the viewport with the navigation drawer, obscuring the title, intro, and key metrics. The user must manually locate and tap `<<` to see the actual page.
- **Impact**: Immediate bounce rate; users believe the landing page is blank or broken.

---

### 🟠 Major Issues (Impairs Core Functionality & Accessibility)

#### 3. Tap Target Dimensions Violating Accessibility Standards (< 44×44 px)
- **Location**: All pages (`st.button`, `st.selectbox`, `st.radio`, `st.slider`, `st.tabs`, `st.expander`)
- **Problem**:
  - Empirical measurement in `audit_metrics.json` reveals that **95.5% to 100%** of interactive elements across mobile viewports fail the WCAG 2.5.5 / 2.5.8 touch target guideline of at least 44×44 CSS pixels.
  - Streamlit's default radio buttons, dropdown chips, slider handles, and navigation pills have heights between 28px and 38px and horizontal paddings under 8px, leading to frequent mis-taps on phone touchscreens.
- **Impact**: High frustration, mis-clicks on drug selection (switching Metformin vs Imatinib), and difficulty toggling subnetwork methods.

#### 4. Filter Invisibility on Mobile (Hidden in Sidebar)
- **Location**: All pages (`app/pages/1_Drug_Explorer.py`, `2_Pathways.py`, `3_Network_Metrics.py`, `4_Disease_Proximity.py`)
- **Problem**:
  - On screens $\le 768\text{px}$, Streamlit collapses the sidebar behind a tiny floating hamburger button (`>>`).
  - Essential scientific parameters (Drug selector, STRING score threshold, RWR vs 2-Hop, FDR $q$-value cutoff, Community resolution) are hidden in this drawer with zero visual cues on the page that filters exist or are currently active.
- **Impact**: Users assume the page is static and cannot figure out how to view Imatinib or adjust cutoffs.

#### 5. Cramped 4-Column Metric Grids & Stacking Walls
- **Location**:
  - `app/streamlit_app.py:34` (`col1, col2, col3, col4 = st.columns(4)`)
  - `app/pages/1_Drug_Explorer.py:72` (`kpi1, kpi2, kpi3, kpi4 = st.columns(4)`)
  - `app/pages/3_Network_Metrics.py:52` (`m1, m2, m3, m4 = st.columns(4)`)
  - `app/pages/4_Disease_Proximity.py:77` (`c1, c2, c3, c4 = st.columns(4)`)
- **Problem**:
  - On phones (< 640px), Streamlit collapses 4 columns into a single vertical column, producing an uncomfortably tall scroll wall (four full vertical cards before any substantive chart or visualization).
  - On tablets (768px), 4 columns are crammed into narrow vertical strips where labels wrap awkwardly and delta values collide.
- **Impact**: Suboptimal vertical hierarchy and poor glanceability on mobile.

#### 6. Horizontal Blowout from Fixed-Width ASCII Pipeline Diagram (`streamlit_app.py`)
- **Location**: `app/streamlit_app.py:54-72`
- **Problem**:
  - The ASCII pipeline architecture diagram inside `st.code()` is 76 characters wide (646px computed rendered width).
  - On 360px and 390px viewports, this causes horizontal scrolling or clipping of the code block.
- **Impact**: Visual degradation on the landing page.

#### 7. Dataframe Overflow and Virtual Scroll Conflicts
- **Location**: 
  - `1_Drug_Explorer.py` (Node Inspector - 7 columns)
  - `2_Pathways.py` (Enrichment Results - 8 columns)
  - `4_Disease_Proximity.py` (Guney Proximity Results - 6 columns)
  - `5_Link_Predictions.py` (Top-20 Novel Predictions - 6 columns)
- **Problem**:
  - Streamlit's Glide Data Grid (`dvn-stack`) creates virtualized canvas tables with internal horizontal scroll bars that conflict with vertical mobile scrolling and hide critical findings (e.g. adjusted p-values or prediction confidence) off-screen.
- **Impact**: Tables require tedious horizontal pinching/swiping on mobile screens.

#### 8. Dense Subgraph Physics on Mobile Battery & CPU
- **Location**: `1_Drug_Explorer.py`
- **Problem**:
  - Defaulting to 100 or 150 nodes with continuous Barnes-Hut physics simulation causes high CPU utilization, rapid battery drain, and thermal throttling on mobile devices.
- **Impact**: Choppy frame rates (<15 FPS) and sluggish browser performance on phones.

---

### 🟡 Minor Issues (Polishing & Polish Refinements)

#### 9. iOS Safari Viewport Auto-Zoom on Input Focus
- **Location**: Inputs and text boxes.
- **Problem**: Font sizes under 16px cause iOS Safari to automatically zoom in on the input field when focused, forcing the user to manually pinch-zoom out to regain full-page context.
- **Impact**: Disorienting user experience on iOS.

#### 10. Lack of Safe-Area Inset Support for Notched Devices
- **Location**: Global container margins.
- **Problem**: App content does not specify `env(safe-area-inset-*)`, causing content or floating hamburger buttons to collide with device status bars, dynamic islands, or home indicator bars.
- **Impact**: Visual clipping on modern iPhones and Android edge displays.

#### 11. Plotly Chart Legends Crowding Narrow Viewports
- **Location**: Scatter plots and histograms on `3_Network_Metrics.py` and `4_Disease_Proximity.py`.
- **Problem**: Right-aligned legends take up 120-160px of the plot area, leaving less than 200px for the actual scatter plot or histogram on a 360px phone.
- **Impact**: Chart points and axis ticks become illegible.

---

## 3. Page-by-Page Audit Matrix

| Page | Viewport Tested | Issues Observed | Recommended Remediation |
| :--- | :--- | :--- | :--- |
| **Overview** (`/`) | 360×640, 390×844, 430×932, 768×1024, 1280×800 | • Initial sidebar drawer blocks page<br>• 4-col metrics stack vertically<br>• ASCII diagram 646px wide<br>• Validation table needs scroll | • Set `initial_sidebar_state="collapsed"`<br>• Convert metrics to responsive 2×2 grid<br>• Responsive ASCII container or SVG card<br>• Mobile-optimized table |
| **Drug Explorer** (`/Drug_Explorer`) | 360×640, 390×844, 430×932, 768×1024, 1280×800 | • 670px iframe traps scrolling<br>• 100 nodes too dense<br>• Hover tooltips fail on touch<br>• Controls hidden in sidebar | • Top `Filters` expander on mobile<br>• Height 60vh; touch scroll-lock toggle<br>• Mobile node cap (60 nodes)<br>• Tap-to-inspect detail card below graph |
| **Pathways** (`/Pathways`) | 360×640, 390×844, 430×932, 768×1024, 1280×800 | • Two-column split [1, 2] cramps tablet<br>• Dotplot labels truncated on mobile<br>• Filters in sidebar hidden | • Stack columns on $\le 768$px<br>• Responsive Plotly margins/orientation<br>• Top collapsible filter expander |
| **Network Metrics** (`/Network_Metrics`) | 360×640, 390×844, 430×932, 768×1024, 1280×800 | • 4 metric cards stack vertically<br>• Degree vs Betweenness scatter cramped<br>• Right-aligned legend squashes chart | • 2×2 metric grid on mobile<br>• Responsive Plotly chart with bottom legend<br>• Tabs for communities vs scatter |
| **Disease Proximity** (`/Disease_Proximity`) | 360×640, 390×844, 430×932, 768×1024, 1280×800 | • 4 metric cards stack into scroll wall<br>• Null distribution histograms narrow<br>• Drug toggle in sidebar | • Top filter toggle<br>• 2×2 metric layout<br>• Stacked full-width Plotly charts |
| **Link Predictions** (`/Link_Predictions`) | 360×640, 390×844, 430×932, 768×1024, 1280×800 | • GNN model benchmark table horizontal scroll<br>• Top-20 candidate table wide on mobile | • Select key columns for mobile view<br>• Add CSV download button<br>• Expandable candidate cards |
| **Drug Comparison** (`/Drug_Comparison`) | 360×640, 390×844, 430×932, 768×1024, 1280×800 | • 2-column chart row [1, 1] narrow on tablet<br>• Shared target table clipped | • Stack chart columns on $\le 768$px<br>• Clean responsive table display |

---

## 4. Phase-by-Phase Remediation Roadmap

Based on this audit, we will execute Phases 2 through 8 in strict sequence:

1. **Phase 2: Layout & Navigation**
   - Change `initial_sidebar_state="collapsed"` on mobile; refine `layout="wide"`.
   - Provide a top collapsible `st.expander("⚙️ Controls & Filters", expanded=False)` on mobile so users don't have to hunt in the sidebar.
   - Implement responsive metric grids (2-per-row on mobile, 4-in-a-row on desktop).
   - Responsive formatting for ASCII / code blocks.

2. **Phase 3: Responsive Styling (`app/ui/styles.py` & `app/static/mobile.css`)**
   - Media queries for `max-width: 640px` and `max-width: 1024px`.
   - Enforce $\ge 16$px font on inputs to prevent iOS auto-zoom.
   - Enforce $\ge 44$px touch targets on buttons, selects, sliders, and expanders.
   - Safe-area insets (`env(safe-area-inset-top)` / `env(safe-area-inset-bottom)`).
   - WCAG AA contrast compliance in light and dark modes.

3. **Phase 4: Mobile-Friendly Graph Visualization**
   - Viewport detection / Mobile Mode toggle.
   - Cap nodes server-side on mobile (e.g. top 60 nodes) with informative notification.
   - Set graph height to 60vh on mobile; disable physics after rapid stabilization (100 iterations) to save battery.
   - Add touch-friendly scroll prevention / drag toggle overlay and tap-to-inspect node details card.
   - Provide fallback high-degree node list table.

4. **Phase 5: Responsive Tables & Charts**
   - Truncate / select high-priority columns for mobile dataframes.
   - Add one-click CSV download buttons.
   - Plotly chart adjustments: dynamic margins, bottom-oriented legends, horizontal bar orientation where labels are long.

5. **Phase 6 & 7: Usability, Accessibility & Performance**
   - Caching with `st.cache_data`.
   - Colorblind-safe palettes (Blue / McLaren Orange / Light Grey).
   - Semantic HTML tags and accessibility labels.

6. **Phase 8: Verification & Automated Regression Testing**
   - Capture all 35 after-screenshots in `reports/mobile/after/`.
   - Run automated Playwright assertion test `tests/test_mobile_ui.py`.
   - Confirm pipeline results and file hashes remain 100% untouched.
