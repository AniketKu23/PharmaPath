"""PharmaPath Streamlit Page 3: Network Metrics.

Centrality Analytics, Hub/Bottleneck Identification, and Louvain Community Detection.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from app.ui.layout import init_page, render_filter_expander, render_responsive_dataframe
from app.ui.styles import render_back_to_top, render_metric_grid

tables_dir = ROOT_DIR / "results" / "tables"

init_page("Network Metrics", "🕸️")

st.title("🕸️ Interactome Centrality & Modularity Analytics")
st.markdown("""
Quantify topological centrality roles across drug-perturbed interactome subnetworks:
- **Hubs**: Top 5% degree centrality — highly connected structural centers.
- **Bottlenecks**: Top 5% betweenness centrality — critical bridge nodes controlling multi-pathway information flow.
- **Louvain Communities**: High-modularity functional clusters annotated with dominant biological pathways.
""")

with st.expander("💡 Concept Guide: Topological Hubs, Bottlenecks & Louvain Modularity", expanded=False):
    st.markdown("""
    - **Hubs (Top 5% Degree)**: Proteins with the highest direct physical connections in the interactome. Highly essential structural anchors whose disruption disrupts cellular viability.
    - **Bottlenecks (Top 5% Betweenness)**: Proteins situated on the highest fraction of shortest paths across the interactome. Serve as essential communication bridges and frequently mediate drug resistance or toxicity.
    - **Dual Hub-Bottleneck Bridges**: Rare proteins (top 5% of both degree and betweenness) that act as multi-functional master switches (e.g., `SRC`, `MAPK1`, `TP53`).
    - **Louvain Community Modularity ($Q$)**: Greedy modularity maximization grouping tightly interacting proteins into functional topological communities, each audited for its dominant pathway.
    """)

# Persistent Filters Expander
with render_filter_expander("⚙️ Subnetwork Scope & Filters", "Select drug and subnetwork extraction method"):
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        drug_choice = st.selectbox("Select Drug:", ["Metformin", "Imatinib"], index=0, key="nm_drug")
        drug_id = drug_choice.lower()
    with fcol2:
        method_choice = st.radio("Subnetwork Type:", ["RWR (Top 150)", "2-Hop Neighborhood (Top 500)"], index=0, key="nm_method")
        method_id = "rwr" if "RWR" in method_choice else "2hop"

cent_file = tables_dir / f"centrality_{drug_id}_{method_id}.csv"
comm_file = tables_dir / f"communities_{drug_id}_{method_id}.csv"

if not cent_file.exists():
    st.error(f"Centrality metrics file {cent_file} not found. Please run pipeline first.")
    st.stop()


@st.cache_data
def load_cent_and_comm(c_path: str, m_path: str):
    c_df = pd.read_csv(c_path)
    m_df = pd.read_csv(m_path) if Path(m_path).exists() else None
    return c_df, m_df


cent_df, comm_df = load_cent_and_comm(str(cent_file), str(comm_file))

# Summary KPI Grid (2x2 on mobile, 4x1 on desktop)
hubs_count = cent_df["is_hub"].sum() if "is_hub" in cent_df.columns else 0
bottlenecks_count = cent_df["is_bottleneck"].sum() if "is_bottleneck" in cent_df.columns else 0
bridges_count = (
    cent_df["is_hub_bottleneck_bridge"].sum()
    if "is_hub_bottleneck_bridge" in cent_df.columns
    else 0
)

kpis = [
    {"label": "Total Subnetwork Proteins", "value": f"{len(cent_df):,}"},
    {"label": "Topological Hubs (Top 5%)", "value": str(hubs_count)},
    {"label": "Bottlenecks (Top 5%)", "value": str(bottlenecks_count)},
    {"label": "Dual Hub-Bottleneck Bridges", "value": str(bridges_count)},
]
render_metric_grid(kpis)

st.markdown("---")

# Visual & Tabular Centrality Landscape
st.subheader("Topological Landscape: Degree vs. Betweenness Centrality")

tab_scatter, tab_ranked = st.tabs(["📈 Scatter Profile", "📋 Top Bottleneck & Bridge Table"])

with tab_scatter:
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=120)
    sns.set_theme(style="whitegrid")

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
        "Hub (High Degree)": "#FF8000",
        "Bottleneck (High Betweenness)": "#E74C3C",
        "Standard Node": "#3498DB",
    }

    sns.scatterplot(
        data=cent_df,
        x="raw_degree",
        y="betweenness_centrality",
        hue="Topological Class",
        palette=palette,
        s=55,
        alpha=0.85,
        ax=ax,
    )

    # Label top 4 bottlenecks
    top_labels = cent_df.sort_values(by="betweenness_centrality", ascending=False).head(4)
    for _, r in top_labels.iterrows():
        ax.annotate(
            r["gene_symbol"],
            xy=(r["raw_degree"], r["betweenness_centrality"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8.5,
            fontweight="bold",
        )

    ax.set_title(f"{drug_choice} ({method_id.upper()}): Centrality Profile", fontsize=11, fontweight="bold")
    ax.set_xlabel("Degree (Connections)", fontsize=10)
    ax.set_ylabel("Betweenness Centrality", fontsize=10)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with tab_ranked:
    st.markdown("##### Top Bottlenecks Ranked by Betweenness Centrality")
    ranked_bottlenecks = cent_df.sort_values(by="betweenness_centrality", ascending=False)
    render_responsive_dataframe(
        ranked_bottlenecks,
        key_columns=["gene_symbol", "raw_degree", "betweenness_centrality", "Topological Class"],
        download_filename=f"{drug_id}_{method_id}_bottlenecks.csv",
        key_prefix="nm_bottlenecks",
    )

st.markdown("---")

# Louvain Community Analysis
st.subheader("Louvain Community Detection & Dominant Functional Themes")
if comm_df is not None:
    render_responsive_dataframe(
        comm_df,
        key_columns=["community_id", "size", "dominant_pathway"],
        download_filename=f"{drug_id}_{method_id}_communities.csv",
        key_prefix="nm_communities",
    )
else:
    st.info("Community file not found.")

render_back_to_top()
