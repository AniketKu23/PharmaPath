"""Mobile-Optimized Graph Visualization Utilities for PharmaPath."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import networkx as nx
import pandas as pd
from pyvis.network import Network

from app.ui.layout import load_app_params


def get_subnetwork_limits(is_mobile: bool = False) -> tuple[int, int]:
    """Retrieve max nodes and default height based on mobile status and params.yaml."""
    params = load_app_params()
    sub_cfg = params.get("subnetwork", {})
    mobile_cfg = sub_cfg.get("mobile", {})

    if is_mobile:
        max_nodes = mobile_cfg.get("max_nodes", 60)
        height_px = 460
    else:
        max_nodes = sub_cfg.get("rwr", {}).get("top_n", 150)
        height_px = 650

    return max_nodes, height_px


def generate_mobile_subnetwork_html(
    G_sub: nx.Graph,
    centrality_df: Optional[pd.DataFrame] = None,
    size_metric: str = "degree_centrality",
    edge_score_threshold: int = 700,
    max_nodes: int = 60,
    height_px: int = 460,
    is_mobile: bool = False,
) -> tuple[str, int, int, bool]:
    """Build an interactive PyVis HTML canvas with mobile touch controls and node inspection.

    Returns
    -------
    tuple of (html_content, total_nodes, total_edges, was_truncated)
    """
    total_nodes_orig = G_sub.number_of_nodes()
    nodes_to_include = list(G_sub.nodes())
    was_truncated = False

    # Server-side pruning: prioritize drug seed targets + highest-degree nodes
    if len(nodes_to_include) > max_nodes:
        was_truncated = True
        deg_map = dict(G_sub.degree())
        target_nodes = [n for n in nodes_to_include if G_sub.nodes[n].get("is_target", False)]
        other_nodes = [n for n in nodes_to_include if not G_sub.nodes[n].get("is_target", False)]
        other_nodes = sorted(other_nodes, key=lambda n: deg_map.get(n, 0), reverse=True)
        remaining_slots = max(0, max_nodes - len(target_nodes))
        nodes_to_include = list(set(target_nodes + other_nodes[:remaining_slots]))

    sub = G_sub.subgraph(nodes_to_include).copy()

    # Pre-parse centrality lookups
    cent_lookup = {}
    if centrality_df is not None and hasattr(centrality_df, "iterrows"):
        for _, row in centrality_df.iterrows():
            g = row["gene_symbol"]
            cent_lookup[g] = row.to_dict()

    canvas_height = f"{height_px}px"
    net = Network(
        height=canvas_height,
        width="100%",
        bgcolor="#0F172A",
        font_color="#F8FAFC",
        directed=False,
    )
    net.force_atlas_2based(
        gravity=-50,
        central_gravity=0.015,
        spring_length=90,
        spring_strength=0.08,
    )

    # Add nodes with custom metadata for touch tap inspection
    for node in sub.nodes():
        node_attr = sub.nodes[node]
        is_target = bool(node_attr.get("is_target", False))
        expr_z = float(node_attr.get("lincs_score", node_attr.get("expression_z_score", 0.0)))
        comm_id = node_attr.get("community_id", "N/A")

        if is_target:
            color = "#F59E0B"  # Amber Gold for Seed Target
            shape = "star"
        elif expr_z >= 1.0:
            color = "#EF4444"  # Up-regulated Red
            shape = "dot"
        elif expr_z <= -1.0:
            color = "#10B981"  # Down-regulated Green
            shape = "dot"
        else:
            color = "#3B82F6"  # Interactome Scaffold Blue
            shape = "dot"

        c_info = cent_lookup.get(node, {})
        val = c_info.get(size_metric, 0.0)
        deg = sub.degree(node)

        if size_metric == "raw_degree":
            node_size = max(12, min(36, 12 + deg * 0.8))
        elif size_metric == "betweenness_centrality":
            node_size = max(12, min(36, 12 + float(val) * 350.0))
        elif size_metric == "eigenvector_centrality":
            node_size = max(12, min(36, 12 + float(val) * 80.0))
        else:
            node_size = max(12, min(36, 12 + float(val) * 150.0))

        if is_target:
            node_size = max(node_size, 26)

        title = (
            f"Gene: {node} | "
            f"Role: {'Primary Target' if is_target else 'Neighbor'} | "
            f"Degree: {deg} | "
            f"Expression z: {expr_z:.2f}"
        )

        net.add_node(
            node,
            label=node,
            title=title,
            color=color,
            size=node_size,
            shape=shape,
            font={"size": 13, "color": "#F8FAFC", "face": "system-ui, -apple-system, sans-serif"},
            # Custom properties for mobile click inspector
            role="Primary Target" if is_target else "Interactome Neighbor",
            degree=deg,
            expr_z=f"{expr_z:.3f}",
            betweenness=f"{float(c_info.get('betweenness_centrality', 0.0)):.5f}",
            eigenvector=f"{float(c_info.get('eigenvector_centrality', 0.0)):.4f}",
            is_hub="Yes" if c_info.get("is_hub", False) else "No",
            is_bottleneck="Yes" if c_info.get("is_bottleneck", False) else "No",
        )

    # Add edges
    edges_added = 0
    for u, v, d in sub.edges(data=True):
        score = int(d.get("score", 700))
        if score < edge_score_threshold:
            continue
        edge_width = max(1.2, (score - 700) / 70.0)
        net.add_edge(u, v, value=edge_width, title=f"STRING Score: {score}", color="#475569")
        edges_added += 1

    # Physics stabilization (rapid 100 iterations to save battery)
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -65,
          "centralGravity": 0.015,
          "springLength": 95,
          "springConstant": 0.08,
          "damping": 0.4
        },
        "solver": "forceAtlas2Based",
        "stabilization": {"iterations": 100}
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "zoomView": true,
        "dragView": true
      }
    }
    """)

    raw_html = net.generate_html()

    # Strip broken relative PyVis binding script that causes 404 syntax error in Streamlit
    raw_html = raw_html.replace('<script src="lib/bindings/utils.js"></script>', '')

    # Inject mobile touch lock bar, recenter button, and tap inspector panel
    injected_js = """
    <style>
      body { margin: 0; padding: 0; overflow: hidden; background: #0F172A; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
      #control-bar {
        position: absolute;
        top: 10px;
        left: 10px;
        right: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 99;
        pointer-events: none;
      }
      .ctrl-btn {
        pointer-events: auto;
        background: rgba(30, 41, 59, 0.9);
        color: #F8FAFC;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      }
      .ctrl-btn:active {
        background: #FF8000;
      }
      #node-card {
        position: absolute;
        bottom: 10px;
        left: 10px;
        right: 10px;
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 8px 12px;
        color: #F8FAFC;
        font-size: 12px;
        z-index: 99;
        display: flex;
        flex-wrap: wrap;
        gap: 8px 16px;
        align-items: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
      }
      .badge-target {
        background: #F59E0B;
        color: #000;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
      }
      .badge-neighbor {
        background: #3B82F6;
        color: #FFF;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
      }
    </style>

    <div id="control-bar">
      <button class="ctrl-btn" id="btn-recenter" onclick="resetGraphView()">🎯 Recenter</button>
      <button class="ctrl-btn" id="btn-toggle-pan" onclick="togglePanDrag()">🔓 Pan: Active</button>
    </div>

    <div id="node-card">
      <span style="opacity: 0.8;">💡 Tap any node to inspect details</span>
    </div>

    <script type="text/javascript">
      let panActive = true;
      function resetGraphView() {
        if (typeof network !== 'undefined') {
          network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
        }
      }

      function togglePanDrag() {
        panActive = !panActive;
        const btn = document.getElementById('btn-toggle-pan');
        if (panActive) {
          btn.innerHTML = '🔓 Pan: Active';
          btn.style.borderColor = '#475569';
          network.setOptions({ interaction: { dragView: true, dragNodes: true, zoomView: true } });
        } else {
          btn.innerHTML = '🔒 Page Scroll Lock';
          btn.style.borderColor = '#FF8000';
          network.setOptions({ interaction: { dragView: false, dragNodes: false, zoomView: false } });
        }
      }

      // Freeze physics after stabilization to preserve battery
      if (typeof network !== 'undefined') {
        network.on("stabilizationIterationsDone", function () {
          network.setOptions({ physics: false });
        });

        // Tap inspection
        network.on("click", function (params) {
          if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const nodeData = nodes.get(nodeId);
            if (nodeData) {
              const isSeed = nodeData.role === "Primary Target";
              const badgeClass = isSeed ? "badge-target" : "badge-neighbor";
              document.getElementById("node-card").innerHTML = `
                <div style="font-weight: 700; font-size: 14px; color: #FFF; display: flex; align-items: center; gap: 6px;">
                  <span>${nodeId}</span>
                  <span class="${badgeClass}">${nodeData.role}</span>
                </div>
                <div><b>Deg:</b> ${nodeData.degree}</div>
                <div><b>LINCS z:</b> ${nodeData.expr_z}</div>
                <div><b>Betweenness:</b> ${nodeData.betweenness}</div>
                <div><b>Hub/Bridge:</b> ${nodeData.is_hub === "Yes" ? "Hub" : ""}${nodeData.is_bottleneck === "Yes" ? "/Bottleneck" : "Scaffold"}</div>
              `;
            }
          }
        });
      }
    </script>
    """

    # Inject into HTML right before </body>
    if "</body>" in raw_html:
        final_html = raw_html.replace("</body>", f"{injected_js}</body>")
    else:
        final_html = raw_html + injected_js

    return final_html, sub.number_of_nodes(), edges_added, was_truncated
