"""
Phase 4 Execution Script: Network Analytics & Disease Proximity
1. Centrality metrics (Degree, Betweenness, Closeness, Eigenvector) -> Hubs & Bottlenecks.
2. Louvain community detection with fixed random seed, modularity Q, and community pathway profiling.
3. Guney et al. (2016) network proximity (closest distance d_c) against >= 1000 degree-matched null permutations.
"""

import json
import logging
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pharmapath.centrality import compute_network_centralities
from pharmapath.communities import detect_louvain_communities
from pharmapath.config import load_drugs_config, load_params
from pharmapath.graph import load_ppi_lcc
from pharmapath.proximity import calculate_network_proximity

logger = logging.getLogger("Phase4_NetworkAnalysis")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def plot_proximity_distribution(
    prox_res: dict,
    output_path: Path
) -> None:
    """Plot null distribution histogram vs observed closest distance."""
    null_vals = np.array(prox_res["null_distribution"])
    obs_val = prox_res["observed_closest_distance"]
    z = prox_res["z_score"]
    p = prox_res["p_value"]

    plt.figure(figsize=(8, 5), dpi=300)
    sns.set_theme(style="whitegrid")
    
    sns.histplot(null_vals, kde=True, color="#4A90E2", bins=30, stat="density", label="Degree-matched Null Model")
    plt.axvline(obs_val, color="#D0021B", linestyle="--", linewidth=2.5, label=f"Observed $d_c$ = {obs_val:.3f}")
    
    plt.title(f"Network Proximity: {prox_res['drug_name']} vs {prox_res['disease_name']}\n(z = {z:.2f}, p = {p:.4f})", fontsize=12, fontweight="bold")
    plt.xlabel("Closest Distance ($d_c$)", fontsize=11)
    plt.ylabel("Null Probability Density", fontsize=11)
    plt.legend(loc="upper right")
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved proximity null distribution plot: {output_path}")


def run_phase_4():
    logger.info("=== STARTING PHASE 4: NETWORK ANALYTICS & DISEASE PROXIMITY ===")
    params = load_params()
    drugs_cfg = load_drugs_config()

    processed_dir = ROOT / "data" / "processed"
    tables_dir = ROOT / "results" / "tables"
    figures_dir = ROOT / "results" / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load PPI LCC
    G_lcc = load_ppi_lcc(processed_dir)

    # --- PART A & B: CENTRALITIES & COMMUNITIES ON SUBNETWORKS ---
    for drug_key, drug_data in drugs_cfg.items():
        drug_name = drug_data["name"]
        logger.info(f"\n--- Analyzing Topology & Communities for {drug_name} ---")

        for method in ["rwr", "2hop"]:
            sub_path = processed_dir / f"subnetwork_{drug_key}_{method}.graphml"
            sub_G = nx.read_graphml(sub_path)

            # Centralities
            sub_G, df_cent, cent_stats = compute_network_centralities(
                sub_G,
                hub_percentile=params.get("centrality", {}).get("hub_percentile", 0.05),
                bottleneck_percentile=params.get("centrality", {}).get("bottleneck_percentile", 0.05)
            )
            df_cent.to_csv(tables_dir / f"centrality_{drug_key}_{method}.csv", index=False)

            # Louvain Communities
            sub_G, df_comm, comm_stats = detect_louvain_communities(
                sub_G,
                random_seed=params.get("communities", {}).get("random_seed", 42),
                resolution=params.get("communities", {}).get("resolution", 1.0),
                find_dominant_pathways=(method == "rwr") # full pathway profiling on RWR
            )
            df_comm.to_csv(tables_dir / f"communities_{drug_key}_{method}.csv", index=False)

            # Save updated GraphML with centrality and community node attributes
            nx.write_graphml(sub_G, sub_path)

            print(f"[{drug_name} {method.upper()}] Modularity Q = {comm_stats['modularity']:.4f} ({comm_stats['num_communities']} communities)")
            print(f"[{drug_name} {method.upper()}] Identified {cent_stats['num_hubs']} hubs, {cent_stats['num_bottlenecks']} bottlenecks, {cent_stats['num_bridges']} bridges")
            if not df_comm.empty and "dominant_pathway" in df_comm.columns:
                print(f"  * Dominant Pathways per Community ({method.upper()}):")
                for _, r in df_comm.head(3).iterrows():
                    print(f"    - Community {r['community_id']} (size {r['size']}): {r['dominant_pathway']}")

    # --- PART C: NETWORK PROXIMITY (GUNEY ET AL.) ---
    logger.info("\n--- Calculating Guney et al. (2016) Disease Module Network Proximity ---")
    n_perms = params.get("proximity", {}).get("num_permutations", 1000)
    proximity_records = []
    proximity_full_dict = {}

    # Load targets and disease genes
    for drug_key, drug_data in drugs_cfg.items():
        drug_name = drug_data["name"]
        targets_file = processed_dir / f"targets_{drug_key}.parquet"
        df_t = pd.read_parquet(targets_file)
        drug_targets = df_t[df_t["in_ppi"]]["gene_symbol"].tolist()

        # Primary disease context
        disease_info = drug_data["disease"]
        disease_name = disease_info["name"]
        disease_id = disease_info.get("mondo_id") or disease_info.get("efo_id")
        disease_file = ROOT / "data" / "raw" / f"opentargets_{disease_id}.parquet"
        df_d = pd.read_parquet(disease_file)
        disease_genes = df_d["gene_symbol"].tolist()

        # Calculate proximity (Primary association)
        res = calculate_network_proximity(
            G_lcc,
            drug_targets=drug_targets,
            disease_genes=disease_genes,
            drug_name=drug_name,
            disease_name=disease_name,
            num_permutations=n_perms,
            random_seed=params.get("proximity", {}).get("random_seed", 42)
        )
        plot_proximity_distribution(res, figures_dir / f"proximity_{drug_key}_{disease_info['code'].lower()}.png")
        proximity_full_dict[f"{drug_key}_{disease_info['code'].lower()}"] = res

        proximity_records.append({
            "drug": drug_name,
            "disease": disease_name,
            "is_primary_context": True,
            "targets_in_ppi": res["target_count_in_ppi"],
            "disease_genes_in_ppi": res["disease_gene_count_in_ppi"],
            "observed_d_c": res["observed_closest_distance"],
            "mean_null_d_c": res["mean_null_distance"],
            "std_null_d_c": res["std_null_distance"],
            "z_score": res["z_score"],
            "p_value": res["p_value"],
            "verdict": res["verdict"]
        })

    # Cross-disease control: Metformin vs CML, Imatinib vs T2D
    logger.info("Computing cross-disease controls (Metformin vs CML, Imatinib vs T2D)...")
    ctrl_pairs = [
        ("metformin", "imatinib"), # Metformin targets vs CML genes
        ("imatinib", "metformin"), # Imatinib targets vs T2D genes
    ]
    for d1_key, d2_key in ctrl_pairs:
        d1_name = drugs_cfg[d1_key]["name"]
        d2_data = drugs_cfg[d2_key]
        d2_disease_name = d2_data["disease"]["name"]
        d2_disease_id = d2_data["disease"].get("mondo_id") or d2_data["disease"].get("efo_id")

        df_t = pd.read_parquet(processed_dir / f"targets_{d1_key}.parquet")
        t_genes = df_t[df_t["in_ppi"]]["gene_symbol"].tolist()

        df_d = pd.read_parquet(ROOT / "data" / "raw" / f"opentargets_{d2_disease_id}.parquet")
        d_genes = df_d["gene_symbol"].tolist()

        res_ctrl = calculate_network_proximity(
            G_lcc,
            drug_targets=t_genes,
            disease_genes=d_genes,
            drug_name=d1_name,
            disease_name=f"{d2_disease_name} (Cross-Control)",
            num_permutations=n_perms,
            random_seed=params.get("proximity", {}).get("random_seed", 42)
        )
        proximity_full_dict[f"{d1_key}_vs_{d2_key}_disease"] = res_ctrl
        proximity_records.append({
            "drug": d1_name,
            "disease": f"{d2_disease_name} [Control]",
            "is_primary_context": False,
            "targets_in_ppi": res_ctrl["target_count_in_ppi"],
            "disease_genes_in_ppi": res_ctrl["disease_gene_count_in_ppi"],
            "observed_d_c": res_ctrl["observed_closest_distance"],
            "mean_null_d_c": res_ctrl["mean_null_distance"],
            "std_null_d_c": res_ctrl["std_null_distance"],
            "z_score": res_ctrl["z_score"],
            "p_value": res_ctrl["p_value"],
            "verdict": res_ctrl["verdict"]
        })

    # Save proximity summary
    df_prox_summary = pd.DataFrame(proximity_records)
    df_prox_summary.to_csv(tables_dir / "proximity_summary.csv", index=False)
    
    # Save raw json (without the large null arrays)
    sanitized_dict = {}
    for k, v in proximity_full_dict.items():
        v_copy = v.copy()
        v_copy.pop("null_distribution", None)
        sanitized_dict[k] = v_copy
    with open(tables_dir / "proximity_summary.json", "w") as f:
        json.dump(sanitized_dict, f, indent=2)

    print("\n" + "="*80)
    print("PHASE 4 NETWORK PROXIMITY SUMMARY TABLE (Guney et al. 2016):")
    print(df_prox_summary[["drug", "disease", "observed_d_c", "z_score", "p_value", "verdict"]].to_string(index=False))
    print("="*80 + "\n")


if __name__ == "__main__":
    run_phase_4()
