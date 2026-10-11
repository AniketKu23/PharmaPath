"""Unit tests for closest-distance network proximity and module separation (Module M4 & M6)."""

import networkx as nx
import pytest

from pharmapath.comparison import compute_network_separation
from pharmapath.proximity import (
    calculate_network_proximity,
    compute_closest_distance,
)


def create_toy_graph() -> nx.Graph:
    """Create a toy graph with known shortest paths:

    A --- B --- C --- D --- E
          |           |
          F           G
    """
    G = nx.Graph()
    G.add_edge("A", "B", weight=1.0)
    G.add_edge("B", "C", weight=1.0)
    G.add_edge("C", "D", weight=1.0)
    G.add_edge("D", "E", weight=1.0)
    G.add_edge("B", "F", weight=1.0)
    G.add_edge("D", "G", weight=1.0)
    return G


def test_compute_closest_distance() -> None:
    G = create_toy_graph()
    # Drug targets: A, F
    # Disease genes: D, E
    # Distances:
    # A to D: A-B-C-D = 3
    # A to E: A-B-C-D-E = 4
    # min for A = 3
    # F to D: F-B-C-D = 3
    # F to E: F-B-C-D-E = 4
    # min for F = 3
    # Average closest distance d_c = (3 + 3) / 2 = 3.0
    targets = ["A", "F"]
    disease = ["D", "E"]

    d_c, target_dists = compute_closest_distance(G, targets, disease)

    assert d_c == pytest.approx(3.0)
    assert target_dists["A"] == 3
    assert target_dists["F"] == 3


def test_proximity_permutation_significance() -> None:
    G = create_toy_graph()
    targets = ["A", "B"]
    disease = ["B", "C"]  # Directly overlapping / adjacent

    result = calculate_network_proximity(
        G,
        drug_name="DrugX",
        disease_name="DiseaseY",
        drug_targets=targets,
        disease_genes=disease,
        num_permutations=100,
        random_seed=42,
    )
    # Observed d_c should be small because B is in both (d_c <= 0.5)
    assert result["observed_closest_distance"] <= 0.5
    assert result["z_score"] < 0  # Should be negative (closer than random)


def test_compute_network_separation() -> None:
    G = create_toy_graph()
    targets_a = ["A", "F"]
    targets_b = ["D", "G"]

    sep = compute_network_separation(G, targets_a, targets_b)
    # Target groups are separated along the path
    assert "s_AB_closest" in sep
    assert "s_AB_mean" in sep
    assert sep["n_targets_a"] == 2
    assert sep["n_targets_b"] == 2
