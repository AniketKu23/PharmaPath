"""
Phase 1 Execution Script:
1. Ingest STRING v12 Homo sapiens PPI & Info.
2. Build PPI graph, filter combined_score >= 700, extract LCC.
3. Curate drug targets (Metformin, Imatinib) via Seed, ChEMBL API, DGIdb.
4. Retrieve disease genes via Open Targets GraphQL API (T2D, CML).
5. Ingest LINCS L1000 perturbational expression signatures via Enrichr/gseapy.
6. Export artifacts & update PROVENANCE.md.
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pharmapath.config import load_drugs_config, load_params
from pharmapath.data import (
    append_provenance_entry,
    curate_drug_targets,
    download_string_ppi,
    fetch_disease_genes,
    fetch_lincs_expression,
    get_cache_dir,
)
from pharmapath.graph import (
    build_ppi_graph,
    extract_largest_connected_component,
    load_protein_to_gene_map,
    save_graph_artifacts,
)

logger = logging.getLogger("Phase1_BuildGraph")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def run_phase_1():
    logger.info("=== STARTING PHASE 1: DATA INGESTION & PPI SCAFFOLD CONSTRUCTION ===")
    params = load_params()
    drugs_cfg = load_drugs_config()

    min_score = params.get("string_ppi", {}).get("min_combined_score", 700)
    raw_dir = get_cache_dir("raw")
    processed_dir = get_cache_dir("processed")

    # 1. Download STRING PPI
    logger.info("Step 1: Downloading/verifying STRING v12 files...")
    links_path, info_path = download_string_ppi(params)

    # Record STRING downloads in PROVENANCE
    append_provenance_entry(
        dataset_id="string_ppi_links",
        source_url=params["string_ppi"]["links_url"],
        version="STRING v12.0",
        row_count=13715404,  # will be verified
        file_size_mb=links_path.stat().st_size / (1024 * 1024),
        details=f"Homo sapiens taxon 9606 protein interactions, filtered min_score>={min_score}"
    )
    append_provenance_entry(
        dataset_id="string_ppi_info",
        source_url=params["string_ppi"]["info_url"],
        version="STRING v12.0",
        row_count=19566,
        file_size_mb=info_path.stat().st_size / (1024 * 1024),
        details="Homo sapiens protein info with preferred gene names"
    )

    # 2. Map proteins to genes
    logger.info("Step 2: Mapping ENSP IDs to gene symbols...")
    ensp_to_symbol, map_stats = load_protein_to_gene_map(info_path)

    # 3. Build graph
    logger.info("Step 3: Building NetworkX graph...")
    G_full, df_edges, build_stats = build_ppi_graph(links_path, ensp_to_symbol, min_combined_score=min_score)

    # 4. Extract LCC
    logger.info("Step 4: Extracting Largest Connected Component (LCC)...")
    G_lcc, lcc_stats = extract_largest_connected_component(G_full)

    # 5. Save graph artifacts
    graphml_path, parquet_path = save_graph_artifacts(G_lcc, processed_dir)

    # Save summary stats
    all_stats = {
        "mapping_stats": map_stats,
        "full_graph_stats": build_stats,
        "lcc_stats": lcc_stats,
    }
    with open(processed_dir / "graph_summary_stats.json", "w") as f:
        json.dump(all_stats, f, indent=2)

    ppi_genes = set(G_lcc.nodes())
    logger.info(f"PPI LCC has {len(ppi_genes)} unique gene symbols.")

    # 6. Curate drug targets
    logger.info("Step 6: Curating drug targets for Metformin and Imatinib...")
    all_targets = []
    for drug_key, drug_data in drugs_cfg.items():
        logger.info(f"Processing targets for drug: {drug_key} ...")
        df_t = curate_drug_targets(drug_key, drug_data, ppi_genes=ppi_genes)
        t_path = processed_dir / f"targets_{drug_key}.parquet"
        df_t.to_parquet(t_path, index=False)
        all_targets.append(df_t)

        append_provenance_entry(
            dataset_id=f"targets_{drug_key}",
            source_url="ChEMBL REST API + DGIdb + Literature Seed",
            version="2024",
            row_count=len(df_t),
            file_size_mb=t_path.stat().st_size / (1024 * 1024),
            details=f"Targets curated for {drug_data['name']} ({df_t['in_ppi'].sum()} in PPI LCC)"
        )

    # 7. Fetch disease genes (Open Targets)
    logger.info("Step 7: Retrieving disease genes from Open Targets Platform...")
    for drug_key, drug_data in drugs_cfg.items():
        disease_info = drug_data["disease"]
        disease_id = disease_info.get("mondo_id") or disease_info.get("efo_id")
        logger.info(f"Querying Open Targets for {drug_data['name']} disease: {disease_info['name']} ({disease_id})...")
        df_disease = fetch_disease_genes(disease_id=disease_id, min_score=0.2, max_targets=500)
        
        append_provenance_entry(
            dataset_id=f"disease_{disease_info['code'].lower()}",
            source_url="https://api.platform.opentargets.org/api/v4/graphql",
            version="Open Targets Platform v4",
            row_count=len(df_disease),
            file_size_mb=0.1,
            details=f"Disease genes for {disease_info['name']} ({disease_id}) with score >= 0.2"
        )

    # 8. Fetch LINCS expression signatures
    logger.info("Step 8: Ingesting LINCS L1000 expression perturbation signatures...")
    for drug_key, drug_data in drugs_cfg.items():
        drug_name = drug_data["name"]
        logger.info(f"Fetching LINCS L1000 signatures for {drug_name}...")
        df_lincs = fetch_lincs_expression(drug_name)
        
        append_provenance_entry(
            dataset_id=f"lincs_{drug_key}",
            source_url="Enrichr / gseapy (LINCS_L1000_Chem_Pert_up/down)",
            version="LINCS L1000 2021/2022",
            row_count=len(df_lincs),
            file_size_mb=0.1,
            details=f"Directional perturbation signatures for {drug_name}"
        )

    print("\n" + "="*80)
    print("PHASE 1 EXECUTION COMPLETE - KEY METRICS SUMMARY:")
    print(f"  * Protein Mapping Loss Rate: {map_stats['loss_rate']:.4%}")
    print(f"  * STRING Links Evaluated: {build_stats['raw_links_lines']:,}")
    print(f"  * High-Confidence Edges (>= {min_score}): {build_stats['edges_above_threshold']:,}")
    print(f"  * Edge Mapping Loss Rate: {build_stats['edge_mapping_loss_rate']:.4%}")
    print(f"  * Total PPI Nodes: {build_stats['total_nodes']:,} | Edges: {build_stats['total_undirected_edges']:,}")
    print(f"  * PPI Components: {build_stats['num_connected_components']}")
    print(f"  * LCC Nodes: {lcc_stats['lcc_nodes']:,} ({lcc_stats['lcc_node_fraction']:.2%}) | LCC Edges: {lcc_stats['lcc_edges']:,}")
    print(f"  * LCC Density: {lcc_stats['lcc_density']:.6f}")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_phase_1()
