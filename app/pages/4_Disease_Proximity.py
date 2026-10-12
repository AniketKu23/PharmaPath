"""PharmaPath Streamlit Page 4: Disease Proximity.

Guney et al. (2016) Closest-Distance Network Proximity Analytics against 1,000 Degree-Matched Permutations.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from PIL import Image
import streamlit as st

from app.ui.layout import init_page, render_responsive_dataframe
from app.ui.styles import render_back_to_top, render_metric_grid

tables_dir = ROOT_DIR / "results" / "tables"
figures_dir = ROOT_DIR / "results" / "figures"

init_page("Disease Proximity", "🎯")

st.title("🎯 Disease Module Network Proximity Analytics")
st.markdown("""
Quantifies whether a drug's targets reside topologically closer to a disease gene module than expected by chance,  
using the **Guney et al. (2016 Nature Communications)** closest-distance measure:

$$\\langle d_c \\rangle = \\frac{1}{|T|} \\sum_{t \\in T} \\min_{s \\in S} d(t, s)$$

Significance is rigorously established against **1,000 degree-matched random node set permutations**, ensuring high-degree hub bias does not inflate statistical significance.
""")

with st.expander("💡 Concept Guide: Guney Closest-Distance $d_c$ & 1,000 Degree-Matched Permutations", expanded=False):
    st.markdown("""
    - **Closest Distance $\\langle d_c \\rangle$**: Measures the average shortest path distance from each drug target $t \\in T$ to the nearest disease gene $s \\in S$.
    - **Why Degree-Matched Permutations?**: In scale-free interactomes, high-degree hubs sit close to all proteins simply due to connectivity. Testing against uniform random nodes causes **hub bias**. Degree matching ensures that the random null sets have the exact same connectivity profile as the real drug targets.
    - **Z-Score & Specificity**:
      $$z = \\frac{\\langle d_c \\rangle - \\mu_{\\text{null}}}{\\sigma_{\\text{null}}}$$
      A large negative Z-score ($z < -2.0, p < 0.05$) demonstrates that the drug is genuinely situated inside the disease module. Positive Z-scores against negative-control indications prove high disease specificity.
    """)

st.markdown("---")

# Summary Table
prox_csv = tables_dir / "proximity_summary.csv"
if prox_csv.exists():
    df_prox = pd.read_csv(prox_csv)
    st.subheader("Statistical Proximity Benchmark (Primary Context vs. Negative Controls)")
    key_prox_cols = ["drug", "disease", "observed_d_c", "z_score", "p_value", "verdict"]
    render_responsive_dataframe(
        df_prox,
        key_columns=key_prox_cols,
        download_filename="proximity_summary.csv",
        key_prefix="prox_table",
    )
else:
    st.error("Proximity summary file not found.")

st.markdown("---")

# Detailed Pair Analysis & Permutation Histograms
st.subheader("Null Permutation Distributions & Localization")
drug_select = st.selectbox(
    "Inspect Disease Module Distribution:",
    ["Metformin → Type 2 Diabetes", "Imatinib → Chronic Myeloid Leukemia"],
    key="prox_select_drug",
)

if "Metformin" in drug_select:
    img_path = figures_dir / "proximity_metformin_t2d.png"
    stat_obs = "0.213"
    stat_null = "1.012 ± 0.044"
    stat_z = "-18.28"
    stat_p = "0.0010"
    interp = "Metformin targets are situated directly inside/adjacent to the Type 2 Diabetes module in the interactome (z = -18.28). In contrast, against the negative control (CML), Metformin has z = +18.32 (p = 1.0), demonstrating strong disease specificity."
else:
    img_path = figures_dir / "proximity_imatinib_cml.png"
    stat_obs = "0.400"
    stat_null = "1.228 ± 0.114"
    stat_z = "-7.25"
    stat_p = "0.0010"
    interp = "Imatinib targets form a tight topological module directly proximate to the Chronic Myeloid Leukemia gene set (z = -7.25). Against Type 2 Diabetes, Imatinib has z = +1.18 (p = 0.965), confirming genuine on-target disease proximity."

# Responsive Metric Cards (2x2 on mobile, 4x1 on desktop)
prox_kpis = [
    {"label": "Observed Distance (d_c)", "value": stat_obs},
    {"label": "Null Mean ± Std", "value": stat_null},
    {"label": "Proximity Z-Score", "value": stat_z},
    {"label": "Empirical P-Value", "value": stat_p},
]
render_metric_grid(prox_kpis)

st.info(f"**Biological Interpretation**: {interp}")

if img_path.exists():
    img = Image.open(img_path)
    st.image(img, caption=f"Permutation Null Distribution (1,000 Degree-Matched Samples): {drug_select}", width=None)

render_back_to_top()
