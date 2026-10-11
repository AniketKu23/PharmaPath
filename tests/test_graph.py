"""Unit tests for graph construction and scaffold operations (Module M1)."""

import networkx as nx
import pytest

from pharmapath.graph import extract_largest_connected_component


def test_extract_largest_connected_component() -> None:
    G = nx.Graph()
    # Component 1 (size 3)
    G.add_edge("A", "B", score=800, weight=0.8)
    G.add_edge("B", "C", score=750, weight=0.75)
    # Component 2 (size 2)
    G.add_edge("D", "E", score=700, weight=0.7)
    # Isolated node
    G.add_node("F")

    G_lcc, stats = extract_largest_connected_component(G)

    assert G_lcc.number_of_nodes() == 3
    assert set(G_lcc.nodes()) == {"A", "B", "C"}
    assert stats["original_nodes"] == 6
    assert stats["lcc_nodes"] == 3
    assert stats["lcc_node_fraction"] == pytest.approx(0.5)
    assert stats["num_components_pruned"] == 2
    assert nx.is_connected(G_lcc)
