"""
Phase 5 Execution Script:
1. Leak-free Train/Val/Test RandomLinkSplit on full PPI LCC scaffold.
2. Trains & evaluates:
   - Node2Vec + Logistic Regression Baseline
   - GraphSAGE Link Predictor
   - Graph Autoencoder (GAE)
3. Evaluates Leave-Targets-Out target recovery (Hits@10, Hits@20, Hits@50, MRR).
4. Generates Top-20 novel drug-protein repurposing / off-target hypotheses per drug.
5. Saves model checkpoints and publication result tables.
"""

import json
import logging
import sys
from pathlib import Path
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pharmapath.config import load_drugs_config, load_params
from pharmapath.graph import load_ppi_lcc
from pharmapath.models import (
    create_pyg_data_from_networkx,
    predict_top_hypotheses,
    run_leave_targets_out_evaluation,
    set_seed,
    split_edges_leak_free,
    train_evaluate_gae,
    train_evaluate_graphsage,
    train_evaluate_node2vec,
)

logger = logging.getLogger("Phase5_GNN")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def run_phase_5():
    logger.info("=== STARTING PHASE 5: GNN LINK PREDICTION & DRUG TARGET RECOVERY ===")
    params = load_params()
    drugs_cfg = load_drugs_config()

    processed_dir = ROOT / "data" / "processed"
    tables_dir = ROOT / "results" / "tables"
    models_dir = ROOT / "results" / "models"
    tables_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    seed = params.get("seed", 42)
    set_seed(seed)

    # 1. Load PPI LCC
    G_lcc = load_ppi_lcc(processed_dir)
    logger.info(f"Loaded PPI LCC: {G_lcc.number_of_nodes()} nodes, {G_lcc.number_of_edges()} edges")

    # 2. Convert to PyG Data
    pyg_data, nodes, node_to_idx = create_pyg_data_from_networkx(
        G_lcc,
        embedding_dim=params.get("gnn", {}).get("node2vec", {}).get("embedding_dim", 64),
        seed=seed
    )

    # 3. Leak-Free Edge Split
    val_ratio = params.get("gnn", {}).get("link_split", {}).get("val_ratio", 0.1)
    test_ratio = params.get("gnn", {}).get("link_split", {}).get("test_ratio", 0.1)
    train_data, val_data, test_data = split_edges_leak_free(pyg_data, val_ratio, test_ratio, seed=seed)

    # 4. Model 1: Node2Vec + Logistic Regression Baseline
    n2v_epochs = params.get("gnn", {}).get("node2vec", {}).get("epochs", 8)
    n2v_dim = params.get("gnn", {}).get("node2vec", {}).get("embedding_dim", 64)
    n2v_auroc, n2v_ap, z_n2v = train_evaluate_node2vec(
        train_data, test_data, embedding_dim=n2v_dim, epochs=n2v_epochs, seed=seed
    )

    # 5. Model 2: GraphSAGE Link Predictor
    sage_cfg = params.get("gnn", {}).get("graphsage", {})
    sage_auroc, sage_ap, z_sage, sage_model = train_evaluate_graphsage(
        train_data, test_data,
        hidden_channels=sage_cfg.get("hidden_channels", 64),
        out_channels=sage_cfg.get("out_channels", 32),
        epochs=sage_cfg.get("epochs", 50),
        lr=sage_cfg.get("lr", 0.005),
        seed=seed
    )
    torch.save(sage_model.state_dict(), models_dir / "graphsage_link_predictor.pt")

    # 6. Model 3: Graph Autoencoder (GAE)
    gae_cfg = params.get("gnn", {}).get("gae", {})
    gae_auroc, gae_ap, z_gae, gae_model = train_evaluate_gae(
        train_data, test_data,
        out_channels=gae_cfg.get("out_channels", 32),
        epochs=gae_cfg.get("epochs", 50),
        lr=gae_cfg.get("lr", 0.005),
        seed=seed
    )
    torch.save(gae_model.state_dict(), models_dir / "gae_link_predictor.pt")

    # Summary table for PPI Link Prediction
    metrics_records = [
        {"Model": "Node2Vec + Logistic Regression (Baseline)", "Test AUROC": round(n2v_auroc, 4), "Test Average Precision": round(n2v_ap, 4)},
        {"Model": "GraphSAGE (Inductive GNN)", "Test AUROC": round(sage_auroc, 4), "Test Average Precision": round(sage_ap, 4)},
        {"Model": "Graph Autoencoder (GAE)", "Test AUROC": round(gae_auroc, 4), "Test Average Precision": round(gae_ap, 4)},
    ]
    df_metrics = pd.DataFrame(metrics_records)
    df_metrics.to_csv(tables_dir / "gnn_ppi_link_prediction_metrics.csv", index=False)

    print("\n" + "="*80)
    print("PPI LINK PREDICTION BENCHMARK RESULTS (Test Split - Zero Data Leakage):")
    print(df_metrics.to_string(index=False))
    print("="*80 + "\n")

    # Pick best embeddings for drug-target prediction
    best_z = z_sage if sage_auroc >= gae_auroc else z_gae
    embedding_source = "GraphSAGE" if sage_auroc >= gae_auroc else "GAE"
    logger.info(f"Using {embedding_source} embeddings for drug-target leave-targets-out validation and hypotheses.")

    # 7. Leave-Targets-Out Validation & Top 20 Hypotheses
    recovery_records = []

    for drug_key, drug_data in drugs_cfg.items():
        drug_name = drug_data["name"]
        df_t = pd.read_parquet(processed_dir / f"targets_{drug_key}.parquet")
        known_targets = df_t[df_t["in_ppi"]]["gene_symbol"].tolist()

        # Leave-targets-out
        rec_res = run_leave_targets_out_evaluation(
            protein_embeddings=best_z,
            node_to_idx=node_to_idx,
            nodes=nodes,
            known_targets=known_targets,
            drug_name=drug_name,
            k_hidden=params.get("gnn", {}).get("leave_targets_out", {}).get("k_hidden", 2),
            hits_ks=params.get("gnn", {}).get("leave_targets_out", {}).get("hits_ks", [10, 20, 50]),
            seed=seed
        )
        if rec_res:
            recovery_records.append({
                "Drug": drug_name,
                "Candidate Proteome Size": rec_res["total_proteome_candidates"],
                "Train Targets Count": len(rec_res["train_targets"]),
                "Hidden Test Targets": ", ".join(rec_res["hidden_test_targets"]),
                "Hidden Targets Ranks": str(rec_res["target_ranks"]),
                "Mean Reciprocal Rank (MRR)": round(rec_res["mrr"], 4),
                "Hits@10": f"{rec_res['hits@10']:.1%}",
                "Hits@20": f"{rec_res['hits@20']:.1%}",
                "Hits@50": f"{rec_res['hits@50']:.1%}"
            })

        # Top 20 Novel Hypotheses
        top_k = params.get("gnn", {}).get("top_hypotheses_k", 20)
        df_hyp = predict_top_hypotheses(
            protein_embeddings=best_z,
            node_to_idx=node_to_idx,
            nodes=nodes,
            known_targets=known_targets,
            drug_name=drug_name,
            top_k=top_k
        )
        df_hyp.to_csv(tables_dir / f"top20_hypotheses_{drug_key}.csv", index=False)

        print(f"\nTOP 5 CANDIDATE HYPOTHESES FOR {drug_name.upper()} (Out of {top_k} predicted):")
        print(df_hyp[["rank", "candidate_protein", "confidence_score", "status"]].head(5).to_string(index=False))

    # Save recovery summary
    if recovery_records:
        df_rec = pd.DataFrame(recovery_records)
        df_rec.to_csv(tables_dir / "leave_targets_out_metrics.csv", index=False)
        print("\n" + "="*80)
        print("LEAVE-TARGETS-OUT RECOVERY BENCHMARK:")
        print(df_rec[["Drug", "Hidden Test Targets", "Hidden Targets Ranks", "Mean Reciprocal Rank (MRR)", "Hits@20"]].to_string(index=False))
        print("="*80 + "\n")

    print("\n" + "="*80)
    print("PHASE 5 EXECUTION COMPLETE - GNN MODELS TRAINED & EVALUATED")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_phase_5()
