"""PharmaPath Streamlit Page 3: Network Metrics.

Centrality Analytics, Hub/Bottleneck Identification, and Louvain Community Detection.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
tables_dir = ROOT_DIR / "results" / "tables"

st.set_page_config(page_title="Network Metrics | PharmaPath", page_icon="🕸️", layout="wide")

st.title("🕸️ Interactome Centrality & Modularity Analytics")
st.markdown("""
Quantify topological centrality roles across drug-perturbed interactome subnetworks:
- **Hubs**: Top 5% degree centrality — highly connected structural centers.
- **Bottlenecks**: Top 5% betweenness centrality — critical bridge nodes controlling multi-pathway information flow.
- **Louvain Communities**: High-modularity functional clusters annotated with dominant biological pathways.
""")

drug_choice = st.sidebar.selectbox("Select Drug:", ["Metformin", "Imatinib"], index=0)
drug_id = drug_choice.lower()
method_choice = st.sidebar.radio("Subnetwork Type:", ["RWR (Top 150)", "2-Hop Neighborhood (Top 500)"], index=0)
method_id = "rwr" if "RWR" in method_choice else "2hop"

cent_file = tables_dir / f"centrality_{drug_id}_{method_id}.csv"
comm_file = tables_dir / f"communities_{drug_id}_{method_id}.csv"

if not cent_file.exists():
    st.error(f"Centrality metrics file {cent_file} not found. Please run pipeline first.")
    st.stop()

cent_df = pd.read_csv(cent_file)

# Summary Counters
hubs_count = cent_df["is_hub"].sum() if "is_hub" in cent_df.columns else 0
bottlenecks_count = cent_df["is_bottleneck"].sum() if "is_bottleneck" in cent_df.columns else 0
bridges_count = (
    cent_df["is_hub_bottleneck_bridge"].sum()
    if "is_hub_bottleneck_bridge" in cent_df.columns
    else 0
)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Subnetwork Proteins", len(cent_df))
with m2:
    st.metric("Topological Hubs (Top 5%)", hubs_count)
with m3:
    st.metric("Bottlenecks (Top 5%)", bottlenecks_count)
with m4:
    st.metric("Dual Hub-Bottleneck Bridges", bridges_count)

st.markdown("---")

# Visual: Degree vs Betweenness Centrality
st.subheader("Topological Landscape: Degree vs. Betweenness Centrality")
col_plot, col_table = st.columns([3, 2])

with col_plot:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.set_theme(style="whitegrid")

    # Determine node category
    def assign_category(row: pd.Series) -> str:
        if row.get("is_hub_bottleneck_bridge", False):
            return "Dual Hub & Bottleneck"
        elif row.get("is_hub", False):
            return "Hub (High Degree)"
        elif row.get("is_bottleneck", False):
            return "Bottleneck (High Betweenness)"
        return "Standard Node"

    cent_df["Topological Class"] = cent_df.apply(assign_category, axis=1)

    palette = {
        "Dual Hub & Bottleneck": "#9B59B6",
        "Hub (High Degree)": "#E67E22",
        "Bottleneck (High Betweenness)": "#E74C3C",
        "Standard Node": "#3498DB",
    }

    sns.scatterplot(
        data=cent_df,
        x="raw_degree",
        y="betweenness_centrality",
        hue="Topological Class",
        palette=palette,
        s=60,
        alpha=0.85,
        ax=ax,
    )

    # Label top bridges/bottlenecks
    top_labels = cent_df.sort_values(by="betweenness_centrality", ascending=False).head(5)
    for _, r in top_labels.iterrows():
        ax.annotate(
            r["gene_symbol"],
            xy=(r["raw_degree"], r["betweenness_centrality"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
        )

    ax.set_title(f"{drug_choice} ({method_id.upper()}): Centrality Profile", fontsize=11, fontweight="bold")
    ax.set_xlabel("Degree (Number of Connections)")
    ax.set_ylabel("Betweenness Centrality")
    st.pyplot(fig)
    plt.close()

with col_table:
    st.markdown("### Top Bottleneck & Bridge Proteins")
    st.dataframe(
        cent_df.sort_values(by="betweenness_centrality", ascending=False)[[
            "gene_symbol", "raw_degree", "betweenness_centrality", "Topological Class"
        ]].head(12),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")

# Louvain Community Analysis
st.subheader("Louvain Community Detection & Dominant Functional Themes")
if comm_file.exists():
    comm_df = pd.read_csv(comm_file)
    st.dataframe(
        comm_df,
        column_config={
            "community_id": st.column_config.NumberColumn("Community ID"),
            "size": st.column_config.NumberColumn("Proteins in Community"),
            "dominant_pathway": st.column_config.TextColumn("Dominant Biological Pathway"),
        },
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Community file not found.")
