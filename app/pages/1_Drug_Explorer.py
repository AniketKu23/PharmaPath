"""PharmaPath Streamlit Page 1: Drug Explorer.

Interactive Subnetwork Visualization using PyVis.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from pharmapath.viz import create_pyvis_subnetwork

st.set_page_config(page_title="Drug Explorer | PharmaPath", page_icon="🔭", layout="wide")

st.title("🔭 Interactive Drug Subnetwork Explorer")
st.markdown("""
Extract and explore drug-perturbed human interactome subnetworks server-side.  
- **Node Color**: 🌟 **Gold Star** = Seed Drug Target | 🔴 **Red** = Up-regulated ($z > 1.0$) | 🟢 **Green** = Down-regulated ($z < -1.0$) | 🔵 **Blue** = Interactome Scaffold Neighbor.  
- **Node Size**: Proportional to topological centrality.  
- **Hover**: Inspect gene symbol, degree, betweenness, expression z-score, and community assignment.
""")

# Sidebar Controls
st.sidebar.header("Subnetwork Controls")
drug_choice = st.sidebar.selectbox("Select Drug:", ["Metformin", "Imatinib"], index=0)
drug_id = drug_choice.lower()

method_choice = st.sidebar.radio(
    "Extraction Method:",
    ["Random Walk with Restart (RWR, r=0.5)", "2-Hop Interactome Neighborhood"],
    index=0,
)
method_id = "rwr" if "RWR" in method_choice else "2hop"

size_metric = st.sidebar.selectbox(
    "Node Sizing Metric:",
    [
        ("degree_centrality", "Degree Centrality"),
        ("betweenness_centrality", "Betweenness Centrality (Bottlenecks)"),
        ("eigenvector_centrality", "Eigenvector Centrality (Influence)"),
        ("raw_degree", "Raw Degree"),
    ],
    format_func=lambda x: x[1],
)[0]

edge_threshold = st.sidebar.slider("Edge STRING Score Threshold:", min_value=700, max_value=950, value=700, step=25)
max_nodes = st.sidebar.slider("Max Nodes Rendered:", min_value=25, max_value=200, value=100, step=25)

# Load Subnetwork & Centrality
data_proc_dir = ROOT_DIR / "data" / "processed"
tables_dir = ROOT_DIR / "results" / "tables"

graphml_path = data_proc_dir / f"subnetwork_{drug_id}_{method_id}.graphml"
cent_path = tables_dir / f"centrality_{drug_id}_{method_id}.csv"

if not graphml_path.exists():
    st.error(f"Subnetwork file {graphml_path} not found. Please run pipeline first.")
    st.stop()

G_sub = nx.read_graphml(graphml_path)
cent_df = pd.read_csv(cent_path) if cent_path.exists() else None

# Summary KPI Columns
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
target_count = sum(1 for _, d in G_sub.nodes(data=True) if d.get("is_target", False))

with kpi1:
    st.metric("Subnetwork Nodes", G_sub.number_of_nodes())
with kpi2:
    st.metric("Subnetwork Edges", G_sub.number_of_edges())
with kpi3:
    st.metric("Graph Density", f"{nx.density(G_sub):.4f}")
with kpi4:
    st.metric("Seed Targets Present", target_count)

# Render PyVis Graph
st.markdown("### Interactive Subgraph Visualization")
with st.spinner("Generating interactive subnetwork canvas..."):
    html_graph = create_pyvis_subnetwork(
        G_sub=G_sub,
        centrality_df=cent_df,
        size_metric=size_metric,
        edge_score_threshold=edge_threshold,
        max_nodes=max_nodes,
        height="650px",
    )
    components.html(html_graph, height=670, scrolling=False)

# Tabular Inspector
st.markdown("### Subnetwork Node Inspector & Centralities")
if cent_df is not None:
    search_term = st.text_input("Filter by Gene Symbol:", "")
    display_df = cent_df.copy()
    if search_term:
        display_df = display_df[display_df["gene_symbol"].str.contains(search_term.upper(), na=False)]

    # Highlight seed targets
    targets_in_sub = [n for n, d in G_sub.nodes(data=True) if d.get("is_target", False)]
    display_df["is_seed_target"] = display_df["gene_symbol"].isin(targets_in_sub)

    cols = [
        "gene_symbol", "is_seed_target", "raw_degree", "degree_centrality",
        "betweenness_centrality", "eigenvector_centrality", "is_hub", "is_bottleneck"
    ]
    st.dataframe(
        display_df[[c for c in cols if c in display_df.columns]],
        use_container_width=True,
        hide_index=True,
    )
