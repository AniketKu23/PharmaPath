"""Generate runnable Jupyter notebooks for PharmaPath."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
nb_dir = ROOT / "notebooks"
nb_dir.mkdir(parents=True, exist_ok=True)


def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3.11.9"
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }


def md_cell(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")]
    }


def code_cell(code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.strip().split("\n")]
    }


# 1. 01_eda.ipynb
eda_cells = [
    md_cell("# PharmaPath: Exploratory Data Analysis (EDA)\nThis notebook explores the raw and processed data assets underpinning the PharmaPath network-pharmacology pipeline:\n1. STRING v12 Homo sapiens PPI Graph and ID mapping fidelity\n2. Crated drug target sets (Metformin & Imatinib)\n3. LINCS L1000 chemical perturbation signatures\n4. Open Targets Platform disease gene modules (Type 2 Diabetes & Chronic Myeloid Leukemia)"),
    code_cell("""import sys
from pathlib import Path
ROOT_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT_DIR / "src"))

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")"""),
    md_cell("## 1. STRING v12 Interactome Scaffold Analysis\nInspect the Largest Connected Component (LCC) extracted from high-confidence (`combined_score >= 700`) STRING v12 edges."),
    code_cell("""edges_df = pd.read_parquet(ROOT_DIR / "data" / "processed" / "ppi_edges.parquet")
print(f"Total Undirected High-Confidence Edges: {len(edges_df):,}")
print(edges_df.head())"""),
    code_cell("""# Degree Distribution of the Human PPI Scaffold
G = nx.read_graphml(ROOT_DIR / "data" / "processed" / "ppi_lcc.graphml")
degrees = [d for n, d in G.degree()]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.hist(degrees, bins=50, color="#2980B9", edgecolor="black", log=True)
ax1.set_title("Degree Distribution (Log Scale)")
ax1.set_xlabel("Node Degree (k)")
ax1.set_ylabel("Count (log)")

# Log-Log scale to assess scale-free power law
sns.histplot(degrees, log_scale=(True, True), ax=ax2, color="#E67E22")
ax2.set_title("Log-Log Scale-Free Interactome Property")
ax2.set_xlabel("log(k)")
ax2.set_ylabel("log(P(k))")
plt.tight_layout()
plt.show()

print(f"Nodes: {G.number_of_nodes():,}, Edges: {G.number_of_edges():,}, Density: {nx.density(G):.6f}")"""),
    md_cell("## 2. Drug Targets Exploration\nCompare the curated targets for Metformin (mitochondrial Complex I + AMPK subunits) and Imatinib (tyrosine kinases)."),
    code_cell("""targets_met = pd.read_parquet(ROOT_DIR / "data" / "processed" / "targets_metformin.parquet")
targets_ima = pd.read_parquet(ROOT_DIR / "data" / "processed" / "targets_imatinib.parquet")

print("=== METFORMIN TARGETS ===")
print(f"Total: {len(targets_met)}, In PPI LCC: {targets_met['in_ppi'].sum()}")
print(targets_met[['gene_symbol', 'in_ppi', 'details']].head(10))

print("\\n=== IMATINIB TARGETS ===")
print(f"Total: {len(targets_ima)}, In PPI LCC: {targets_ima['in_ppi'].sum()}")
print(targets_ima[['gene_symbol', 'in_ppi', 'details']])"""),
    md_cell("## 3. Open Targets Disease Modules\nInspect disease gene sets retrieved via Open Targets GraphQL API (Score >= 0.2)."),
    code_cell("""t2d_df = pd.read_parquet(ROOT_DIR / "data" / "raw" / "opentargets_type_2_diabetes.parquet")
cml_df = pd.read_parquet(ROOT_DIR / "data" / "raw" / "opentargets_chronic_myeloid_leukemia.parquet")

print(f"Type 2 Diabetes Genes: {len(t2d_df)}, Top 5:")
print(t2d_df.head(5))

print(f"\\nChronic Myeloid Leukemia Genes: {len(cml_df)}, Top 5:")
print(cml_df.head(5))"""),
    md_cell("## 4. LINCS L1000 Expression Signatures\nExplore chemically perturbed gene expression signatures derived via Enrichr."),
    code_cell("""lincs_met = pd.read_parquet(ROOT_DIR / "data" / "raw" / "lincs_metformin.parquet")
lincs_ima = pd.read_parquet(ROOT_DIR / "data" / "raw" / "lincs_imatinib.parquet")

print(f"Metformin LINCS Perturbed Genes: {len(lincs_met)}")
print(lincs_met.head())

print(f"\\nImatinib LINCS Perturbed Genes: {len(lincs_ima)}")
print(lincs_ima.head())""")
]

with open(nb_dir / "01_eda.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(eda_cells), f, indent=2)

print("Generated notebooks/01_eda.ipynb")

# 2. 02_results.ipynb
results_cells = [
    md_cell("# PharmaPath: Comprehensive Experimental Results\nThis notebook analyzes and visualizes results across all 6 core modules:\n1. Subnetwork extraction (2-hop vs. RWR)\n2. Expression overlay and pathway enrichment (KEGG/Reactome)\n3. Network centrality, hubs, bottlenecks, and Louvain modularity\n4. Disease module network proximity (Guney et al., 2016)\n5. GNN link prediction benchmark & novel drug-protein hypotheses\n6. Two-drug comparison (Menche et al., 2015 separation $s_{AB}$ & combination synergy)"),
    code_cell("""import sys
from pathlib import Path
ROOT_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT_DIR / "src"))

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

tables_dir = ROOT_DIR / "results" / "tables"
figures_dir = ROOT_DIR / "results" / "figures"
sns.set_theme(style="whitegrid")"""),
    md_cell("## 1. Subnetwork Extraction Benchmark (2-Hop vs. RWR)"),
    code_cell("""sub_df = pd.read_csv(tables_dir / "subnetwork_comparison_all_drugs.csv")
print(sub_df)"""),
    md_cell("## 2. Enriched Pathways & Biological Sanity Audit"),
    code_cell("""with open(tables_dir / "pathway_sanity_audit.json", "r") as f:
    audit_data = json.load(f)

print("Metformin Sanity Verdict:", audit_data['Metformin']['rwr_sanity']['verdict'])
print("Imatinib Sanity Verdict:", audit_data['Imatinib']['rwr_sanity']['verdict'])

# Display top pathways for Metformin RWR
met_path = pd.read_csv(tables_dir / "pathways_metformin_rwr_subnetwork.csv")
print("\\nTop 5 Metformin RWR Pathways:")
print(met_path[['Term', 'Library', 'adj_p_value', 'Overlap']].head(5))"""),
    md_cell("## 3. Centrality Landscapes & Community Modularity"),
    code_cell("""cent_met = pd.read_csv(tables_dir / "centrality_metformin_rwr.csv")
cent_ima = pd.read_csv(tables_dir / "centrality_imatinib_rwr.csv")

print("Top 5 Metformin Bottlenecks (Betweenness):")
print(cent_met.sort_values(by="betweenness_centrality", ascending=False)[['gene_symbol', 'raw_degree', 'betweenness_centrality', 'is_bottleneck']].head(5))

print("\\nTop 5 Imatinib Bottlenecks (Betweenness):")
print(cent_ima.sort_values(by="betweenness_centrality", ascending=False)[['gene_symbol', 'raw_degree', 'betweenness_centrality', 'is_bottleneck']].head(5))"""),
    md_cell("## 4. Disease Proximity Significance (Guney et al., 2016)"),
    code_cell("""prox_df = pd.read_csv(tables_dir / "proximity_summary.csv")
print(prox_df[['drug', 'disease', 'is_primary_context', 'observed_d_c', 'mean_null_d_c', 'z_score', 'p_value', 'verdict']])"""),
    md_cell("## 5. Inductive GNN Link Prediction & Novel Hypotheses"),
    code_cell("""gnn_df = pd.read_csv(tables_dir / "gnn_ppi_link_prediction_metrics.csv")
print("=== GNN PPI Link Prediction Benchmark ===")
print(gnn_df)

rec_df = pd.read_csv(tables_dir / "leave_targets_out_metrics.csv")
print("\\n=== Leave-Targets-Out Target Recovery ===")
print(rec_df)

lit_df = pd.read_csv(tables_dir / "literature_check_table.csv")
print("\\n=== Top Predicted Candidate Hypotheses & Literature Cross-Check ===")
print(lit_df[['Drug', 'Candidate Rank', 'Candidate Protein', 'Model Confidence Score', 'Literature Cross-Check Status']].head(10))"""),
    md_cell("## 6. Two-Drug Comparative Network Pharmacology & Combination Synergy"),
    code_cell("""comp_df = pd.read_csv(tables_dir / "two_drug_comparison_summary.csv")
print(comp_df[['Comparison Metric', 'Shared Count', 'Jaccard Index', 'Detail / Interpretation']])""")
]

with open(nb_dir / "02_results.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(results_cells), f, indent=2)

print("Generated notebooks/02_results.ipynb")
