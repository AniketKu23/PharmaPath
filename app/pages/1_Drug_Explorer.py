"""PharmaPath Streamlit Page 1: Drug Explorer.

Interactive Subnetwork Visualization using PyVis with mobile touch optimizations.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from app.ui.graph import generate_mobile_subnetwork_html, get_subnetwork_limits
from app.ui.layout import init_page, render_filter_expander, render_responsive_dataframe
from app.ui.styles import render_back_to_top, render_metric_grid

init_page("Drug Explorer", "🔭")

st.title("🔭 Interactive Drug Subnetwork Explorer")
st.markdown("""
Extract and explore drug-perturbed human interactome subnetworks.  
- **Node Colors**: 🌟 **Gold Star** = Seed Drug Target | 🔴 **Red** = Up-regulated ($z > 1.0$) | 🟢 **Green** = Down-regulated ($z < -1.0$) | 🔵 **Blue** = Interactome Scaffold Neighbor.  
- **Node Size**: Proportional to topological centrality.
""")

# Persistent Filters Expander (accessible without needing sidebar on mobile)
with render_filter_expander("⚙️ Subnetwork Controls & Filters", "Customize drug, extraction method & thresholds"):
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        drug_choice = st.selectbox("Select Drug:", ["Metformin", "Imatinib"], index=0, key="de_drug")
        method_choice = st.radio(
            "Extraction Method:",
            ["Random Walk with Restart (RWR, r=0.5)", "2-Hop Interactome Neighborhood"],
            index=0,
            key="de_method",
        )
    with fcol2:
        size_metric = st.selectbox(
            "Node Sizing Metric:",
            [
                ("degree_centrality", "Degree Centrality"),
                ("betweenness_centrality", "Betweenness Centrality (Bottlenecks)"),
                ("eigenvector_centrality", "Eigenvector Centrality (Influence)"),
                ("raw_degree", "Raw Degree"),
            ],
            format_func=lambda x: x[1],
            key="de_metric",
        )[0]
        edge_threshold = st.slider("Edge STRING Score Threshold:", min_value=700, max_value=950, value=700, step=25, key="de_edge_thresh")

drug_id = drug_choice.lower()
method_id = "rwr" if "RWR" in method_choice else "2hop"

# Load Subnetwork & Centrality
data_proc_dir = ROOT_DIR / "data" / "processed"
tables_dir = ROOT_DIR / "results" / "tables"

graphml_path = data_proc_dir / f"subnetwork_{drug_id}_{method_id}.graphml"
cent_path = tables_dir / f"centrality_{drug_id}_{method_id}.csv"

if not graphml_path.exists():
    st.error(f"Subnetwork file {graphml_path} not found. Please run pipeline first.")
    st.stop()


@st.cache_data
def load_graph_and_cent(g_path: str, c_path: str):
    G = nx.read_graphml(g_path)
    df = pd.read_csv(c_path) if Path(c_path).exists() else None
    return G, df


G_sub, cent_df = load_graph_and_cent(str(graphml_path), str(cent_path))

# Summary KPI Grid (2x2 on mobile, 4x1 on desktop)
target_count = sum(1 for _, d in G_sub.nodes(data=True) if d.get("is_target", False))
kpi_data = [
    {"label": "Subnetwork Nodes", "value": f"{G_sub.number_of_nodes():,}"},
    {"label": "Subnetwork Edges", "value": f"{G_sub.number_of_edges():,}"},
    {"label": "Graph Density", "value": f"{nx.density(G_sub):.4f}"},
    {"label": "Seed Targets Present", "value": f"{target_count} ({drug_choice})"},
]
render_metric_grid(kpi_data)

st.markdown("---")

# View Controls: Mobile Optimization & Low Bandwidth Fallback
ctrl_col1, ctrl_col2 = st.columns([3, 2])
with ctrl_col1:
    is_mobile_mode = st.toggle("📱 Mobile Optimization Mode", value=True, help="Caps rendered nodes to top 60, quick physics stop to save battery, and touch drag controls.")
with ctrl_col2:
    view_type = st.radio("Display Mode:", ["Interactive Graph Canvas", "Low-Bandwidth List View"], horizontal=True)

max_nodes_cfg, height_cfg = get_subnetwork_limits(is_mobile=is_mobile_mode)

if view_type == "Interactive Graph Canvas":
    st.markdown("### Interactive Subgraph Visualization")
    with st.spinner("Rendering responsive subnetwork canvas..."):
        html_graph, rendered_nodes, rendered_edges, was_truncated = generate_mobile_subnetwork_html(
            G_sub=G_sub,
            centrality_df=cent_df,
            size_metric=size_metric,
            edge_score_threshold=edge_threshold,
            max_nodes=max_nodes_cfg,
            height_px=height_cfg,
            is_mobile=is_mobile_mode,
        )

        if was_truncated:
            st.info(f"📱 Rendered top {rendered_nodes} most central nodes (server-side trimmed from {G_sub.number_of_nodes()} nodes) to preserve mobile battery and frame rate. Primary drug targets are fully preserved.")

        components.html(html_graph, height=height_cfg + 30, scrolling=False)

else:
    st.markdown("### 📋 Subnetwork Node Directory (Low Bandwidth)")
    if cent_df is not None:
        st.write("Lightweight tabular view of nodes ranked by degree and centrality.")
        targets_in_sub = [n for n, d in G_sub.nodes(data=True) if d.get("is_target", False)]
        list_df = cent_df.copy()
        list_df["is_seed_target"] = list_df["gene_symbol"].isin(targets_in_sub)
        render_responsive_dataframe(
            list_df,
            key_columns=["gene_symbol", "is_seed_target", "degree_centrality", "is_hub", "is_bottleneck"],
            download_filename=f"{drug_id}_{method_id}_nodes.csv",
            key_prefix="de_list_view",
        )

# Tabular Inspector Section
st.markdown("---")
st.markdown("### Subnetwork Node Inspector & Centralities")
if cent_df is not None:
    search_term = st.text_input("Filter by Gene Symbol:", "", key="de_gene_search")
    display_df = cent_df.copy()
    if search_term:
        display_df = display_df[display_df["gene_symbol"].str.contains(search_term.upper(), na=False)]

    targets_in_sub = [n for n, d in G_sub.nodes(data=True) if d.get("is_target", False)]
    display_df["is_seed_target"] = display_df["gene_symbol"].isin(targets_in_sub)

    key_inspect_cols = ["gene_symbol", "is_seed_target", "raw_degree", "degree_centrality", "is_hub", "is_bottleneck"]
    render_responsive_dataframe(
        display_df,
        key_columns=key_inspect_cols,
        download_filename=f"{drug_id}_{method_id}_centrality.csv",
        key_prefix="de_inspector",
    )

render_back_to_top()
