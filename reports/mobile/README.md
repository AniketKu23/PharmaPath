# PharmaPath Mobile & Responsive UX Optimization Report

## Executive Summary

This report documents the mobile front-end and UX optimization of the **PharmaPath** Streamlit application across mobile phones (360–430px width), tablets (768–1024px width), and desktop workstations (1280×800px baseline). All presentation-layer enhancements were achieved **without modifying any scientific results, pipeline code, or data files in `results/`** (verified via Git status and file hash integrity).

---

## 1. Audited & Verified Viewports

Testing and screenshot capture were conducted programmatically via Playwright across 5 standardized viewports for all 7 application pages (35 baseline before-captures and 35 verified after-captures):

| Viewport Profile | Dimensions | Device Class Represented | Status |
| :--- | :--- | :--- | :--- |
| **Mobile Narrow** | `360 × 640 px` | Android Baseline (Samsung Galaxy S-series, Moto G) | ✅ Passed (0px overflow) |
| **Mobile Standard** | `390 × 844 px` | Apple iPhone 12 / 13 / 14 / 15 / 16 | ✅ Passed (0px overflow) |
| **Mobile Large** | `430 × 932 px` | Apple iPhone Pro Max / Plus & Large Android | ✅ Passed (0px overflow) |
| **Tablet Portrait** | `768 × 1024 px`| Apple iPad Mini / Air (Portrait) | ✅ Passed (0px overflow) |
| **Desktop Baseline** | `1280 × 800 px`| Laptop / Desktop Reference Baseline | ✅ Passed (No regression) |

---

## 2. Before vs. After Usability Benchmark

| Feature / Inspection Item | Before Optimization | After Optimization | Impact & Resolution |
| :--- | :--- | :--- | :--- |
| **Initial Mobile Sidebar Drawer** | Blocks 85% of mobile screen (`initial_sidebar_state="expanded"`) | Clean collapsed drawer (`initial_sidebar_state="collapsed"`) | Users immediately see title, key findings, and content without manual dismissal. |
| **Filter Discoverability** | Buried in hidden sidebar drawer behind hamburger icon `>>` | Top collapsible `st.expander("⚙️ Controls & Filters")` on all pages | Parameter controls (Drug, RWR vs 2-Hop, Thresholds) are prominently accessible. |
| **PyVis Canvas Touch Trapping** | Canvas captures touch drags; user gets trapped scrolling past graph | Toggleable Pan Lock button (`🔒 Page Scroll Lock` vs `🔓 Pan: Active`) | User can freely scroll up/down past the interactive graph without touch interception. |
| **Graph Height on Mobile** | Fixed 670px (104% of 360×640 screen height) | Dynamic 460px (~60% viewport height) | Balanced aspect ratio suitable for handheld mobile orientation. |
| **Mobile Graph Node Density** | 100–150 nodes with continuous physics (high battery & GPU load) | Server-side capped to top 60 nodes; physics freezes after 100 steps | Eliminates mobile thermal throttling and frame jitter; preserves battery. |
| **Node Inspection on Touch** | Mouse-hover tooltip only (`title` attribute fails on touchscreens) | Tap-to-Inspect Card directly beneath canvas | Tapping any node displays Gene Symbol, Target Status, Degree, and $z$-score. |
| **Low-Bandwidth Fallback** | None; heavy HTML/WebGL canvas forced on all devices | Segmented toggle: `Interactive Graph Canvas` vs `Low-Bandwidth List View` | High-performance tabular alternative for slow mobile data connections. |
| **KPI Metrics Grid** | Squeezed 4 columns into narrow vertical stack wall | Responsive 2-per-row grid (`render_metric_grid`) | Clean 2×2 layout on mobile/tablet; 4-in-a-row on desktop. |
| **ASCII Workflow Diagram** | Fixed 646px preformatted code causing horizontal blowout | Wrapped in `.pp-ascii-container` with smooth touch scroll | Prevents page-width blowout while preserving monospace alignment. |
| **Tables & Dataframes** | Wide virtualized Glide Data Grids with hidden columns off-screen | `render_responsive_dataframe`: Priority columns + `Show All` toggle + CSV export | Instant glanceability of key columns plus one-click data export. |
| **Tap Target Dimensions** | 95.5% – 100% of interactive widgets under 44×44px | Enforced $\ge 44\times 44$px touch padding via `mobile.css` | Conforms to WCAG 2.5.5 / 2.5.8 accessibility standards. |
| **iOS Auto-Zoom on Inputs** | Font size < 16px triggered viewport auto-zoom on iOS | Enforced `font-size: 16px !important` on all inputs | Eliminates disorientation caused by iOS focus zooming. |
| **Navigation on Long Pages** | Long manual vertical scrolling back to top | Persistent floating `Back to Top` button on every page | Fast one-tap return to the top navigation header. |

---

## 3. Architecture & Modular Implementation

All improvements are cleanly isolated into dedicated presentation modules in `app/ui/` and `app/static/`:

1. **`app/static/mobile.css`**:
   - Clean, consolidated stylesheet targeting `@media (max-width: 640px)` and `@media (min-width: 641px) and (max-width: 1024px)`.
   - Incorporates `env(safe-area-inset-top)` and `env(safe-area-inset-bottom)` for notched phones and home indicator bars.
   - Enforces WCAG AA contrast standards ($\ge 4.5:1$) in both light and dark operating system modes.
   - Pinned to Streamlit version `1.65.0` in `requirements.txt`.

2. **`app/ui/styles.py`**:
   - Safe CSS injector (`inject_mobile_styles()`).
   - Responsive metric card grid renderer (`render_metric_grid()`).
   - Monospace diagram container (`render_ascii_box()`).
   - Persistent scroll-to-top button (`render_back_to_top()`).

3. **`app/ui/layout.py`**:
   - Standardized page initializer (`init_page()`).
   - Mobile-first filter expander (`render_filter_expander()`).
   - Responsive dataframe wrapper with column pruning and CSV export (`render_responsive_dataframe()`).
   - Plotly chart formatting helper (`format_plotly_figure()`).

4. **`app/ui/graph.py`**:
   - Server-side subnetwork trimming (`get_subnetwork_limits()`, `generate_mobile_subnetwork_html()`).
   - Touch drag lock/unlock overlay controls.
   - Vis.js physics freeze upon stabilization to conserve battery.
   - Tap-to-inspect node details bottom card.
   - Strips broken relative PyVis script bindings to eliminate 404 syntax errors.

5. **`config/params.yaml`**:
   - Added configurable mobile limits under `subnetwork.mobile` (`max_nodes: 60`, `physics_stabilization_iterations: 100`, `height_vh: 60`).

---

## 4. Verification & Automated Quality Assurance

### Automated Mobile Test (`tests/test_mobile_ui.py`)
A comprehensive Playwright test was integrated into the continuous test suite. At mobile viewport (390×844 px), the test:
1. Navigates to all 7 pages (`/`, `/Drug_Explorer`, `/Pathways`, `/Network_Metrics`, `/Disease_Proximity`, `/Link_Predictions`, `/Drug_Comparison`).
2. Interacts with at least one control per page (toggling views, opening expanders, switching tabs, clicking back-to-top).
3. Verifies zero horizontal overflow (`scrollWidth <= innerWidth + 1`).
4. Verifies zero unhandled JavaScript runtime exceptions (`len(js_errors) == 0`).

**Test Execution Result**:
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 7 items

tests/test_graph.py::test_extract_largest_connected_component PASSED     [ 14%]
tests/test_leakage.py::test_link_split_zero_leakage PASSED               [ 28%]
tests/test_mapping.py::test_load_protein_to_gene_map PASSED              [ 42%]
tests/test_mobile_ui.py::test_mobile_pages_no_overflow_and_no_js_errors PASSED [ 57%]
tests/test_proximity.py::test_compute_closest_distance PASSED            [ 71%]
tests/test_proximity.py::test_proximity_permutation_significance PASSED  [ 85%]
tests/test_proximity.py::test_compute_network_separation PASSED          [100%]

======================= 7 passed, 2 warnings in 45.87s ========================
```

### Scientific Results & Data Integrity
- Git status check: `git status --porcelain results/` produced **0 modifications**.
- File hashes across `results/tables/`, `results/models/`, and `results/figures/` remain 100% identical.

---

## 5. Artifacts and Deliverables

- Baseline Audit Report: `reports/mobile/audit.md`
- Baseline Screenshots (35 images across 5 viewports): `reports/mobile/before/`
- Verified After Screenshots (35 images across 5 viewports): `reports/mobile/after/`
- Automated Test Suite: `tests/test_mobile_ui.py`
- Consolidated Mobile Stylesheet: `app/static/mobile.css`
- Responsive UI Architecture: `app/ui/`
