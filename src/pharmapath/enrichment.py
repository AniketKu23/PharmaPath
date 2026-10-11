"""
Expression overlay and pathway enrichment analysis module for PharmaPath.
Performs Over-Representation Analysis (ORA) on KEGG and Reactome gene sets using gseapy,
generates publication-ready figures, and runs biological sanity checks.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
import gseapy

from pharmapath.config import get_project_root, load_params

logger = logging.getLogger(__name__)


def overlay_expression_scores(
    G: nx.Graph,
    df_lincs: pd.DataFrame
) -> Tuple[nx.Graph, pd.DataFrame]:
    """
    Map LINCS expression scores onto subnetwork nodes.
    Adds node attributes: perturbation_score, direction, is_perturbed.
    """
    expr_map = {}
    if not df_lincs.empty:
        for _, row in df_lincs.iterrows():
            expr_map[row["gene_symbol"]] = {
                "score": float(row.get("perturbation_score", 0.0)),
                "direction": str(row.get("direction", "neutral")),
                "is_perturbed": bool(abs(float(row.get("perturbation_score", 0.0))) > 0.0)
            }

    node_data = []
    for n in G.nodes():
        if n in expr_map:
            score = float(expr_map[n]["score"])
            direction = str(expr_map[n]["direction"])
            is_pert = bool(expr_map[n]["is_perturbed"])
        else:
            score = 0.0
            direction = "unmeasured"
            is_pert = False

        G.nodes[n]["perturbation_score"] = score
        G.nodes[n]["direction"] = direction
        G.nodes[n]["is_perturbed"] = is_pert

        node_data.append({
            "gene_symbol": n,
            "perturbation_score": score,
            "direction": direction,
            "is_perturbed": is_pert,
            "degree": G.degree(n)
        })

    df_annotated = pd.DataFrame(node_data)
    logger.info(
        f"Expression overlaid on graph: {df_annotated['is_perturbed'].sum()}/{len(df_annotated)} nodes "
        f"have measured perturbation signatures."
    )
    return G, df_annotated


def run_enrichment(
    gene_list: List[str] | Set[str],
    libraries: List[str] | None = None,
    fdr_cutoff: float = 0.05,
    top_n: int = 20
) -> pd.DataFrame:
    """
    Run Over-Representation Analysis (ORA) using gseapy against KEGG and Reactome.
    """
    if libraries is None:
        libraries = ["KEGG_2021_Human", "Reactome_2022"]

    genes = list(set([g.upper() for g in gene_list if g]))
    if len(genes) < 3:
        logger.warning(f"Gene list too small for enrichment: {len(genes)} genes")
        return pd.DataFrame()

    logger.info(f"Running pathway enrichment for {len(genes)} genes against {libraries} ...")
    dfs = []
    for lib in libraries:
        try:
            enr = gseapy.enrichr(
                gene_list=genes,
                gene_sets=lib,
                outdir=None,
                verbose=False
            )
            df_res = enr.results
            if not df_res.empty:
                df_res["Library"] = lib
                dfs.append(df_res)
        except Exception as e:
            logger.warning(f"Enrichment failed for library {lib}: {e}")

    if not dfs:
        return pd.DataFrame()

    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Standardize column names
    col_rename = {
        "Gene_set": "Library",
        "Term": "Term",
        "Overlap": "Overlap",
        "P-value": "p_value",
        "Adjusted P-value": "adj_p_value",
        "Odds Ratio": "odds_ratio",
        "Combined Score": "combined_score",
        "Genes": "genes"
    }
    # Keep only known columns and rename
    existing_cols = [c for c in col_rename.keys() if c in combined_df.columns]
    combined_df = combined_df[existing_cols].rename(columns=col_rename)
    combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()].copy()
    
    # Filter and sort
    combined_df["adj_p_value"] = pd.to_numeric(combined_df["adj_p_value"], errors="coerce")
    combined_df["p_value"] = pd.to_numeric(combined_df["p_value"], errors="coerce")
    combined_df["combined_score"] = pd.to_numeric(combined_df.get("combined_score", 0), errors="coerce")
    
    # Sort by Adjusted P-value
    combined_df = combined_df.sort_values(by=["adj_p_value", "p_value"], ascending=[True, True])
    return combined_df


def sanity_check_pathways(
    df_enrichment: pd.DataFrame,
    expected_keywords: List[str],
    fdr_cutoff: float = 0.05
) -> Dict[str, Any]:
    """
    Audit enrichment results against biologically expected hallmark pathways.
    Reports honestly whether expected pathways are present among significant terms.
    """
    if df_enrichment.empty:
        return {
            "passed": False,
            "significant_terms_count": 0,
            "matched_hallmarks": [],
            "missing_hallmarks": expected_keywords,
            "verdict": "FAILED: No enrichment results returned"
        }

    sig_df = df_enrichment[df_enrichment["adj_p_value"] <= fdr_cutoff]
    sig_terms = sig_df["Term"].tolist()

    matched = []
    missing = []

    for kw in expected_keywords:
        kw_clean = kw.lower()
        matches = [t for t in sig_terms if kw_clean in t.lower()]
        if matches:
            matched.append({"keyword": kw, "matched_terms": matches[:3]})
        else:
            missing.append(kw)

    passed = len(matched) > 0
    match_rate = len(matched) / len(expected_keywords) if expected_keywords else 0.0

    if match_rate >= 0.5:
        verdict = f"PASSED: Robust biological alignment ({len(matched)}/{len(expected_keywords)} hallmark concepts verified with FDR < {fdr_cutoff})"
    elif match_rate > 0.0:
        verdict = f"PARTIALLY VALIDATED: Moderate alignment ({len(matched)}/{len(expected_keywords)} hallmarks detected with FDR < {fdr_cutoff})"
    else:
        verdict = f"UNEXPECTED: None of the primary hallmark keywords ({expected_keywords}) achieved FDR < {fdr_cutoff}"

    return {
        "passed": passed,
        "match_rate": match_rate,
        "significant_terms_count": len(sig_df),
        "matched_hallmarks": matched,
        "missing_hallmarks": missing,
        "verdict": verdict
    }


def plot_pathway_enrichment(
    df_enrichment: pd.DataFrame,
    drug_name: str,
    analysis_type: str,
    output_path: Path,
    top_n: int = 12
) -> None:
    """
    Generate a publication-quality dot/bar plot of top enriched pathways.
    """
    if df_enrichment.empty:
        logger.warning(f"No enrichment data to plot for {drug_name} ({analysis_type})")
        return

    top_df = df_enrichment.loc[:, ~df_enrichment.columns.duplicated()].head(top_n).copy()
    
    # Shorten long pathway names
    clean_terms = [str(t).split(" (")[0][:45] for t in top_df["Term"]]
    top_df["Clean_Term"] = clean_terms
    
    fdr_vals = pd.to_numeric(top_df["adj_p_value"], errors="coerce").fillna(1.0).values
    neg_log_fdr = -np.log10(np.clip(fdr_vals, 1e-30, 1.0))
    top_df["neg_log10_fdr"] = neg_log_fdr

    # Parse overlap ratio
    gene_ratios = []
    for s in top_df["Overlap"]:
        try:
            parts = str(s).split("/")
            ratio = int(parts[0]) / int(parts[1]) if len(parts) == 2 else 0.05
        except Exception:
            ratio = 0.05
        gene_ratios.append(ratio)
    top_df["Gene_Ratio"] = gene_ratios

    # Plot
    plt.figure(figsize=(10, 6), dpi=300)
    sns.set_theme(style="whitegrid")
    
    # Dot plot: x = Gene Ratio, y = Term, size = -log10(FDR), hue = Library
    sns.scatterplot(
        data=top_df,
        x="Gene_Ratio",
        y="Clean_Term",
        size="neg_log10_fdr",
        sizes=(70, 350),
        hue="Library" if "Library" in top_df.columns else None,
        palette="viridis",
        alpha=0.9,
        edgecolor="black"
    )

    plt.title(f"Top Enriched Pathways: {drug_name} ({analysis_type})", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Gene Ratio (Overlap / Pathway Size)", fontsize=11)
    plt.ylabel("Pathway Term", fontsize=11)
    plt.axvline(x=0, color="gray", linestyle="--", alpha=0.5)
    if "Library" in top_df.columns:
        plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0)
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved publication-grade enrichment plot: {output_path}")
