"""Unit tests verifying zero data leakage in GNN link-prediction splits (Module M5)."""

import networkx as nx
import pytest
import torch

from pharmapath.models import create_pyg_data_from_networkx, split_edges_leak_free


def test_link_split_zero_leakage() -> None:
    # Create a synthetic graph with 50 nodes and 150 edges
    G = nx.erdos_renyi_graph(n=50, p=0.15, seed=42)
    while not nx.is_connected(G):
        G = nx.erdos_renyi_graph(n=50, p=0.15, seed=42)

    data, nodes, node_to_idx = create_pyg_data_from_networkx(G, embedding_dim=16, seed=42)

    train_data, val_data, test_data = split_edges_leak_free(
        data,
        val_ratio=0.1,
        test_ratio=0.1,
        seed=42,
    )

    # Extract canonical undirected edge sets {(min(u,v), max(u,v))}
    def extract_canonical_edges(edge_label_index: torch.Tensor) -> set:
        edges = set()
        for i in range(edge_label_index.size(1)):
            u = int(edge_label_index[0, i])
            v = int(edge_label_index[1, i])
            edges.add((min(u, v), max(u, v)))
        return edges

    train_edges = extract_canonical_edges(train_data.pos_edge_label_index)
    val_edges = extract_canonical_edges(val_data.pos_edge_label_index)
    test_edges = extract_canonical_edges(test_data.pos_edge_label_index)

    # 1. Strict pairwise disjointness
    train_val_overlap = train_edges.intersection(val_edges)
    train_test_overlap = train_edges.intersection(test_edges)
    val_test_overlap = val_edges.intersection(test_edges)

    assert len(train_val_overlap) == 0, f"Leakage detected between train and val: {train_val_overlap}"
    assert len(train_test_overlap) == 0, f"Leakage detected between train and test: {train_test_overlap}"
    assert len(val_test_overlap) == 0, f"Leakage detected between val and test: {val_test_overlap}"

    # 2. Message passing graph isolation:
    # Test edges must NEVER be present in train_data.edge_index (used for message passing)
    train_mp_edges = extract_canonical_edges(train_data.edge_index)
    test_in_train_mp = test_edges.intersection(train_mp_edges)
    assert len(test_in_train_mp) == 0, f"Test edges leaked into training message passing graph! {test_in_train_mp}"

    # 3. Negative test edge disjointness
    test_neg_edges = extract_canonical_edges(test_data.neg_edge_label_index)
    assert len(test_edges.intersection(test_neg_edges)) == 0, "Negative test edges overlap with positive test edges!"
