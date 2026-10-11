"""
Louvain Community Detection and Functional Module Profiling Module for PharmaPath.
Partitions drug subnetworks using the Louvain algorithm with a fixed seed,
computes Newman's modularity, and identifies dominant biological pathways per community.
"""

import logging
from typing import Any, Dict, List, Set, Tuple
import community as community_louvain
import networkx as nx
import pandas as pd

from pharmapath.enrichment import run_enrichment

logger = logging.getLogger(__name__)


def detect_louvain_communities(
    G: nx.Graph,
    random_seed: int = 42,
    resolution: float = 1.0,
    find_dominant_pathways: bool = True
) -> Tuple[nx.Graph, pd.DataFrame, Dict[str, Any]]:
    """
    Apply Louvain community detection to graph G with fixed random seed.
    Computes modularity and dominant biological pathway per community.
    """
    logger.info(f"Running Louvain community detection on {G.number_of_nodes()} nodes (seed={random_seed})...")
    
    # Run Louvain
    partition = community_louvain.best_partition(
        G,
        weight="weight",
        random_state=random_seed,
        resolution=resolution
    )

    # Modularity Q
    modularity_q = community_louvain.modularity(partition, G, weight="weight")

    # Group nodes by community
    community_members: Dict[int, List[str]] = {}
    for node, comm_id in partition.items():
        community_members.setdefault(comm_id, []).append(node)
        G.nodes[node]["community_id"] = comm_id

    # Characterize each community
    comm_records = []
    logger.info(f"Detected {len(community_members)} communities (Modularity Q={modularity_q:.4f})")

    for comm_id, members in sorted(community_members.items(), key=lambda kv: len(kv[1]), reverse=True):
        comm_subgraph = G.subgraph(members)
        sub_density = nx.density(comm_subgraph)
        
        dominant_pathway = "Uncharacterized"
        pathway_fdr = 1.0
        
        # Pathway enrichment if community has >= 5 members
        if find_dominant_pathways and len(members) >= 5:
            try:
                df_enr = run_enrichment(members, libraries=["KEGG_2021_Human", "Reactome_2022"])
                if not df_enr.empty:
                    top_p = df_enr.iloc[0]
                    dominant_pathway = f"{top_p['Term']} ({top_p['Library']})"
                    pathway_fdr = float(top_p["adj_p_value"])
            except Exception as e:
                logger.warning(f"Pathway profiling error for community {comm_id}: {e}")

        comm_records.append({
            "community_id": comm_id,
            "size": len(members),
            "internal_edges": comm_subgraph.number_of_edges(),
            "internal_density": sub_density,
            "dominant_pathway": dominant_pathway,
            "dominant_pathway_fdr": pathway_fdr,
            "member_genes": "; ".join(sorted(members)[:15]) + ("..." if len(members) > 15 else "")
        })

    df_communities = pd.DataFrame(comm_records)

    stats = {
        "num_communities": len(community_members),
        "modularity": float(modularity_q),
        "resolution": resolution,
        "community_sizes": {c: len(m) for c, m in community_members.items()},
        "largest_community_size": max(len(m) for m in community_members.values()) if community_members else 0,
    }

    return G, df_communities, stats
