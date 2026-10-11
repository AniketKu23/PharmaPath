"""
Data acquisition, API querying, and caching module for PharmaPath.
Maintains strict provenance and handles fallbacks gracefully.
"""

from datetime import datetime
import gzip
import logging
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import requests
import pandas as pd
import gseapy

from pharmapath.config import get_project_root, load_params

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def get_cache_dir(subdir: str = "raw") -> Path:
    """Return cache directory path and create if needed."""
    cache_path = get_project_root() / "data" / subdir
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


def download_file(url: str, dest_path: Path, mirror_url: str | None = None, chunk_size: int = 1024 * 1024) -> Path:
    """
    Download a file with streaming and caching.
    If already cached and non-empty, skips download.
    """
    if dest_path.exists() and dest_path.stat().st_size > 1024:
        logger.info(f"File already cached: {dest_path} ({dest_path.stat().st_size / (1024*1024):.2f} MB)")
        return dest_path

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    urls_to_try = [url]
    if mirror_url:
        urls_to_try.append(mirror_url)

    for attempt_url in urls_to_try:
        try:
            logger.info(f"Downloading from {attempt_url} -> {dest_path} ...")
            response = requests.get(attempt_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded {dest_path.name} ({dest_path.stat().st_size / (1024*1024):.2f} MB)")
            return dest_path
        except Exception as e:
            logger.warning(f"Failed to download from {attempt_url}: {e}")

    raise RuntimeError(f"Could not download file from primary or mirror URL to {dest_path}")


def download_string_ppi(params: Dict[str, Any] | None = None) -> Tuple[Path, Path]:
    """
    Download STRING v12 Homo sapiens protein links and protein info.
    """
    if params is None:
        params = load_params()

    cfg = params["string_ppi"]
    raw_dir = get_cache_dir("raw")

    links_path = raw_dir / "9606.protein.links.v12.0.txt.gz"
    info_path = raw_dir / "9606.protein.info.v12.0.txt.gz"

    download_file(cfg["links_url"], links_path, mirror_url=cfg.get("links_mirror_url"))
    download_file(cfg["info_url"], info_path, mirror_url=cfg.get("info_mirror_url"))

    return links_path, info_path


def fetch_chembl_targets(chembl_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve drug target mechanisms and bioactivities from ChEMBL REST API.
    """
    targets = []
    headers = {"Accept": "application/json"}

    # 1. Mechanism of action
    mech_url = f"https://www.ebi.ac.uk/chembl/api/data/mechanism.json?parent_molecule_chembl_id={chembl_id}"
    try:
        r = requests.get(mech_url, headers=headers, timeout=20)
        if r.status_code == 200:
            mechs = r.json().get("mechanisms", [])
            for m in mechs:
                target_chembl_id = m.get("target_chembl_id")
                action_type = m.get("action_type", "INHIBITOR")
                desc = m.get("mechanism_of_action", "")
                
                # Resolve target components to gene symbol
                gene_symbols = resolve_chembl_target_to_genes(target_chembl_id)
                for gene in gene_symbols:
                    targets.append({
                        "gene_symbol": gene,
                        "source": "chembl_mechanism",
                        "target_chembl_id": target_chembl_id,
                        "details": f"{desc} ({action_type})"
                    })
    except Exception as e:
        logger.warning(f"ChEMBL mechanism query error for {chembl_id}: {e}")

    # 2. High affinity bioactivities (IC50 / Ki with pChEMBL >= 6.0)
    act_url = f"https://www.ebi.ac.uk/chembl/api/data/activity.json?molecule_chembl_id={chembl_id}&pchembl_value__gte=6.0&limit=50"
    try:
        r = requests.get(act_url, headers=headers, timeout=20)
        if r.status_code == 200:
            acts = r.json().get("activities", [])
            for a in acts:
                target_chembl_id = a.get("target_chembl_id")
                pchembl = a.get("pchembl_value")
                std_type = a.get("standard_type")
                if target_chembl_id:
                    gene_symbols = resolve_chembl_target_to_genes(target_chembl_id)
                    for gene in gene_symbols:
                        targets.append({
                            "gene_symbol": gene,
                            "source": "chembl_activity",
                            "target_chembl_id": target_chembl_id,
                            "details": f"{std_type} pChEMBL={pchembl}"
                        })
    except Exception as e:
        logger.warning(f"ChEMBL activity query error for {chembl_id}: {e}")

    return targets


_chembl_target_cache: Dict[str, List[str]] = {}

def resolve_chembl_target_to_genes(target_chembl_id: str) -> List[str]:
    """Resolve ChEMBL target ID to approved Gene Symbol(s)."""
    if target_chembl_id in _chembl_target_cache:
        return _chembl_target_cache[target_chembl_id]

    genes = []
    try:
        url = f"https://www.ebi.ac.uk/chembl/api/data/target/{target_chembl_id}.json"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            for comp in data.get("target_components", []):
                for syn in comp.get("target_component_synonyms", []):
                    if syn.get("syn_type") == "GENE_SYMBOL":
                        gene = syn.get("component_synonym")
                        if gene and gene not in genes:
                            genes.append(gene.upper())
    except Exception as e:
        logger.warning(f"Failed to resolve ChEMBL target {target_chembl_id}: {e}")

    _chembl_target_cache[target_chembl_id] = genes
    return genes


def fetch_dgidb_targets(drug_name: str) -> List[Dict[str, Any]]:
    """Query DGIdb API for drug interactions."""
    targets = []
    url = f"https://dgidb.org/api/v2/interactions.json?drugs={drug_name.lower()}"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            matched = r.json().get("matchedTerms", [])
            for term in matched:
                for inter in term.get("interactions", []):
                    gene = inter.get("geneName")
                    types = inter.get("interactionTypes", [])
                    if gene:
                        targets.append({
                            "gene_symbol": gene.upper(),
                            "source": "dgidb",
                            "details": f"Interaction types: {', '.join(types) if types else 'unspecified'}"
                        })
    except Exception as e:
        logger.warning(f"DGIdb query failed for {drug_name}: {e}")
    return targets


def curate_drug_targets(
    drug_key: str,
    drug_cfg: Dict[str, Any],
    ppi_genes: Set[str] | None = None
) -> pd.DataFrame:
    """
    Curate drug targets by merging seed targets, ChEMBL API, DGIdb, and NDUF* expansion.
    """
    targets_dict: Dict[str, Dict[str, Any]] = {}

    # 1. Seed targets
    for gene in drug_cfg.get("seed_targets", []):
        g = gene.strip().upper()
        targets_dict[g] = {
            "gene_symbol": g,
            "drug": drug_key,
            "sources": ["seed_literature"],
            "details": "Documented primary seed target"
        }

    # 2. ChEMBL REST API
    chembl_id = drug_cfg.get("chembl_id")
    if chembl_id:
        chembl_targets = fetch_chembl_targets(chembl_id)
        for ct in chembl_targets:
            g = ct["gene_symbol"]
            src = ct["source"]
            if g in targets_dict:
                if src not in targets_dict[g]["sources"]:
                    targets_dict[g]["sources"].append(src)
            else:
                targets_dict[g] = {
                    "gene_symbol": g,
                    "drug": drug_key,
                    "sources": [src],
                    "details": ct.get("details", "")
                }

    # 3. DGIdb
    drug_name = drug_cfg.get("name", drug_key)
    dgi_targets = fetch_dgidb_targets(drug_name)
    for dt in dgi_targets:
        g = dt["gene_symbol"]
        src = dt["source"]
        if g in targets_dict:
            if src not in targets_dict[g]["sources"]:
                targets_dict[g]["sources"].append(src)
        else:
            targets_dict[g] = {
                "gene_symbol": g,
                "drug": drug_key,
                "sources": [src],
                "details": dt.get("details", "")
            }

    # 4. Complex I NDUF* expansion if configured
    if drug_cfg.get("include_nduf_subunits", False) and ppi_genes is not None:
        nduf_genes = [g for g in ppi_genes if g.startswith("NDUF")]
        for g in nduf_genes:
            if g in targets_dict:
                if "complex_I_nduf" not in targets_dict[g]["sources"]:
                    targets_dict[g]["sources"].append("complex_I_nduf")
            else:
                targets_dict[g] = {
                    "gene_symbol": g,
                    "drug": drug_key,
                    "sources": ["complex_I_nduf"],
                    "details": "Mitochondrial complex I subunit"
                }

    records = []
    for g, info in targets_dict.items():
        in_ppi = (g in ppi_genes) if ppi_genes is not None else True
        records.append({
            "drug": drug_key,
            "gene_symbol": g,
            "sources": "; ".join(info["sources"]),
            "in_ppi": in_ppi,
            "details": info["details"]
        })

    df = pd.DataFrame(records)
    logger.info(f"Curated {len(df)} targets for {drug_key} ({df['in_ppi'].sum()} present in PPI)")
    return df


def fetch_disease_genes(
    disease_id: str,
    min_score: float = 0.2,
    max_targets: int = 500
) -> pd.DataFrame:
    """
    Retrieve disease-associated genes from Open Targets Platform GraphQL API.
    """
    cache_path = get_cache_dir("raw") / f"opentargets_{disease_id}.parquet"
    if cache_path.exists():
        logger.info(f"Loading cached Open Targets data: {cache_path}")
        return pd.read_parquet(cache_path)

    query = """
    query diseaseTargets($efoId: String!, $size: Int!) {
      disease(efoId: $efoId) {
        id
        name
        associatedTargets(page: {size: $size, index: 0}) {
          count
          rows {
            target {
              id
              approvedSymbol
              approvedName
            }
            score
          }
        }
      }
    }
    """
    url = "https://api.platform.opentargets.org/api/v4/graphql"
    r = requests.post(
        url,
        json={"query": query, "variables": {"efoId": disease_id, "size": max_targets}},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()

    d_info = data.get("data", {}).get("disease")
    if not d_info or not d_info.get("associatedTargets"):
        logger.warning(f"No targets found in Open Targets for disease ID {disease_id}")
        return pd.DataFrame(columns=["gene_symbol", "disease_id", "disease_name", "association_score"])

    disease_name = d_info.get("name", disease_id)
    rows = d_info.get("associatedTargets", {}).get("rows", [])

    records = []
    for row in rows:
        score = float(row.get("score", 0.0))
        if score >= min_score:
            records.append({
                "gene_symbol": row["target"]["approvedSymbol"].upper(),
                "ensembl_id": row["target"]["id"],
                "disease_id": disease_id,
                "disease_name": disease_name,
                "association_score": score
            })

    df = pd.DataFrame(records)
    df.to_parquet(cache_path, index=False)
    logger.info(f"Retrieved {len(df)} disease genes for {disease_name} ({disease_id}) [Score >= {min_score}]")
    return df


def fetch_lincs_expression(drug_name: str) -> pd.DataFrame:
    """
    Retrieve LINCS L1000 chemical perturbation signatures from Enrichr via gseapy.
    Computes gene perturbation scores (+1 for up, -1 for down, or frequency-weighted score).
    """
    cache_path = get_cache_dir("raw") / f"lincs_{drug_name.lower()}.parquet"
    if cache_path.exists():
        logger.info(f"Loading cached LINCS expression data: {cache_path}")
        return pd.read_parquet(cache_path)

    logger.info(f"Extracting LINCS L1000 signatures for {drug_name} via gseapy...")
    lib_up = gseapy.get_library(name="LINCS_L1000_Chem_Pert_up")
    lib_down = gseapy.get_library(name="LINCS_L1000_Chem_Pert_down")

    up_terms = [k for k in lib_up.keys() if drug_name.lower() in k.lower()]
    down_terms = [k for k in lib_down.keys() if drug_name.lower() in k.lower()]

    gene_up_counts: Dict[str, int] = {}
    for term in up_terms:
        for g in lib_up[term]:
            g_sym = g.strip().upper()
            gene_up_counts[g_sym] = gene_up_counts.get(g_sym, 0) + 1

    gene_down_counts: Dict[str, int] = {}
    for term in down_terms:
        for g in lib_down[term]:
            g_sym = g.strip().upper()
            gene_down_counts[g_sym] = gene_down_counts.get(g_sym, 0) + 1

    all_genes = set(gene_up_counts.keys()) | set(gene_down_counts.keys())
    records = []
    total_up_sigs = max(len(up_terms), 1)
    total_down_sigs = max(len(down_terms), 1)

    for g in all_genes:
        up_c = gene_up_counts.get(g, 0)
        down_c = gene_down_counts.get(g, 0)
        # Normalized directional perturbation score: (up_freq - down_freq)
        score = (up_c / total_up_sigs) - (down_c / total_down_sigs)
        records.append({
            "gene_symbol": g,
            "drug": drug_name,
            "up_count": up_c,
            "down_count": down_c,
            "perturbation_score": score,
            "direction": "up" if score > 0 else ("down" if score < 0 else "neutral")
        })

    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values(by="perturbation_score", ascending=False)
        df.to_parquet(cache_path, index=False)
    logger.info(f"Compiled LINCS signature for {drug_name}: {len(df)} perturbed genes ({len(up_terms)} up-sets, {len(down_terms)} down-sets)")
    return df


def append_provenance_entry(
    dataset_id: str,
    source_url: str,
    version: str,
    row_count: int,
    file_size_mb: float,
    details: str
) -> None:
    """Update data/PROVENANCE.md with an accurate audit trail."""
    prov_path = get_project_root() / "data" / "PROVENANCE.md"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"| `{dataset_id}` | {source_url} | {version} | {date_str} | Parquet/TSV | {row_count:,} rows | {details} ({file_size_mb:.2f} MB) |\n"
    
    with open(prov_path, "a", encoding="utf-8") as f:
        f.write(entry)
