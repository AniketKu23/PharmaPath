"""PharmaPath: Master End-to-End Orchestrator.

Executes all 7 analytical phases sequentially:
  Phase 1: Ingestion & PPI LCC Graph Construction (M1)
  Phase 2: Drug Subnetwork Extraction - 2-Hop & RWR (M2)
  Phase 3: Expression Overlay & Pathway Enrichment (M3)
  Phase 4: Network Analysis, Centralities & Disease Proximity (M4)
  Phase 5: GNN Link Prediction & Leave-Targets-Out Recovery (M5)
  Phase 6: Two-Drug Comparative Network Pharmacology (M6)
  Phase 7: Validation Module & Literature Cross-Check (M7)
"""

from __future__ import annotations

import logging
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("PharmaPath_Master")


def run_phase_script(script_path: Path) -> float:
    """Run a pipeline script as a subprocess and track execution duration."""
    logger.info("=" * 80)
    logger.info("RUNNING PIPELINE STAGE: %s", script_path.name)
    logger.info("=" * 80)

    start_time = time.time()
    result = subprocess.run([sys.executable, str(script_path)], capture_output=False, check=True)
    duration = time.time() - start_time
    logger.info("STAGE %s COMPLETED SUCCESSFULLY in %.2f seconds\n", script_path.name, duration)
    return duration


def main() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    scripts_dir = root_dir / "scripts"

    phases = [
        scripts_dir / "01_build_graph.py",
        scripts_dir / "02_extract_subnetworks.py",
        scripts_dir / "03_enrichment.py",
        scripts_dir / "04_network_analysis.py",
        scripts_dir / "05_gnn_models.py",
        scripts_dir / "06_comparison.py",
        scripts_dir / "07_validation.py",
    ]

    total_start = time.time()
    timing_records = {}

    print("\n" + "#" * 80)
    print("PHARMAPATH: AUTOMATED END-TO-END NETWORK PHARMACOLOGY PIPELINE")
    print("#" * 80 + "\n")

    for p in phases:
        if not p.exists():
            logger.error("Script not found: %s", p)
            sys.exit(1)
        dur = run_phase_script(p)
        timing_records[p.name] = dur

    total_duration = time.time() - total_start
    print("\n" + "=" * 80)
    print("PHARMAPATH END-TO-END EXECUTION COMPLETE")
    print("=" * 80)
    for script_name, dur in timing_records.items():
        print(f"  - {script_name:<30}: {dur:>7.2f} s")
    print(f"Total Pipeline Runtime: {total_duration:.2f} s")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
