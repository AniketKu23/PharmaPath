"""
Drug Subnetwork Extraction module for PharmaPath.
Implements:
1. k-hop neighborhood expansion (default: 2-hop) with degree-based pruning if graph explodes.
2. Random Walk with Restart (RWR, restart prob r=0.5) using personalized PageRank.
3. Comparative subnetwork topology analysis.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import networkx as nx
import numpy as np
import pandas as pd

from pharmapath.config import get_project_root, load_params

logger = logging.getLogger(__name__)


def get_seed_nodes_in_graph(G: nx.Graph, target_genes: List[str] | Set[str]) -> List[str]:
    """Filter target gene list to those present in graph G."""
    present = [g for g in target_genes if g in G]
    if not present:
        raise ValueError("None of the specified target genes are present in the PPI graph!")
    return present


def extract_2hop_subnetwork(
    G: nx.Graph,
    seed_targets: List[str] | Set[str],
    max_hops: int = 2,
    max_nodes: int = 500
) -> Tuple[nx.Graph, pd.DataFrame, Dict[str, Any]]:
    """
    Extract k-hop neighborhood induced subnetwork around drug targets.
    Annotates hop distance for each node.
    """
    seeds = set(get_seed_nodes_in_graph(G, seed_targets))
    
    current_layer = set(seeds)
    visited = set(seeds)
    node_hop_dict: Dict[str, int] = {s: 0 for s in seeds}

    for hop in range(1, max_hops + 1):
        next_layer = set()
        for node in current_layer:
            for nbr in G.neighbors(node):
                if nbr not in visited:
                    visited.add(nbr)
                    next_layer.add(nbr)
                    node_hop_dict[nbr] = hop
        current_layer = next_layer

    # If the 2-hop neighborhood is very large, prioritize top nodes connected to seeds
    selected_nodes = visited
    pruned = False
    if len(selected_nodes) > max_nodes:
        pruned = True
        logger.info(f"2-hop neighborhood has {len(selected_nodes)} nodes; pruning to top {max_nodes} by seed-affinity...")
        # Score nodes by number of connections to seeds/layer-1
        seed_connection_scores = {}
        for n in selected_nodes:
            if n in seeds:
                seed_connection_scores[n] = 9999
            else:
                seed_connection_scores[n] = sum(1 for nbr in G.neighbors(n) if nbr in seeds) * 10 + G.degree(n)
        
        sorted_nodes = sorted(selected_nodes, key=lambda n: seed_connection_scores[n], reverse=True)
        selected_nodes = set(sorted_nodes[:max_nodes])

    sub_G = G.subgraph(selected_nodes).copy()
    
    # Node metadata
    rows = []
    for n in sub_G.nodes():
        rows.append({
            "gene_symbol": n,
            "hop_distance": node_hop_dict.get(n, max_hops),
            "is_seed": n in seeds,
            "degree": sub_G.degree(n),
            "full_graph_degree": G.degree(n)
        })
    df_nodes = pd.DataFrame(rows).sort_values(by=["hop_distance", "degree"], ascending=[True, False])

    stats = {
        "method": "2-hop neighborhood",
        "seed_count": len(seeds),
        "total_nodes": sub_G.number_of_nodes(),
        "total_edges": sub_G.number_of_edges(),
        "density": nx.density(sub_G),
        "pruned": pruned,
        "is_connected": nx.is_connected(sub_G),
        "num_components": nx.number_connected_components(sub_G),
    }

    logger.info(
        f"Extracted 2-hop subnetwork: {stats['total_nodes']} nodes, {stats['total_edges']} edges, "
        f"density={stats['density']:.4f}"
    )
    return sub_G, df_nodes, stats


def extract_rwr_subnetwork(
    G: nx.Graph,
    seed_targets: List[str] | Set[str],
    restart_prob: float = 0.5,
    top_n: int = 150
) -> Tuple[nx.Graph, pd.DataFrame, Dict[str, Any]]:
    """
    Extract Random Walk with Restart (RWR) subnetwork using personalized PageRank.
    restart_prob = 0.5 means alpha = 1.0 - 0.5 = 0.5.
    Seeds receive uniform personalization probability 1.0 / |S|.
    """
    seeds = set(get_seed_nodes_in_graph(G, seed_targets))
    
    # Personalization vector
    personalization = {n: 0.0 for n in G.nodes()}
    seed_weight = 1.0 / len(seeds)
    for s in seeds:
        personalization[s] = seed_weight

    # Personalized PageRank
    alpha = 1.0 - restart_prob
    logger.info(f"Computing RWR stationary distribution (restart_prob={restart_prob}, alpha={alpha})...")
    pagerank_scores = nx.pagerank(
        G,
        alpha=alpha,
        personalization=personalization,
        weight="weight",
        max_iter=200,
        tol=1e-6
    )

    # Rank nodes by RWR score
    sorted_nodes = sorted(pagerank_scores.items(), key=lambda kv: kv[1], reverse=True)
    top_node_entries = sorted_nodes[:top_n]
    top_node_set = {n for n, score in top_node_entries}
    
    # Always ensure all seeds are included in RWR subnetwork
    top_node_set.update(seeds)

    sub_G = G.subgraph(top_node_set).copy()

    rows = []
    for rank, (n, score) in enumerate(sorted_nodes, start=1):
        if n in top_node_set:
            rows.append({
                "gene_symbol": n,
                "rwr_score": score,
                "rwr_rank": rank,
                "is_seed": n in seeds,
                "degree": sub_G.degree(n),
                "full_graph_degree": G.degree(n)
            })
    df_nodes = pd.DataFrame(rows).sort_values(by="rwr_score", ascending=False)

    stats = {
        "method": "Random Walk with Restart (RWR)",
        "restart_prob": restart_prob,
        "seed_count": len(seeds),
        "total_nodes": sub_G.number_of_nodes(),
        "total_edges": sub_G.number_of_edges(),
        "density": nx.density(sub_G),
        "is_connected": nx.is_connected(sub_G),
        "num_components": nx.number_connected_components(sub_G),
    }

    logger.info(
        f"Extracted RWR subnetwork: {stats['total_nodes']} nodes, {stats['total_edges']} edges, "
        f"density={stats['density']:.4f}"
    )
    return sub_G, df_nodes, stats


def compare_subnetworks(
    sub_2hop: nx.Graph,
    sub_rwr: nx.Graph,
    drug_name: str
) -> pd.DataFrame:
    """
    Compare 2-hop and RWR subnetwork topologies for a given drug.
    """
    nodes_2hop = set(sub_2hop.nodes())
    nodes_rwr = set(sub_rwr.nodes())

    intersection = nodes_2hop & nodes_rwr
    union = nodes_2hop | nodes_rwr
    jaccard_nodes = len(intersection) / len(union) if union else 0.0

    edges_2hop = set(frozenset((u, v)) for u, v in sub_2hop.edges())
    edges_rwr = set(frozenset((u, v)) for u, v in sub_rwr.edges())
    jaccard_edges = len(edges_2hop & edges_rwr) / len(edges_2hop | edges_rwr) if (edges_2hop | edges_rwr) else 0.0

    metrics = [
        {"metric": "Total Nodes", "2-hop": sub_2hop.number_of_nodes(), "RWR": sub_rwr.number_of_nodes()},
        {"metric": "Total Edges", "2-hop": sub_2hop.number_of_edges(), "RWR": sub_rwr.number_of_edges()},
        {"metric": "Graph Density", "2-hop": f"{nx.density(sub_2hop):.4f}", "RWR": f"{nx.density(sub_rwr):.4f}"},
        {"metric": "Avg Degree", "2-hop": f"{2 * sub_2hop.number_of_edges() / sub_2hop.number_of_nodes():.2f}", "RWR": f"{2 * sub_rwr.number_of_edges() / sub_rwr.number_of_nodes():.2f}"},
        {"metric": "Connected Components", "2-hop": nx.number_connected_components(sub_2hop), "RWR": nx.number_connected_components(sub_rwr)},
        {"metric": "Node Overlap Count", "2-hop": len(intersection), "RWR": len(intersection)},
        {"metric": "Node Jaccard Similarity", "2-hop": f"{jaccard_nodes:.4f}", "RWR": f"{jaccard_nodes:.4f}"},
        {"metric": "Edge Jaccard Similarity", "2-hop": f"{jaccard_edges:.4f}", "RWR": f"{jaccard_edges:.4f}"},
    ]

    df_comp = pd.DataFrame(metrics)
    df_comp["drug"] = drug_name
    return df_comp
