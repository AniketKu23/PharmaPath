"""PharmaPath Streamlit Page 6: Drug Comparison.

Two-Drug Comparative Network Pharmacology, Menche Separation s_AB, and Combination Synergy.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
tables_dir = ROOT_DIR / "results" / "tables"
figures_dir = ROOT_DIR / "results" / "figures"

st.set_page_config(page_title="Drug Comparison | PharmaPath", page_icon="⚖️", layout="wide")

st.title("⚖️ Two-Drug Comparison: Metformin vs. Imatinib")
st.markdown("""
Cross-modality comparative network pharmacology evaluating interactome overlap, topological module separation,  
and combination therapy mechanisms connecting cellular metabolism to oncogenic signaling.
""")

st.markdown("---")

# Summary Comparison Metrics
st.subheader("1. Modality Overlap & Topological Separation Benchmark")
comp_summary_file = tables_dir / "two_drug_comparison_summary.csv"
if comp_summary_file.exists():
    df_comp = pd.read_csv(comp_summary_file)
    st.dataframe(
        df_comp,
        column_config={
            "Comparison Metric": st.column_config.TextColumn("Metric"),
            "Metformin Count": st.column_config.NumberColumn("Metformin"),
            "Imatinib Count": st.column_config.NumberColumn("Imatinib"),
            "Shared Count": st.column_config.NumberColumn("Shared Count"),
            "Jaccard Index": st.column_config.NumberColumn("Jaccard Index", format="%.4f"),
            "Detail / Interpretation": st.column_config.TextColumn("Biological Interpretation"),
        },
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")

# Comparison Visualizations
st.subheader("2. Comparative Figures & Cross-Talk Hubs")
col_fig1, col_fig2 = st.columns(2)

with col_fig1:
    fig1_path = figures_dir / "two_drug_jaccard_comparison.png"
    if fig1_path.exists():
        st.image(Image.open(fig1_path), caption="Topological & Biological Overlap (Jaccard Index)", use_column_width=True)

with col_fig2:
    fig2_path = figures_dir / "shared_cross_talk_proteins.png"
    if fig2_path.exists():
        st.image(Image.open(fig2_path), caption="Top Shared Interactome Cross-Talk Proteins", use_column_width=True)

st.markdown("---")

# Shared Proteins Table
st.subheader("3. Shared Subnetwork Cross-Talk Proteins")
shared_proteins_file = tables_dir / "shared_subnetwork_proteins_2hop.csv"
if not shared_proteins_file.exists():
    shared_proteins_file = tables_dir / "shared_subnetwork_proteins.csv"

if shared_proteins_file.exists():
    df_shared = pd.read_csv(shared_proteins_file)
    st.write(f"Total Shared Interactome Nodes: **{len(df_shared)}** (within 2-hop interactome scaffold):")
    st.dataframe(
        df_shared.head(25),
        column_config={
            "gene_symbol": st.column_config.TextColumn("Gene Symbol"),
            "full_ppi_degree": st.column_config.NumberColumn("Full PPI Degree"),
            "metformin_degree": st.column_config.NumberColumn("Metformin Subnetwork Degree"),
            "imatinib_degree": st.column_config.NumberColumn("Imatinib Subnetwork Degree"),
            "metformin_betweenness": st.column_config.NumberColumn("Metformin Betweenness", format="%.5f"),
            "imatinib_betweenness": st.column_config.NumberColumn("Imatinib Betweenness", format="%.5f"),
            "is_shared_hub": st.column_config.CheckboxColumn("Shared Hub?"),
            "is_shared_bottleneck": st.column_config.CheckboxColumn("Shared Bottleneck?"),
        },
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")

# Combination Pharmacology Report
st.subheader("4. Combination Pharmacology & Clinical Rationale")
comb_rep_path = tables_dir / "combination_pharmacology_report.md"
if comb_rep_path.exists():
    st.markdown(comb_rep_path.read_text(encoding="utf-8"))
