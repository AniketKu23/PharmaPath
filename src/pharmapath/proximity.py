"""
Network Proximity Module for PharmaPath.
Implements the Guney et al. (2016) closest-distance measure between drug targets and disease modules,
evaluated against >= 1000 degree-matched random node set permutations.
"""

from collections import deque
import logging
from typing import Any, Dict, List, Set, Tuple
import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def build_degree_bins(G: nx.Graph) -> Dict[int, List[str]]:
    """
    Bin all nodes in graph G by their degree for degree-matched null model sampling.
    """
    deg_dict = dict(G.degree())
    degree_bins: Dict[int, List[str]] = {}

    for node, deg in deg_dict.items():
        if deg <= 10:
            bin_id = deg
        elif deg <= 50:
            bin_id = (deg // 5) * 5
        elif deg <= 200:
            bin_id = (deg // 20) * 20
        else:
            bin_id = (deg // 100) * 100
        
        degree_bins.setdefault(bin_id, []).append(node)

    return degree_bins


def sample_degree_matched_nodes(
    nodes: List[str],
    G: nx.Graph,
    degree_bins: Dict[int, List[str]],
    rng: np.random.Generator
) -> List[str]:
    """
    Sample a random set of nodes matching the degree distribution of the given node set.
    """
    deg_dict = dict(G.degree())
    sampled = []
    
    for n in nodes:
        deg = deg_dict.get(n, 1)
        if deg <= 10:
            bin_id = deg
        elif deg <= 50:
            bin_id = (deg // 5) * 5
        elif deg <= 200:
            bin_id = (deg // 20) * 20
        else:
            bin_id = (deg // 100) * 100

        bin_nodes = degree_bins.get(bin_id, [n])
        sampled.append(bin_nodes[rng.integers(0, len(bin_nodes))])

    return sampled


def shortest_dist_to_set(target_node: str, target_set: Set[str], adj: Dict[str, Any]) -> int:
    """
    Compute shortest path distance from a single target node to the closest node in target_set.
    Terminates as soon as the first member of target_set is encountered.
    """
    if target_node in target_set:
        return 0

    # Hop 1 check
    nbrs = adj[target_node]
    for nbr in nbrs:
        if nbr in target_set:
            return 1

    # Hop 2+ BFS
    visited = {target_node} | set(nbrs)
    q = deque([(nbr, 1) for nbr in nbrs])

    while q:
        u, d = q.popleft()
        if d >= 6:  # Diameter safeguard
            break
        for v in adj[u]:
            if v in target_set:
                return d + 1
            if v not in visited:
                visited.add(v)
                q.append((v, d + 1))

    return 6


def compute_closest_distance(
    G: nx.Graph,
    drug_targets: List[str] | Set[str],
    disease_genes: List[str] | Set[str]
) -> Tuple[float, Dict[str, int]]:
    """
    Compute Guney et al. closest-distance measure:
    d_c(T, S) = (1 / |T|) * sum_{t in T} min_{s in S} d(t, s)
    Optimized multi-target BFS terminating upon first disease module hit.
    """
    T = [t for t in drug_targets if t in G]
    S_set = set([s for s in disease_genes if s in G])

    if not T or not S_set:
        raise ValueError("Drug targets or disease genes not present in the PPI graph.")

    adj = G._adj
    target_distances = {}
    total_dist = 0

    for t in T:
        d = shortest_dist_to_set(t, S_set, adj)
        target_distances[t] = d
        total_dist += d

    d_c = total_dist / len(T)
    return d_c, target_distances


def calculate_network_proximity(
    G: nx.Graph,
    drug_targets: List[str] | Set[str],
    disease_genes: List[str] | Set[str],
    drug_name: str,
    disease_name: str,
    num_permutations: int = 1000,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Calculate Guney et al. (2016) network proximity d_c with z-score and empirical p-value
    against >= 1000 degree-matched random node permutations.
    """
    T = list(set([t for t in drug_targets if t in G]))
    S = list(set([s for s in disease_genes if s in G]))

    logger.info(
        f"Evaluating network proximity for {drug_name} (|T|={len(T)}) vs "
        f"{disease_name} (|S|={len(S)}) with {num_permutations} permutations..."
    )

    # 1. Observed closest distance
    d_c_obs, target_dist_map = compute_closest_distance(G, T, S)

    # 2. Build degree bins for degree-matched sampling
    degree_bins = build_degree_bins(G)
    rng = np.random.default_rng(random_seed)

    # 3. Permutations
    adj = G._adj
    null_d_c = np.zeros(num_permutations)
    for i in range(num_permutations):
        T_rand = sample_degree_matched_nodes(T, G, degree_bins, rng)
        S_rand_set = set(sample_degree_matched_nodes(S, G, degree_bins, rng))
        tot = sum(shortest_dist_to_set(t, S_rand_set, adj) for t in T_rand)
        null_d_c[i] = tot / len(T_rand)

    mean_null = float(np.mean(null_d_c))
    std_null = float(np.std(null_d_c))

    if std_null == 0.0:
        std_null = 1e-6

    # z-score: z = (d_c - mu) / sigma
    z_score = float((d_c_obs - mean_null) / std_null)

    # Empirical p-value
    p_value = float((np.sum(null_d_c <= d_c_obs) + 1) / (num_permutations + 1))

    # Significance interpretation (Guney et al. standard)
    if z_score < -2.0 and p_value < 0.01:
        significance = "Highly Significant Topological Proximity (z < -2.0, p < 0.01)"
        is_proximate = True
    elif z_score < -0.15 and p_value < 0.05:
        significance = "Significant Proximity (z < -0.15, p < 0.05)"
        is_proximate = True
    else:
        significance = "Not Topologically Proximate (z >= -0.15 or p >= 0.05)"
        is_proximate = False

    result = {
        "drug_name": drug_name,
        "disease_name": disease_name,
        "target_count_in_ppi": len(T),
        "disease_gene_count_in_ppi": len(S),
        "observed_closest_distance": float(d_c_obs),
        "mean_null_distance": mean_null,
        "std_null_distance": std_null,
        "z_score": z_score,
        "p_value": p_value,
        "num_permutations": num_permutations,
        "is_proximate": is_proximate,
        "verdict": significance,
        "target_distances": target_dist_map,
        "null_distribution": null_d_c.tolist()
    }

    logger.info(
        f"Proximity Result: observed d_c = {d_c_obs:.3f}, null mean = {mean_null:.3f} +/- {std_null:.3f}, "
        f"z-score = {z_score:.3f}, p-value = {p_value:.4f} -> {significance}"
    )
    return result
