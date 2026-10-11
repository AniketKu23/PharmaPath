"""Two-drug comparative network pharmacology module for PharmaPath.

Calculates:
- Jaccard similarity across target sets, extracted subnetworks, enriched pathways, and communities.
- Interactome module separation s_AB (Menche et al., 2015 Science).
- Shared hubs, bottlenecks, and bridge proteins in the PPI scaffold.
- Quantitative synergy and combination pharmacology interpretation.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)


def compute_jaccard(set_a: Set[Any], set_b: Set[Any]) -> Tuple[float, int, int, int]:
    """Calculate Jaccard similarity between two sets.

    Returns:
        (jaccard_index, intersection_size, union_size, difference_a_b_size)
    """
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    if not union:
        return 0.0, 0, 0, 0
    jaccard = len(intersection) / len(union)
    return float(jaccard), len(intersection), len(union), len(set_a - set_b)


def compute_network_separation(
    G: nx.Graph,
    targets_a: List[str],
    targets_b: List[str],
) -> Dict[str, float]:
    """Compute network separation s_AB between two target sets (Menche et al., 2015).

    s_AB = <d_AB> - (<d_AA> + <d_BB>) / 2

    Uses both:
    1. Closest-distance formulation (Guney et al. / Menche et al.):
       <d_AB> = (1 / (|A| + |B|)) * [ sum_{a in A} min_{b in B} d(a,b) + sum_{b in B} min_{a in A} d(a,b) ]
       <d_AA> = (1 / |A|) * sum_{a in A} min_{a' in A, a' != a} d(a, a')
    2. Mean all-pairs shortest path distance formulation.

    Negative s_AB indicates topological overlap / interpenetration.
    Positive s_AB indicates topological separation.
    """
    nodes_a = [n for n in targets_a if n in G]
    nodes_b = [n for n in targets_b if n in G]

    if not nodes_a or not nodes_b:
        logger.warning("Empty target set in graph for separation calculation.")
        return {
            "s_AB_closest": 0.0,
            "d_AB_closest": 0.0,
            "d_AA_closest": 0.0,
            "d_BB_closest": 0.0,
            "s_AB_mean": 0.0,
            "d_AB_mean": 0.0,
            "d_AA_mean": 0.0,
            "d_BB_mean": 0.0,
        }

    # Precompute pairwise distances between all relevant nodes
    all_relevant = list(set(nodes_a + nodes_b))
    dist_map: Dict[str, Dict[str, int]] = {}
    for node in all_relevant:
        lengths = nx.single_source_shortest_path_length(G, node)
        dist_map[node] = lengths

    # 1. Closest-distance within A
    d_aa_closest_vals = []
    for a1 in nodes_a:
        dists = [dist_map[a1][a2] for a2 in nodes_a if a2 != a1 and a2 in dist_map[a1]]
        if dists:
            d_aa_closest_vals.append(min(dists))
        else:
            d_aa_closest_vals.append(0.0)
    d_AA_closest = float(np.mean(d_aa_closest_vals)) if d_aa_closest_vals else 0.0

    # Closest-distance within B
    d_bb_closest_vals = []
    for b1 in nodes_b:
        dists = [dist_map[b1][b2] for b2 in nodes_b if b2 != b1 and b2 in dist_map[b1]]
        if dists:
            d_bb_closest_vals.append(min(dists))
        else:
            d_bb_closest_vals.append(0.0)
    d_BB_closest = float(np.mean(d_bb_closest_vals)) if d_bb_closest_vals else 0.0

    # Closest-distance between A and B
    d_a_to_b = []
    for a in nodes_a:
        dists = [dist_map[a][b] for b in nodes_b if b in dist_map[a]]
        if dists:
            d_a_to_b.append(min(dists))
    d_b_to_a = []
    for b in nodes_b:
        dists = [dist_map[b][a] for a in nodes_a if a in dist_map[b]]
        if dists:
            d_b_to_a.append(min(dists))

    d_AB_closest = (
        float((sum(d_a_to_b) + sum(d_b_to_a)) / (len(d_a_to_b) + len(d_b_to_a)))
        if (len(d_a_to_b) + len(d_b_to_a)) > 0
        else 0.0
    )

    s_AB_closest = d_AB_closest - ((d_AA_closest + d_BB_closest) / 2.0)

    # 2. All-pairs mean shortest path
    all_d_aa = []
    for i, a1 in enumerate(nodes_a):
        for j, a2 in enumerate(nodes_a):
            if i < j and a2 in dist_map[a1]:
                all_d_aa.append(dist_map[a1][a2])
    d_AA_mean = float(np.mean(all_d_aa)) if all_d_aa else 0.0

    all_d_bb = []
    for i, b1 in enumerate(nodes_b):
        for j, b2 in enumerate(nodes_b):
            if i < j and b2 in dist_map[b1]:
                all_d_bb.append(dist_map[b1][b2])
    d_BB_mean = float(np.mean(all_d_bb)) if all_d_bb else 0.0

    all_d_ab = []
    for a in nodes_a:
        for b in nodes_b:
            if b in dist_map[a]:
                all_d_ab.append(dist_map[a][b])
    d_AB_mean = float(np.mean(all_d_ab)) if all_d_ab else 0.0

    s_AB_mean = d_AB_mean - ((d_AA_mean + d_BB_mean) / 2.0)

    return {
        "s_AB_closest": round(s_AB_closest, 4),
        "d_AB_closest": round(d_AB_closest, 4),
        "d_AA_closest": round(d_AA_closest, 4),
        "d_BB_closest": round(d_BB_closest, 4),
        "s_AB_mean": round(s_AB_mean, 4),
        "d_AB_mean": round(d_AB_mean, 4),
        "d_AA_mean": round(d_AA_mean, 4),
        "d_BB_mean": round(d_BB_mean, 4),
        "n_targets_a": len(nodes_a),
        "n_targets_b": len(nodes_b),
    }


def find_shared_and_bridge_proteins(
    G: nx.Graph,
    drug_a: str,
    drug_b: str,
    subgraph_nodes_a: Set[str],
    subgraph_nodes_b: Set[str],
    centrality_df_a: pd.DataFrame,
    centrality_df_b: pd.DataFrame,
    top_n: int = 15,
) -> Dict[str, Any]:
    """Identify shared proteins, shared hubs, and cross-drug bridge nodes."""
    shared_subnetwork_nodes = list(subgraph_nodes_a.intersection(subgraph_nodes_b))

    bridge_col_a = "is_hub_bottleneck_bridge" if "is_hub_bottleneck_bridge" in centrality_df_a.columns else "is_bridge"
    bridge_col_b = "is_hub_bottleneck_bridge" if "is_hub_bottleneck_bridge" in centrality_df_b.columns else "is_bridge"

    deg_col_a = "raw_degree" if "raw_degree" in centrality_df_a.columns else "degree"
    deg_col_b = "raw_degree" if "raw_degree" in centrality_df_b.columns else "degree"

    # Shared hubs
    hubs_a = set(
        centrality_df_a[centrality_df_a.get("is_hub", False) == True]["gene_symbol"].tolist()
    ) if "is_hub" in centrality_df_a.columns else set()
    hubs_b = set(
        centrality_df_b[centrality_df_b.get("is_hub", False) == True]["gene_symbol"].tolist()
    ) if "is_hub" in centrality_df_b.columns else set()
    shared_hubs = list(hubs_a.intersection(hubs_b))

    # Shared bottlenecks
    bottlenecks_a = set(
        centrality_df_a[centrality_df_a.get("is_bottleneck", False) == True]["gene_symbol"].tolist()
    ) if "is_bottleneck" in centrality_df_a.columns else set()
    bottlenecks_b = set(
        centrality_df_b[centrality_df_b.get("is_bottleneck", False) == True]["gene_symbol"].tolist()
    ) if "is_bottleneck" in centrality_df_b.columns else set()
    shared_bottlenecks = list(bottlenecks_a.intersection(bottlenecks_b))

    # Shared bridges
    bridges_a = set(
        centrality_df_a[centrality_df_a.get(bridge_col_a, False) == True]["gene_symbol"].tolist()
    ) if bridge_col_a in centrality_df_a.columns else set()
    bridges_b = set(
        centrality_df_b[centrality_df_b.get(bridge_col_b, False) == True]["gene_symbol"].tolist()
    ) if bridge_col_b in centrality_df_b.columns else set()
    shared_bridges = list(bridges_a.intersection(bridges_b))

    # Rank shared nodes by average degree across both subnetworks
    shared_metrics = []
    for g in shared_subnetwork_nodes:
        deg_in_full = G.degree(g) if g in G else 0
        row_a = centrality_df_a[centrality_df_a["gene_symbol"] == g]
        row_b = centrality_df_b[centrality_df_b["gene_symbol"] == g]
        deg_a = int(row_a[deg_col_a].iloc[0]) if (not row_a.empty and deg_col_a in row_a) else 0
        deg_b = int(row_b[deg_col_b].iloc[0]) if (not row_b.empty and deg_col_b in row_b) else 0
        btw_a = float(row_a["betweenness_centrality"].iloc[0]) if (not row_a.empty and "betweenness_centrality" in row_a) else 0.0
        btw_b = float(row_b["betweenness_centrality"].iloc[0]) if (not row_b.empty and "betweenness_centrality" in row_b) else 0.0

        shared_metrics.append({
            "gene_symbol": g,
            "full_ppi_degree": deg_in_full,
            f"{drug_a}_degree": deg_a,
            f"{drug_b}_degree": deg_b,
            f"{drug_a}_betweenness": round(btw_a, 5),
            f"{drug_b}_betweenness": round(btw_b, 5),
            "is_shared_hub": g in shared_hubs,
            "is_shared_bottleneck": g in shared_bottlenecks,
            "is_shared_bridge": g in shared_bridges,
        })

    shared_df = pd.DataFrame(shared_metrics)
    if not shared_df.empty:
        shared_df = shared_df.sort_values(by="full_ppi_degree", ascending=False)

    return {
        "shared_subnetwork_nodes_count": len(shared_subnetwork_nodes),
        "shared_hubs": shared_hubs,
        "shared_bottlenecks": shared_bottlenecks,
        "shared_bridges": shared_bridges,
        "shared_nodes_df": shared_df,
    }


def compare_pathways(
    pathways_df_a: pd.DataFrame,
    pathways_df_b: pd.DataFrame,
    fdr_threshold: float = 0.05,
) -> Dict[str, Any]:
    """Compare significantly enriched pathways between two drugs."""
    df_a = pathways_df_a.copy()
    df_b = pathways_df_b.copy()

    # Standardize column names
    col_map = {
        "adj_p_value": "adjusted_p_value",
        "Adjusted P-value": "adjusted_p_value",
        "Term": "term",
        "Library": "library",
        "Genes": "genes",
    }
    df_a = df_a.rename(columns=col_map)
    df_b = df_b.rename(columns=col_map)

    sig_a = df_a[df_a["adjusted_p_value"] < fdr_threshold]
    sig_b = df_b[df_b["adjusted_p_value"] < fdr_threshold]

    terms_a = set(sig_a["term"].tolist())
    terms_b = set(sig_b["term"].tolist())

    jaccard, inter_len, union_len, diff_len = compute_jaccard(terms_a, terms_b)
    shared_terms = list(terms_a.intersection(terms_b))

    shared_records = []
    for term in shared_terms:
        row_a = sig_a[sig_a["term"] == term].iloc[0]
        row_b = sig_b[sig_b["term"] == term].iloc[0]
        shared_records.append({
            "term": term,
            "library": row_a.get("library", ""),
            "fdr_drug_a": float(row_a["adjusted_p_value"]),
            "fdr_drug_b": float(row_b["adjusted_p_value"]),
            "genes_drug_a": row_a.get("genes", ""),
            "genes_drug_b": row_b.get("genes", ""),
        })

    shared_df = pd.DataFrame(shared_records)
    if not shared_df.empty:
        shared_df["min_fdr"] = shared_df[["fdr_drug_a", "fdr_drug_b"]].min(axis=1)
        shared_df = shared_df.sort_values(by="min_fdr", ascending=True)

    return {
        "jaccard": round(jaccard, 4),
        "sig_terms_a_count": len(terms_a),
        "sig_terms_b_count": len(terms_b),
        "shared_terms_count": inter_len,
        "shared_pathways_df": shared_df,
    }


def plot_comparison_summary(
    separation_results: Dict[str, Any],
    jaccard_summary: Dict[str, float],
    shared_nodes_df: pd.DataFrame,
    out_dir: Path,
) -> None:
    """Generate visual comparison figures for the two drugs."""
    sns.set_theme(style="whitegrid")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Figure 1: Jaccard Similarities Across Modalities
    fig, ax = plt.subplots(figsize=(8, 5))
    metrics = list(jaccard_summary.keys())
    values = list(jaccard_summary.values())
    colors = ["#3498db", "#2ecc71", "#9b59b6", "#e67e22", "#e74c3c"]

    bars = ax.barh(metrics, values, color=colors[: len(metrics)], edgecolor="black", alpha=0.85)
    for bar in bars:
        w = bar.get_width()
        ax.annotate(
            f"{w:.3f}",
            xy=(w, bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontweight="bold",
            fontsize=10,
        )
    ax.set_xlim(0, max(max(values) * 1.25, 0.4))
    ax.set_title("Topological & Biological Overlap (Jaccard Index): Metformin vs Imatinib", fontsize=12, fontweight="bold")
    ax.set_xlabel("Jaccard Similarity Index")
    plt.tight_layout()
    fig_path = out_dir / "two_drug_jaccard_comparison.png"
    plt.savefig(fig_path, dpi=300)
    plt.close()
    logger.info("Saved comparison Jaccard figure to %s", fig_path)

    # Figure 2: Top Shared Bridge Proteins by Full PPI Degree
    if not shared_nodes_df.empty:
        fig, ax = plt.subplots(figsize=(9, 6))
        top_shared = shared_nodes_df.head(12)
        sns.barplot(
            data=top_shared,
            x="full_ppi_degree",
            y="gene_symbol",
            palette="viridis",
            edgecolor="black",
            ax=ax,
        )
        ax.set_title("Top Shared Cross-Talk Proteins in Interactome Scaffold", fontsize=12, fontweight="bold")
        ax.set_xlabel("Degree Centrality in Human PPI Scaffold")
        ax.set_ylabel("Gene Symbol")
        for p in ax.patches:
            width = p.get_width()
            ax.annotate(
                f"{int(width)}",
                xy=(width, p.get_y() + p.get_height() / 2),
                xytext=(5, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=9,
            )
        plt.tight_layout()
        bridge_path = out_dir / "shared_cross_talk_proteins.png"
        plt.savefig(bridge_path, dpi=300)
        plt.close()
        logger.info("Saved shared cross-talk figure to %s", bridge_path)
