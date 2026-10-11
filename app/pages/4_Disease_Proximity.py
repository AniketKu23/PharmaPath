"""PharmaPath Streamlit Page 4: Disease Proximity.

Guney et al. (2016) Closest-Distance Network Proximity Analytics against 1,000 Degree-Matched Permutations.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
tables_dir = ROOT_DIR / "results" / "tables"
figures_dir = ROOT_DIR / "results" / "figures"

st.set_page_config(page_title="Disease Proximity | PharmaPath", page_icon="🎯", layout="wide")

st.title("🎯 Disease Module Network Proximity Analytics")
st.markdown("""
Quantifies whether a drug's targets reside topologically closer to a disease gene module than expected by chance,  
using the **Guney et al. (2016 Nature Communications)** closest-distance measure:

$$\\langle d_c \\rangle = \\frac{1}{|T|} \\sum_{t \\in T} \\min_{s \\in S} d(t, s)$$

Significance is rigorously established against **1,000 degree-matched random node set permutations**, ensuring high-degree hub bias does not inflate statistical significance.
""")

st.markdown("---")

# Summary Table
prox_csv = tables_dir / "proximity_summary.csv"
if prox_csv.exists():
    df_prox = pd.read_csv(prox_csv)

    st.subheader("Statistical Proximity Benchmark (Primary Context vs. Negative Controls)")
    st.dataframe(
        df_prox,
        column_config={
            "drug": st.column_config.TextColumn("Drug"),
            "disease": st.column_config.TextColumn("Disease Module"),
            "is_primary_context": st.column_config.CheckboxColumn("Primary Indication?"),
            "observed_d_c": st.column_config.NumberColumn("Observed d_c", format="%.3f"),
            "mean_null_d_c": st.column_config.NumberColumn("Null Mean d_c", format="%.3f"),
            "z_score": st.column_config.NumberColumn("Z-Score", format="%.2f"),
            "p_value": st.column_config.NumberColumn("Empirical P-Value", format="%.4f"),
            "verdict": st.column_config.TextColumn("Verdict"),
        },
        use_container_width=True,
        hide_index=True,
    )
else:
    st.error("Proximity summary file not found.")

st.markdown("---")

# Detailed Pair Analysis & Permutation Histograms
st.subheader("Null Permutation Distributions & Localization")
drug_select = st.selectbox("Inspect Primary Disease Distribution:", ["Metformin → Type 2 Diabetes", "Imatinib → Chronic Myeloid Leukemia"])

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

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Observed Closest Distance (d_c)", stat_obs)
with c2:
    st.metric("Null Model Mean ± Std", stat_null)
with c3:
    st.metric("Proximity Z-Score", stat_z)
with c4:
    st.metric("Empirical P-Value", stat_p)

st.info(f"**Biological Interpretation**: {interp}")

if img_path.exists():
    img = Image.open(img_path)
    st.image(img, caption=f"Permutation Null Distribution (1,000 Degree-Matched Samples): {drug_select}", use_column_width=True)
