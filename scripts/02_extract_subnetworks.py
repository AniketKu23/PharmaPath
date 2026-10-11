"""
Phase 2 Execution Script:
Extracts and compares (a) 2-hop neighborhood and (b) Random Walk with Restart (RWR, r=0.5)
subnetworks for Metformin and Imatinib.
"""

import json
import logging
import sys
from pathlib import Path
import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pharmapath.config import load_drugs_config, load_params
from pharmapath.graph import load_ppi_lcc
from pharmapath.subnetwork import (
    compare_subnetworks,
    extract_2hop_subnetwork,
    extract_rwr_subnetwork,
)

logger = logging.getLogger("Phase2_Subnetworks")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def run_phase_2():
    logger.info("=== STARTING PHASE 2: DRUG SUBNETWORK EXTRACTION & COMPARISON ===")
    params = load_params()
    drugs_cfg = load_drugs_config()

    processed_dir = ROOT / "data" / "processed"
    tables_dir = ROOT / "results" / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load PPI LCC
    G_lcc = load_ppi_lcc(processed_dir)
    logger.info(f"Loaded PPI LCC: {G_lcc.number_of_nodes()} nodes, {G_lcc.number_of_edges()} edges")

    comparison_frames = []

    for drug_key, drug_data in drugs_cfg.items():
        drug_name = drug_data["name"]
        logger.info(f"\n--- Extracting Subnetworks for {drug_name} ({drug_key}) ---")

        # Load targets
        targets_file = processed_dir / f"targets_{drug_key}.parquet"
        if not targets_file.exists():
            raise FileNotFoundError(f"Targets file missing for {drug_key}: {targets_file}")
        df_targets = pd.read_parquet(targets_file)
        
        # Seeds in PPI
        seed_targets = df_targets[df_targets["in_ppi"]]["gene_symbol"].tolist()
        logger.info(f"Using {len(seed_targets)} targets in PPI for {drug_name}")

        # A: 2-Hop Subnetwork
        max_hops = params.get("subnetwork", {}).get("two_hop", {}).get("max_hops", 2)
        max_nodes = params.get("subnetwork", {}).get("two_hop", {}).get("max_nodes", 500)
        sub_2hop, df_2hop, stats_2hop = extract_2hop_subnetwork(
            G_lcc, seed_targets, max_hops=max_hops, max_nodes=max_nodes
        )
        
        # Save 2-hop artifacts
        path_2hop_graph = processed_dir / f"subnetwork_{drug_key}_2hop.graphml"
        nx.write_graphml(sub_2hop, path_2hop_graph)
        df_2hop.to_csv(tables_dir / f"subnetwork_nodes_{drug_key}_2hop.csv", index=False)

        # B: RWR Subnetwork (r=0.5, top N=150)
        restart_prob = params.get("subnetwork", {}).get("rwr", {}).get("restart_prob", 0.5)
        top_n = params.get("subnetwork", {}).get("rwr", {}).get("top_n", 150)
        sub_rwr, df_rwr, stats_rwr = extract_rwr_subnetwork(
            G_lcc, seed_targets, restart_prob=restart_prob, top_n=top_n
        )

        # Save RWR artifacts
        path_rwr_graph = processed_dir / f"subnetwork_{drug_key}_rwr.graphml"
        nx.write_graphml(sub_rwr, path_rwr_graph)
        df_rwr.to_csv(tables_dir / f"subnetwork_nodes_{drug_key}_rwr.csv", index=False)

        # Comparison
        df_comp = compare_subnetworks(sub_2hop, sub_rwr, drug_name=drug_name)
        df_comp.to_csv(tables_dir / f"subnetwork_comparison_{drug_key}.csv", index=False)
        comparison_frames.append(df_comp)

        print("\n" + f"=== {drug_name.upper()} SUBNETWORK TOPOLOGY COMPARISON ===")
        print(df_comp.to_string(index=False))

    # Combined comparison
    if comparison_frames:
        combined_comp = pd.concat(comparison_frames, ignore_index=True)
        combined_comp.to_csv(tables_dir / "subnetwork_comparison_all_drugs.csv", index=False)

    print("\n" + "="*80)
    print("PHASE 2 EXECUTION COMPLETE - SUBNETWORKS EXTRACTED & SAVED TO GRAPHML & CSV")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_phase_2()
