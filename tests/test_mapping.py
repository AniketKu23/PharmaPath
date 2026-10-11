"""Unit tests for gene symbol mapping and loss rate calculation (Module M1)."""

import gzip
import tempfile
from pathlib import Path
import pytest

from pharmapath.graph import load_protein_to_gene_map


def test_load_protein_to_gene_map() -> None:
    # Create mock protein info gzip file
    mock_data = (
        "#string_protein_id\tpreferred_name\tprotein_size\tannotation\n"
        "9606.ENSP00000000233\tARF5\t180\tADP-ribosylation factor 5\n"
        "9606.ENSP00000001008\tFKBP4\t459\tPeptidyl-prolyl cis-trans isomerase\n"
        "9606.ENSP00000002165\t-\t120\tHypothetical protein without symbol\n"
        "9606.ENSP00000003084\tCFTR\t1480\tCystic fibrosis transmembrane regulator\n"
    )

    with tempfile.NamedTemporaryFile(suffix=".txt.gz", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        with gzip.open(tmp_path, "wt", encoding="utf-8") as gz:
            gz.write(mock_data)

    try:
        mapping, stats = load_protein_to_gene_map(tmp_path)
        assert len(mapping) == 3
        assert mapping["9606.ENSP00000000233"] == "ARF5"
        assert mapping["9606.ENSP00000001008"] == "FKBP4"
        assert mapping["9606.ENSP00000003084"] == "CFTR"
        assert "9606.ENSP00000002165" not in mapping

        assert stats["total_proteins"] == 4
        assert stats["mapped_proteins"] == 3
        assert stats["missing_symbols"] == 1
        assert stats["loss_rate"] == pytest.approx(0.25)
    finally:
        tmp_path.unlink(missing_ok=True)
