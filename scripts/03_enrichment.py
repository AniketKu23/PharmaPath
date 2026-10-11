"""
Phase 3 Execution Script:
1. Overlays LINCS L1000 expression perturbation signatures onto drug subnetworks.
2. Runs Reactome & KEGG Over-Representation Analysis (ORA) via gseapy on:
   (i) significantly perturbed genes (expression-filtered)
   (ii) extracted subnetwork gene sets (2-hop and RWR).
3. Generates publication-ready dot plots in results/figures/.
4. Conducts biological sanity checks (AMPK/mTOR for Metformin, BCR-ABL/TK for Imatinib) and prints honest assessments.
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
from pharmapath.enrichment import (
    overlay_expression_scores,
    plot_pathway_enrichment,
    run_enrichment,
    sanity_check_pathways,
)

logger = logging.getLogger("Phase3_Enrichment")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def run_phase_3():
    logger.info("=== STARTING PHASE 3: EXPRESSION OVERLAY & PATHWAY ENRICHMENT ===")
    params = load_params()
    drugs_cfg = load_drugs_config()

    processed_dir = ROOT / "data" / "processed"
    raw_dir = ROOT / "data" / "raw"
    tables_dir = ROOT / "results" / "tables"
    figures_dir = ROOT / "results" / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    libraries = params.get("enrichment", {}).get("pathway_libraries", ["KEGG_2021_Human", "Reactome_2022"])
    fdr_cutoff = params.get("enrichment", {}).get("fdr_cutoff", 0.05)

    sanity_reports = {}

    for drug_key, drug_data in drugs_cfg.items():
        drug_name = drug_data["name"]
        logger.info(f"\n==================== PROCESSING {drug_name.upper()} ====================")

        # 1. Load LINCS expression data
        lincs_file = raw_dir / f"lincs_{drug_name.lower()}.parquet"
        df_lincs = pd.read_parquet(lincs_file) if lincs_file.exists() else pd.DataFrame()
        logger.info(f"Loaded {len(df_lincs)} LINCS gene expression records for {drug_name}")

        # 2. Load Subnetworks (2-hop and RWR)
        path_2hop = processed_dir / f"subnetwork_{drug_key}_2hop.graphml"
        path_rwr = processed_dir / f"subnetwork_{drug_key}_rwr.graphml"
        G_2hop = nx.read_graphml(path_2hop)
        G_rwr = nx.read_graphml(path_rwr)

        # 3. Overlay expression scores onto subnetworks and re-save
        G_2hop, df_annot_2hop = overlay_expression_scores(G_2hop, df_lincs)
        G_rwr, df_annot_rwr = overlay_expression_scores(G_rwr, df_lincs)
        nx.write_graphml(G_2hop, path_2hop)
        nx.write_graphml(G_rwr, path_rwr)

        # 4. Enrichment on (i) Significantly Perturbed Genes from LINCS
        perturbed_genes = []
        if not df_lincs.empty:
            # Genes with non-zero perturbation score
            perturbed_genes = df_lincs[df_lincs["perturbation_score"].abs() > 0]["gene_symbol"].tolist()
        logger.info(f"Running enrichment on {len(perturbed_genes)} LINCS perturbed genes for {drug_name}...")
        df_enr_lincs = run_enrichment(perturbed_genes, libraries=libraries, fdr_cutoff=fdr_cutoff)
        if not df_enr_lincs.empty:
            out_tbl_lincs = tables_dir / f"pathways_{drug_key}_lincs_perturbed.csv"
            df_enr_lincs.to_csv(out_tbl_lincs, index=False)
            plot_pathway_enrichment(
                df_enr_lincs, drug_name, "LINCS Perturbed Genes",
                figures_dir / f"pathways_{drug_key}_lincs_perturbed.png"
            )

        # 5. Enrichment on (ii) Subnetwork Genes: RWR Subnetwork
        rwr_genes = list(G_rwr.nodes())
        logger.info(f"Running enrichment on {len(rwr_genes)} RWR subnetwork genes for {drug_name}...")
        df_enr_rwr = run_enrichment(rwr_genes, libraries=libraries, fdr_cutoff=fdr_cutoff)
        if not df_enr_rwr.empty:
            out_tbl_rwr = tables_dir / f"pathways_{drug_key}_rwr_subnetwork.csv"
            df_enr_rwr.to_csv(out_tbl_rwr, index=False)
            plot_pathway_enrichment(
                df_enr_rwr, drug_name, "RWR Subnetwork",
                figures_dir / f"pathways_{drug_key}_rwr_subnetwork.png"
            )

        # 6. Enrichment on (iii) Subnetwork Genes: 2-Hop Subnetwork
        twohop_genes = list(G_2hop.nodes())
        logger.info(f"Running enrichment on {len(twohop_genes)} 2-hop subnetwork genes for {drug_name}...")
        df_enr_2hop = run_enrichment(twohop_genes, libraries=libraries, fdr_cutoff=fdr_cutoff)
        if not df_enr_2hop.empty:
            out_tbl_2hop = tables_dir / f"pathways_{drug_key}_2hop_subnetwork.csv"
            df_enr_2hop.to_csv(out_tbl_2hop, index=False)
            plot_pathway_enrichment(
                df_enr_2hop, drug_name, "2-Hop Subnetwork",
                figures_dir / f"pathways_{drug_key}_2hop_subnetwork.png"
            )

        # 7. Biological Sanity Auditing
        expected_hallmarks = drug_data.get("expected_hallmark_pathways", [])
        sanity_res_rwr = sanity_check_pathways(df_enr_rwr, expected_hallmarks, fdr_cutoff=fdr_cutoff)
        sanity_reports[drug_name] = {
            "expected_hallmarks": expected_hallmarks,
            "rwr_sanity": sanity_res_rwr,
            "top_rwr_pathways": df_enr_rwr[["Term", "Library", "adj_p_value", "Overlap"]].head(5).to_dict(orient="records") if not df_enr_rwr.empty else []
        }

        print(f"\nBIOLOGICAL SANITY AUDIT FOR {drug_name.upper()}:")
        print(f"  * Verdict: {sanity_res_rwr['verdict']}")
        print(f"  * Total Significant Pathways (FDR < {fdr_cutoff}): {sanity_res_rwr['significant_terms_count']}")
        print("  * Matched Hallmark Keywords:")
        for m in sanity_res_rwr["matched_hallmarks"]:
            print(f"    - [{m['keyword']}]: {m['matched_terms'][0]}")
        if sanity_res_rwr["missing_hallmarks"]:
            print(f"  * Missing Hallmark Keywords: {sanity_res_rwr['missing_hallmarks']}")

    # Save complete audit report
    with open(tables_dir / "pathway_sanity_audit.json", "w") as f:
        json.dump(sanity_reports, f, indent=2)

    print("\n" + "="*80)
    print("PHASE 3 EXECUTION COMPLETE - TABLES & DOT PLOTS GENERATED")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_phase_3()
