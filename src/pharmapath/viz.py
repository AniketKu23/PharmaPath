"""Visualization module for PharmaPath.

Provides:
- PyVis interactive HTML network generation with custom styles, tooltips, and color mappings.
- Matplotlib/Seaborn static figures for academic reports and exports.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx
from pyvis.network import Network

logger = logging.getLogger(__name__)


def create_pyvis_subnetwork(
    G_sub: nx.Graph,
    centrality_df: Optional[Any] = None,
    size_metric: str = "degree_centrality",
    edge_score_threshold: int = 700,
    max_nodes: int = 150,
    height: str = "650px",
    width: str = "100%",
) -> str:
    """Generate an interactive PyVis HTML snippet for a subnetwork.

    Node aesthetics:
    - Color:
        * Gold / Yellow (#F39C12) if direct drug target
        * Crimson / Red (#E74C3C) if positive expression change (z-score > 1.0)
        * Emerald / Green (#27AE60) if negative expression change (z-score < -1.0)
        * Steel Blue (#2980B9) default interactome neighbor
    - Size: scaled by selected centrality metric
    - Tooltip: detailed biological attributes
    """
    net = Network(height=height, width=width, bgcolor="#1E1E2F", font_color="#FFFFFF", directed=False)
    net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100, spring_strength=0.08)

    # Filter to top max_nodes by degree if subnetwork is larger
    nodes_to_include = list(G_sub.nodes())
    if len(nodes_to_include) > max_nodes:
        deg_map = dict(G_sub.degree())
        # Always preserve targets
        target_nodes = [n for n in nodes_to_include if G_sub.nodes[n].get("is_target", False)]
        other_nodes = [n for n in nodes_to_include if not G_sub.nodes[n].get("is_target", False)]
        other_nodes = sorted(other_nodes, key=lambda n: deg_map.get(n, 0), reverse=True)
        nodes_to_include = list(set(target_nodes + other_nodes[: (max_nodes - len(target_nodes))]))

    sub = G_sub.subgraph(nodes_to_include).copy()

    # Pre-parse centralities if dataframe supplied
    cent_lookup = {}
    if centrality_df is not None and hasattr(centrality_df, "iterrows"):
        for _, row in centrality_df.iterrows():
            g = row["gene_symbol"]
            cent_lookup[g] = row.to_dict()

    for node in sub.nodes():
        node_attr = sub.nodes[node]
        is_target = node_attr.get("is_target", False)
        expr_z = float(node_attr.get("lincs_score", node_attr.get("expression_z_score", 0.0)))
        comm_id = node_attr.get("community_id", "N/A")

        # Color mapping
        if is_target:
            color = "#F39C12"  # Amber Gold for Seed Target
            shape = "star"
        elif expr_z >= 1.0:
            color = "#E74C3C"  # Up-regulated (Red)
            shape = "dot"
        elif expr_z <= -1.0:
            color = "#2ECC71"  # Down-regulated (Green)
            shape = "dot"
        else:
            color = "#3498DB"  # Neutral interactome neighbor (Blue)
            shape = "dot"

        # Centrality sizing
        c_info = cent_lookup.get(node, {})
        val = c_info.get(size_metric, 0.0)
        deg = sub.degree(node)

        if size_metric == "raw_degree":
            node_size = max(10, min(35, 10 + deg * 0.8))
        elif size_metric == "betweenness_centrality":
            node_size = max(10, min(35, 10 + float(val) * 350.0))
        elif size_metric == "eigenvector_centrality":
            node_size = max(10, min(35, 10 + float(val) * 80.0))
        else:
            node_size = max(10, min(35, 10 + float(val) * 150.0))

        if is_target:
            node_size = max(node_size, 25)

        # Tooltip HTML
        title = (
            f"<b>Gene:</b> {node}<br>"
            f"<b>Role:</b> {'Primary Drug Target' if is_target else 'Interactome Neighbor'}<br>"
            f"<b>Degree (Subnetwork):</b> {deg}<br>"
            f"<b>Community ID:</b> {comm_id}<br>"
            f"<b>LINCS Expression z:</b> {expr_z:.3f}<br>"
            f"<b>Betweenness:</b> {float(c_info.get('betweenness_centrality', 0.0)):.5f}<br>"
            f"<b>Eigenvector:</b> {float(c_info.get('eigenvector_centrality', 0.0)):.4f}"
        )

        net.add_node(
            node,
            label=node,
            title=title,
            color=color,
            size=node_size,
            shape=shape,
            font={"size": 12, "color": "#FFFFFF", "face": "arial"},
        )

    # Add edges
    for u, v, d in sub.edges(data=True):
        score = int(d.get("score", 700))
        if score < edge_score_threshold:
            continue
        weight = float(d.get("weight", score / 1000.0))
        edge_width = max(1.0, (score - 700) / 75.0)
        net.add_edge(u, v, value=edge_width, title=f"STRING Score: {score}", color="#555577")

    # Options for physics
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -60,
          "centralGravity": 0.015,
          "springLength": 90,
          "springStrength": 0.08,
          "damping": 0.4
        },
        "solver": "forceAtlas2Based",
        "stabilization": {"iterations": 150}
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """)

    html_content = net.generate_html()
    return html_content
