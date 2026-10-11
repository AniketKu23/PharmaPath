"""
PPI Graph construction, protein-to-gene ID mapping, and topological scaffold module.
Builds undirected weighted NetworkX graph and exports to GraphML and Parquet.
"""

import gzip
import logging
from pathlib import Path
from typing import Any, Dict, Set, Tuple
import networkx as nx
import pandas as pd

from pharmapath.config import get_project_root, load_params

logger = logging.getLogger(__name__)


def load_protein_to_gene_map(info_gz_path: Path) -> Tuple[Dict[str, str], Dict[str, Any]]:
    """
    Parse STRING protein info file and build ENSP -> Gene Symbol mapping.
    Reports mapping statistics and loss/unmapped counts.
    """
    logger.info(f"Parsing STRING protein info from {info_gz_path} ...")
    ensp_to_symbol: Dict[str, str] = {}
    symbol_to_ensp: Dict[str, Set[str]] = {}
    total_proteins = 0
    missing_symbols = 0

    with gzip.open(info_gz_path, "rt", encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        # Find index of protein ID and preferred name
        id_col = 0
        name_col = 1
        for idx, col in enumerate(header):
            if "string_protein_id" in col:
                id_col = idx
            elif "preferred_name" in col:
                name_col = idx

        for line in f:
            parts = line.strip().split("\t")
            if len(parts) <= max(id_col, name_col):
                continue
            total_proteins += 1
            ensp = parts[id_col].strip()
            symbol = parts[name_col].strip().upper()

            if not symbol or symbol == "-":
                missing_symbols += 1
                continue

            ensp_to_symbol[ensp] = symbol
            if symbol not in symbol_to_ensp:
                symbol_to_ensp[symbol] = set()
            symbol_to_ensp[symbol].add(ensp)

    stats = {
        "total_proteins": total_proteins,
        "mapped_proteins": len(ensp_to_symbol),
        "unique_gene_symbols": len(symbol_to_ensp),
        "missing_symbols": missing_symbols,
        "loss_rate": (missing_symbols / total_proteins) if total_proteins > 0 else 0.0,
    }
    logger.info(
        f"Protein mapping complete: {stats['mapped_proteins']}/{stats['total_proteins']} mapped "
        f"({stats['unique_gene_symbols']} unique symbols, loss rate: {stats['loss_rate']:.4%})"
    )
    return ensp_to_symbol, stats


def build_ppi_graph(
    links_gz_path: Path,
    ensp_to_symbol: Dict[str, str],
    min_combined_score: int = 700
) -> Tuple[nx.Graph, pd.DataFrame, Dict[str, Any]]:
    """
    Parse STRING links, map protein IDs to gene symbols, filter by confidence score,
    and construct the full undirected weighted NetworkX graph.
    """
    logger.info(
        f"Reading STRING links from {links_gz_path} with min_combined_score >= {min_combined_score} ..."
    )

    total_raw_lines = 0
    edges_above_threshold = 0
    unmapped_edges = 0
    edge_dict: Dict[Tuple[str, str], int] = {}

    with gzip.open(links_gz_path, "rt", encoding="utf-8") as f:
        # Skip header
        f.readline()
        for line in f:
            total_raw_lines += 1
            parts = line.strip().split()
            if len(parts) < 3:
                continue
            p1, p2, score_str = parts[0], parts[1], parts[2]
            score = int(score_str)

            if score < min_combined_score:
                continue
            edges_above_threshold += 1

            g1 = ensp_to_symbol.get(p1)
            g2 = ensp_to_symbol.get(p2)

            if not g1 or not g2:
                unmapped_edges += 1
                continue

            if g1 == g2:
                continue  # skip self-loops

            # Canonical edge tuple for undirected deduplication
            u, v = (g1, g2) if g1 < g2 else (g2, g1)
            if (u, v) not in edge_dict or score > edge_dict[(u, v)]:
                edge_dict[(u, v)] = score

    # Construct NetworkX Graph
    G = nx.Graph()
    edge_rows = []
    for (u, v), score in edge_dict.items():
        weight = score / 1000.0  # normalize 0.0 - 1.0
        G.add_edge(u, v, score=score, weight=weight)
        edge_rows.append({"source": u, "target": v, "combined_score": score, "weight": weight})

    edge_df = pd.DataFrame(edge_rows)

    stats = {
        "raw_links_lines": total_raw_lines,
        "edges_above_threshold": edges_above_threshold,
        "unmapped_edges": unmapped_edges,
        "edge_mapping_loss_rate": (unmapped_edges / edges_above_threshold) if edges_above_threshold > 0 else 0.0,
        "total_nodes": G.number_of_nodes(),
        "total_undirected_edges": G.number_of_edges(),
        "density": nx.density(G),
        "num_connected_components": nx.number_connected_components(G),
    }

    logger.info(
        f"PPI Graph built: {stats['total_nodes']} nodes, {stats['total_undirected_edges']} edges, "
        f"{stats['num_connected_components']} components (density={stats['density']:.6f})"
    )
    return G, edge_df, stats


def extract_largest_connected_component(G: nx.Graph) -> Tuple[nx.Graph, Dict[str, Any]]:
    """
    Extract the Largest Connected Component (LCC) from the graph.
    """
    components = list(nx.connected_components(G))
    lcc_nodes = max(components, key=len)
    G_lcc = G.subgraph(lcc_nodes).copy()

    stats = {
        "original_nodes": G.number_of_nodes(),
        "original_edges": G.number_of_edges(),
        "lcc_nodes": G_lcc.number_of_nodes(),
        "lcc_edges": G_lcc.number_of_edges(),
        "lcc_node_fraction": G_lcc.number_of_nodes() / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
        "lcc_density": nx.density(G_lcc),
        "num_components_pruned": len(components) - 1,
    }

    logger.info(
        f"Extracted LCC: {stats['lcc_nodes']} nodes ({stats['lcc_node_fraction']:.2%} of total), "
        f"{stats['lcc_edges']} edges, density={stats['lcc_density']:.6f}"
    )
    return G_lcc, stats


def save_graph_artifacts(
    G_lcc: nx.Graph,
    processed_dir: Path | None = None
) -> Tuple[Path, Path]:
    """
    Save the LCC graph as GraphML and Parquet edge list.
    """
    if processed_dir is None:
        processed_dir = get_project_root() / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    graphml_path = processed_dir / "ppi_lcc.graphml"
    parquet_path = processed_dir / "ppi_edges.parquet"

    # Export GraphML
    logger.info(f"Saving LCC graph to {graphml_path} ...")
    nx.write_graphml(G_lcc, graphml_path)

    # Export Parquet
    logger.info(f"Saving edge list to {parquet_path} ...")
    edges_data = []
    for u, v, d in G_lcc.edges(data=True):
        edges_data.append({
            "source": u,
            "target": v,
            "combined_score": int(d.get("score", 700)),
            "weight": float(d.get("weight", 0.7))
        })
    df_edges = pd.DataFrame(edges_data)
    df_edges.to_parquet(parquet_path, index=False)

    return graphml_path, parquet_path


def load_ppi_lcc(processed_dir: Path | None = None) -> nx.Graph:
    """
    Load the saved LCC graph from GraphML or Parquet edge list.
    """
    if processed_dir is None:
        processed_dir = get_project_root() / "data" / "processed"
    
    graphml_path = processed_dir / "ppi_lcc.graphml"
    parquet_path = processed_dir / "ppi_edges.parquet"

    if graphml_path.exists():
        logger.info(f"Loading LCC graph from GraphML: {graphml_path}")
        return nx.read_graphml(graphml_path)
    elif parquet_path.exists():
        logger.info(f"Loading LCC graph from Parquet: {parquet_path}")
        df = pd.read_parquet(parquet_path)
        G = nx.Graph()
        for _, row in df.iterrows():
            G.add_edge(row["source"], row["target"], score=row["combined_score"], weight=row["weight"])
        return G
    else:
        raise FileNotFoundError(f"Neither {graphml_path} nor {parquet_path} exists. Run Phase 1 first.")
