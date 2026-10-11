"""
Network Centrality and Topological Bottleneck Detection Module for PharmaPath.
Computes:
1. Degree Centrality (Hubs: top 5%)
2. Betweenness Centrality (Bottlenecks: top 5%)
3. Closeness Centrality
4. Eigenvector Centrality
"""

import logging
from typing import Any, Dict, List, Set, Tuple
import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_network_centralities(
    G: nx.Graph,
    hub_percentile: float = 0.05,
    bottleneck_percentile: float = 0.05
) -> Tuple[nx.Graph, pd.DataFrame, Dict[str, Any]]:
    """
    Compute degree, betweenness, closeness, and eigenvector centralities.
    Flags hubs (top hub_percentile degree) and bottlenecks (top bottleneck_percentile betweenness).
    """
    n_nodes = G.number_of_nodes()
    if n_nodes < 2:
        raise ValueError("Graph too small for centrality analysis.")

    logger.info(f"Computing centralities for graph with {n_nodes} nodes and {G.number_of_edges()} edges...")

    # Degree Centrality
    deg_cent = nx.degree_centrality(G)
    raw_degrees = dict(G.degree())

    # Betweenness Centrality (normalized)
    bet_cent = nx.betweenness_centrality(G, normalized=True, weight="weight")

    # Closeness Centrality
    close_cent = nx.closeness_centrality(G, distance="weight")

    # Eigenvector Centrality
    try:
        eigen_cent = nx.eigenvector_centrality(G, max_iter=500, tol=1e-5, weight="weight")
    except nx.PowerIterationFailedConvergence:
        logger.warning("Eigenvector centrality power iteration did not converge; falling back to unweighted.")
        try:
            eigen_cent = nx.eigenvector_centrality(G, max_iter=1000, tol=1e-4)
        except Exception:
            eigen_cent = {n: 0.0 for n in G.nodes()}

    # Compute cutoffs
    deg_vals = list(deg_cent.values())
    bet_vals = list(bet_cent.values())

    deg_cutoff = np.percentile(deg_vals, (1.0 - hub_percentile) * 100)
    bet_cutoff = np.percentile(bet_vals, (1.0 - bottleneck_percentile) * 100)

    rows = []
    for n in G.nodes():
        dc = deg_cent[n]
        bc = bet_cent[n]
        cc = close_cent[n]
        ec = eigen_cent.get(n, 0.0)

        is_hub = bool(dc >= deg_cutoff)
        is_bottleneck = bool(bc >= bet_cutoff)
        is_bridge = bool(is_hub and is_bottleneck)

        # Update node attributes in Graph
        G.nodes[n]["degree_centrality"] = float(dc)
        G.nodes[n]["betweenness_centrality"] = float(bc)
        G.nodes[n]["closeness_centrality"] = float(cc)
        G.nodes[n]["eigenvector_centrality"] = float(ec)
        G.nodes[n]["is_hub"] = is_hub
        G.nodes[n]["is_bottleneck"] = is_bottleneck
        G.nodes[n]["is_bridge"] = is_bridge

        rows.append({
            "gene_symbol": n,
            "raw_degree": raw_degrees[n],
            "degree_centrality": dc,
            "betweenness_centrality": bc,
            "closeness_centrality": cc,
            "eigenvector_centrality": ec,
            "is_hub": is_hub,
            "is_bottleneck": is_bottleneck,
            "is_hub_bottleneck_bridge": is_bridge
        })

    df_cent = pd.DataFrame(rows).sort_values(by="betweenness_centrality", ascending=False)

    hubs = df_cent[df_cent["is_hub"]]["gene_symbol"].tolist()
    bottlenecks = df_cent[df_cent["is_bottleneck"]]["gene_symbol"].tolist()
    bridges = df_cent[df_cent["is_hub_bottleneck_bridge"]]["gene_symbol"].tolist()

    stats = {
        "total_nodes": n_nodes,
        "total_edges": G.number_of_edges(),
        "hub_degree_cutoff": float(deg_cutoff),
        "bottleneck_betweenness_cutoff": float(bet_cutoff),
        "num_hubs": len(hubs),
        "num_bottlenecks": len(bottlenecks),
        "num_bridges": len(bridges),
        "top_hubs": hubs[:10],
        "top_bottlenecks": bottlenecks[:10],
        "bridges": bridges[:10]
    }

    logger.info(
        f"Centrality analysis complete: {len(hubs)} hubs, {len(bottlenecks)} bottlenecks, "
        f"{len(bridges)} hub-bottleneck bridges identified."
    )
    return G, df_cent, stats
