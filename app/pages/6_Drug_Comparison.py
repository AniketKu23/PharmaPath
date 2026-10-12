"""PharmaPath Streamlit Page 6: Drug Comparison.

Two-Drug Comparative Network Pharmacology, Menche Separation s_AB, and Combination Synergy.
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
from app.ui.styles import render_back_to_top

tables_dir = ROOT_DIR / "results" / "tables"
figures_dir = ROOT_DIR / "results" / "figures"

init_page("Drug Comparison", "⚖️")

st.title("⚖️ Two-Drug Comparison: Metformin vs. Imatinib")
st.markdown("""
Cross-modality comparative network pharmacology evaluating interactome overlap, topological module separation,  
and combination therapy mechanisms connecting cellular metabolism to oncogenic signaling.
""")

st.markdown("---")

tab_metrics, tab_figs, tab_shared, tab_rationale = st.tabs([
    "📊 Overlap & Separation",
    "🖼️ Comparative Visualizations",
    "🧬 Shared Cross-Talk Proteins",
    "💊 Combination Therapy Rationale",
])

with tab_metrics:
    st.subheader("1. Modality Overlap & Topological Separation Benchmark")
    comp_summary_file = tables_dir / "two_drug_comparison_summary.csv"
    if comp_summary_file.exists():
        df_comp = pd.read_csv(comp_summary_file)
        render_responsive_dataframe(
            df_comp,
            key_columns=["Comparison Metric", "Metformin Count", "Imatinib Count", "Shared Count", "Jaccard Index"],
            download_filename="two_drug_comparison_summary.csv",
            key_prefix="comp_summary",
        )

with tab_figs:
    st.subheader("2. Comparative Figures & Cross-Talk Hubs")
    fig1_path = figures_dir / "two_drug_jaccard_comparison.png"
    if fig1_path.exists():
        st.image(Image.open(fig1_path), caption="Topological & Biological Overlap (Jaccard Index)", width=None)

    fig2_path = figures_dir / "shared_cross_talk_proteins.png"
    if fig2_path.exists():
        st.image(Image.open(fig2_path), caption="Top Shared Interactome Cross-Talk Proteins", width=None)

with tab_shared:
    st.subheader("3. Shared Subnetwork Cross-Talk Proteins")
    shared_proteins_file = tables_dir / "shared_subnetwork_proteins_2hop.csv"
    if not shared_proteins_file.exists():
        shared_proteins_file = tables_dir / "shared_subnetwork_proteins.csv"

    if shared_proteins_file.exists():
        df_shared = pd.read_csv(shared_proteins_file)
        st.write(f"Total Shared Interactome Nodes: **{len(df_shared)}** (within 2-hop interactome scaffold):")
        key_shared_cols = ["gene_symbol", "metformin_degree", "imatinib_degree", "is_shared_hub", "is_shared_bottleneck"]
        render_responsive_dataframe(
            df_shared.head(50),
            key_columns=[c for c in key_shared_cols if c in df_shared.columns],
            download_filename="shared_cross_talk_proteins.csv",
            key_prefix="comp_shared",
        )

with tab_rationale:
    st.subheader("4. Combination Pharmacology & Clinical Rationale")
    comb_rep_path = tables_dir / "combination_pharmacology_report.md"
    if comb_rep_path.exists():
        st.markdown(comb_rep_path.read_text(encoding="utf-8"))

render_back_to_top()
