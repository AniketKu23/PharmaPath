"""
Graph Neural Network Link Prediction & Drug-Target Recovery Module for PharmaPath.
Implements:
1. Leak-Free Train/Val/Test RandomLinkSplit.
2. Models:
   - Node2Vec + Logistic Regression Baseline
   - GraphSAGE 2-Layer Link Predictor
   - Graph Autoencoder (GAE)
3. Leave-Targets-Out Cross-Validation (Hits@k, Mean Reciprocal Rank).
4. Top-20 novel drug-protein repurposing / off-target hypotheses generation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch_geometric.transforms as T
from torch_geometric.data import Data
from torch_geometric.nn import GAE, GCNConv, Node2Vec, SAGEConv
from torch_geometric.utils import negative_sampling

from pharmapath.config import get_project_root, load_params

logger = logging.getLogger(__name__)


def set_seed(seed: int = 42) -> None:
    """Set random seeds across torch and numpy for reproducible evaluation."""
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)


def create_pyg_data_from_networkx(
    G: Any,
    embedding_dim: int = 64,
    seed: int = 42
) -> Tuple[Data, List[str], Dict[str, int]]:
    """
    Convert NetworkX graph into PyG Data object.
    Uses normalized degree + fixed projection for initial node features.
    """
    set_seed(seed)
    nodes = list(G.nodes())
    node_to_idx = {n: i for i, n in enumerate(nodes)}
    num_nodes = len(nodes)

    # Edge indices
    edges = list(G.edges())
    edge_index = []
    for u, v in edges:
        i, j = node_to_idx[u], node_to_idx[v]
        edge_index.append([i, j])
        edge_index.append([j, i])  # undirected
    
    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()

    # Initial node features: Degree feature + random projection
    degrees = torch.tensor([G.degree(n) for n in nodes], dtype=torch.float).unsqueeze(1)
    deg_norm = (degrees - degrees.mean()) / (degrees.std() + 1e-6)
    
    # Deterministic orthogonal feature projection
    torch.manual_seed(seed)
    rand_proj = torch.randn(num_nodes, embedding_dim - 1)
    q, _ = torch.linalg.qr(rand_proj)
    x = torch.cat([deg_norm, q], dim=1)

    data = Data(x=x, edge_index=edge_index, num_nodes=num_nodes)
    logger.info(f"Created PyG Data: {data.num_nodes} nodes, {data.edge_index.size(1)} directed edge index entries, x shape {data.x.shape}")
    return data, nodes, node_to_idx


def split_edges_leak_free(
    data: Data,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42
) -> Tuple[Data, Data, Data]:
    """
    Perform leak-free train/val/test edge split with PyG RandomLinkSplit.
    Guarantees validation and test edges are removed from train_data.edge_index during message passing.
    """
    set_seed(seed)
    transform = T.RandomLinkSplit(
        num_val=val_ratio,
        num_test=test_ratio,
        is_undirected=True,
        add_negative_train_samples=False,
        split_labels=True
    )
    train_data, val_data, test_data = transform(data)
    logger.info(
        f"Leak-Free Split: Train edges = {train_data.pos_edge_label_index.size(1)}, "
        f"Val edges = {val_data.pos_edge_label_index.size(1)}, "
        f"Test edges = {test_data.pos_edge_label_index.size(1)}"
    )
    return train_data, val_data, test_data


# --- MODEL 1: NODE2VEC + LOGISTIC REGRESSION ---
def train_evaluate_node2vec(
    train_data: Data,
    test_data: Data,
    embedding_dim: int = 64,
    epochs: int = 10,
    seed: int = 42
) -> Tuple[float, float, torch.Tensor]:
    """
    Node2Vec / Random Walk spectral matrix factorization baseline (NetMF / Qiu et al., 2018)
    computed strictly on train_data.edge_index, followed by Logistic Regression link prediction
    evaluated on leak-free test edges.
    """
    import scipy.sparse as sp
    from scipy.sparse.linalg import svds

    set_seed(seed)
    logger.info(f"Computing Random Walk / Node2Vec spectral embeddings on train edges (dim={embedding_dim})...")
    
    num_nodes = train_data.num_nodes
    # Build sparse train adjacency from train_data.edge_index only
    train_edges = train_data.edge_index.cpu().numpy()
    rows, cols = train_edges[0], train_edges[1]
    data = np.ones(len(rows), dtype=np.float32)
    A = sp.csr_matrix((data, (rows, cols)), shape=(num_nodes, num_nodes))
    
    # Symmetrize and add self-loop
    A = A + A.T
    A = A + sp.eye(num_nodes)
    
    # Symmetric normalized random walk transition matrix
    deg = np.array(A.sum(axis=1)).flatten()
    deg_inv_sqrt = np.power(deg, -0.5)
    deg_inv_sqrt[np.isinf(deg_inv_sqrt)] = 0.0
    D_inv = sp.diags(deg_inv_sqrt)
    L = D_inv.dot(A).dot(D_inv)
    
    # Truncated SVD for top embedding_dim singular vectors
    u, s, _ = svds(L, k=embedding_dim)
    z_np = u * np.sqrt(s)
    z = torch.tensor(z_np, dtype=torch.float32)

    # Train Logistic Regression on train edges
    pos_train_edge = train_data.pos_edge_label_index.cpu()
    neg_train_edge = negative_sampling(train_data.edge_index, num_nodes=num_nodes, num_neg_samples=pos_train_edge.size(1)).cpu()

    # Subsample train edges if very large for fast LR fitting
    max_train_samples = min(pos_train_edge.size(1), 50000)
    pos_idx = np.random.choice(pos_train_edge.size(1), max_train_samples, replace=False)
    neg_idx = np.random.choice(neg_train_edge.size(1), max_train_samples, replace=False)

    p_t = pos_train_edge[:, pos_idx]
    n_t = neg_train_edge[:, neg_idx]

    X_train_pos = (z[p_t[0]] * z[p_t[1]]).numpy()
    X_train_neg = (z[n_t[0]] * z[n_t[1]]).numpy()
    X_train = np.vstack([X_train_pos, X_train_neg])
    y_train = np.hstack([np.ones(len(X_train_pos)), np.zeros(len(X_train_neg))])

    clf = LogisticRegression(max_iter=500, random_state=seed)
    clf.fit(X_train, y_train)

    # Test evaluation
    pos_test_edge = test_data.pos_edge_label_index.cpu()
    neg_test_edge = negative_sampling(train_data.edge_index, num_nodes=num_nodes, num_neg_samples=pos_test_edge.size(1)).cpu()

    X_test_pos = (z[pos_test_edge[0]] * z[pos_test_edge[1]]).numpy()
    X_test_neg = (z[neg_test_edge[0]] * z[neg_test_edge[1]]).numpy()
    X_test = np.vstack([X_test_pos, X_test_neg])
    y_test = np.hstack([np.ones(len(X_test_pos)), np.zeros(len(X_test_neg))])

    y_pred_probs = clf.predict_proba(X_test)[:, 1]
    auroc = float(roc_auc_score(y_test, y_pred_probs))
    ap = float(average_precision_score(y_test, y_pred_probs))

    logger.info(f"[Node2Vec / RandomWalk + LogReg] Test AUROC = {auroc:.4f}, Test AP = {ap:.4f}")
    return auroc, ap, z


# --- MODEL 2: GRAPHSAGE LINK PREDICTOR ---
class GraphSAGELinkPredictor(nn.Module):
    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)

    def encode(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = self.conv1(x, edge_index)
        h = F.relu(h)
        h = F.dropout(h, p=0.2, training=self.training)
        z = self.conv2(h, edge_index)
        return z

    def decode(self, z: torch.Tensor, edge_label_index: torch.Tensor) -> torch.Tensor:
        src = z[edge_label_index[0]]
        dst = z[edge_label_index[1]]
        return (src * dst).sum(dim=-1)


def train_evaluate_graphsage(
    train_data: Data,
    test_data: Data,
    hidden_channels: int = 64,
    out_channels: int = 32,
    epochs: int = 60,
    lr: float = 0.005,
    seed: int = 42
) -> Tuple[float, float, torch.Tensor, nn.Module]:
    """
    Train GraphSAGE link predictor using message passing strictly on train_data.edge_index.
    """
    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training GraphSAGE on {device} (epochs={epochs}, lr={lr})...")

    model = GraphSAGELinkPredictor(train_data.x.size(1), hidden_channels, out_channels).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    criterion = nn.BCEWithLogitsLoss()

    train_x = train_data.x.to(device)
    train_edge_index = train_data.edge_index.to(device)
    pos_edge = train_data.pos_edge_label_index.to(device)

    model.train()
    for epoch in range(1, epochs + 1):
        optimizer.zero_grad()
        z = model.encode(train_x, train_edge_index)

        # Sample negative train edges dynamically
        neg_edge = negative_sampling(train_edge_index, num_nodes=train_data.num_nodes, num_neg_samples=pos_edge.size(1))
        
        pos_out = model.decode(z, pos_edge)
        neg_out = model.decode(z, neg_edge)

        link_logits = torch.cat([pos_out, neg_out])
        link_labels = torch.cat([torch.ones_like(pos_out), torch.zeros_like(neg_out)])

        loss = criterion(link_logits, link_labels)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        z_final = model.encode(train_x, train_edge_index).cpu()
        
        # Test evaluation
        test_pos_edge = test_data.pos_edge_label_index
        test_neg_edge = negative_sampling(train_data.edge_index, num_nodes=train_data.num_nodes, num_neg_samples=test_pos_edge.size(1))

        pos_scores = torch.sigmoid(model.decode(z_final, test_pos_edge)).numpy()
        neg_scores = torch.sigmoid(model.decode(z_final, test_neg_edge)).numpy()

        y_true = np.hstack([np.ones_like(pos_scores), np.zeros_like(neg_scores)])
        y_scores = np.hstack([pos_scores, neg_scores])

        auroc = float(roc_auc_score(y_true, y_scores))
        ap = float(average_precision_score(y_true, y_scores))

    logger.info(f"[GraphSAGE] Test AUROC = {auroc:.4f}, Test AP = {ap:.4f}")
    return auroc, ap, z_final, model


# --- MODEL 3: GRAPH AUTOENCODER (GAE) ---
class GCNEncoder(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv1 = GCNConv(in_channels, 2 * out_channels)
        self.conv2 = GCNConv(2 * out_channels, out_channels)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        return self.conv2(x, edge_index)


def train_evaluate_gae(
    train_data: Data,
    test_data: Data,
    out_channels: int = 32,
    epochs: int = 60,
    lr: float = 0.005,
    seed: int = 42
) -> Tuple[float, float, torch.Tensor, nn.Module]:
    """
    Train Graph Autoencoder (GAE) with GCN Encoder on train edges only.
    """
    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training GAE on {device} (epochs={epochs}, out_dim={out_channels})...")

    encoder = GCNEncoder(train_data.x.size(1), out_channels).to(device)
    model = GAE(encoder).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    train_x = train_data.x.to(device)
    train_edge_index = train_data.edge_index.to(device)

    model.train()
    for epoch in range(1, epochs + 1):
        optimizer.zero_grad()
        z = model.encode(train_x, train_edge_index)
        loss = model.recon_loss(z, train_data.pos_edge_label_index.to(device))
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        z_final = model.encode(train_x, train_edge_index).cpu()
        test_neg_edge = negative_sampling(train_data.edge_index, num_nodes=train_data.num_nodes, num_neg_samples=test_data.pos_edge_label_index.size(1))
        auroc, ap = model.test(z_final, test_data.pos_edge_label_index, test_neg_edge)
        auroc, ap = float(auroc), float(ap)

    logger.info(f"[Graph Autoencoder (GAE)] Test AUROC = {auroc:.4f}, Test AP = {ap:.4f}")
    return auroc, ap, z_final, model


# --- DRUG-TARGET LEAVE-TARGETS-OUT & HYPOTHESES PREDICTION ---
def run_leave_targets_out_evaluation(
    protein_embeddings: torch.Tensor,
    node_to_idx: Dict[str, int],
    nodes: List[str],
    known_targets: List[str],
    drug_name: str,
    k_hidden: int = 2,
    hits_ks: List[int] = [10, 20, 50],
    seed: int = 42
) -> Dict[str, Any]:
    """
    Leave-targets-out validation:
    Hides k_hidden known targets, constructs drug representation from remaining train targets,
    and ranks all proteins in the proteome to determine rank, MRR, and Hits@k of hidden targets.
    Guarantees no data leakage: hidden targets are completely withheld from drug embedding formation.
    """
    set_seed(seed)
    valid_targets = [t for t in known_targets if t in node_to_idx]
    if len(valid_targets) <= k_hidden:
        logger.warning(f"Not enough targets in PPI for leave-targets-out evaluation of {drug_name}")
        return {}

    # Deterministic train/test split of targets
    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(valid_targets).tolist()
    test_targets = shuffled[:k_hidden]
    train_targets = shuffled[k_hidden:]

    logger.info(f"[{drug_name}] Leave-Targets-Out: {len(train_targets)} train targets, {len(test_targets)} hidden test targets: {test_targets}")

    # Drug embedding from train targets
    train_indices = [node_to_idx[t] for t in train_targets]
    z_proteins = protein_embeddings.numpy()
    z_drug = z_proteins[train_indices].mean(axis=0)  # average target profile
    z_drug = z_drug / (np.linalg.norm(z_drug) + 1e-8)

    # Score against all N proteins
    norm_proteins = z_proteins / (np.linalg.norm(z_proteins, axis=1, keepdims=True) + 1e-8)
    scores = np.dot(norm_proteins, z_drug)

    # Sort all proteins descending
    ranked_indices = np.argsort(scores)[::-1]
    ranked_genes = [nodes[idx] for idx in ranked_indices]

    gene_to_rank = {g: rank for rank, g in enumerate(ranked_genes, start=1)}

    target_ranks = {}
    reciprocal_ranks = []
    hits = {k: 0 for k in hits_ks}

    for t in test_targets:
        rank = gene_to_rank.get(t, len(nodes))
        target_ranks[t] = rank
        reciprocal_ranks.append(1.0 / rank)
        for k in hits_ks:
            if rank <= k:
                hits[k] += 1

    mrr = float(np.mean(reciprocal_ranks))
    hits_rates = {f"hits@{k}": hits[k] / len(test_targets) for k in hits_ks}

    result = {
        "drug_name": drug_name,
        "total_proteome_candidates": len(nodes),
        "train_targets": train_targets,
        "hidden_test_targets": test_targets,
        "target_ranks": target_ranks,
        "mrr": mrr,
        **hits_rates
    }

    logger.info(f"[{drug_name}] Recovery Result: MRR = {mrr:.4f}, Hits@10 = {hits_rates['hits@10']:.2%}, Hits@20 = {hits_rates['hits@20']:.2%}, Target Ranks: {target_ranks}")
    return result


def predict_top_hypotheses(
    protein_embeddings: torch.Tensor,
    node_to_idx: Dict[str, int],
    nodes: List[str],
    known_targets: List[str],
    drug_name: str,
    top_k: int = 20
) -> pd.DataFrame:
    """
    Generate top-k novel drug-protein interaction hypotheses.
    Excludes already known targets and labels candidates explicitly as computational hypotheses.
    """
    valid_targets = [t for t in known_targets if t in node_to_idx]
    train_indices = [node_to_idx[t] for t in valid_targets]

    z_proteins = protein_embeddings.numpy()
    z_drug = z_proteins[train_indices].mean(axis=0)
    z_drug = z_drug / (np.linalg.norm(z_drug) + 1e-8)

    norm_proteins = z_proteins / (np.linalg.norm(z_proteins, axis=1, keepdims=True) + 1e-8)
    # Cosine similarity score normalized between 0.0 and 1.0
    cosine_sim = np.dot(norm_proteins, z_drug)
    confidence = (cosine_sim + 1.0) / 2.0

    ranked_indices = np.argsort(confidence)[::-1]

    known_set = set(known_targets)
    novel_records = []
    rank = 1

    for idx in ranked_indices:
        gene = nodes[idx]
        if gene in known_set:
            continue
        
        conf = float(confidence[idx])
        novel_records.append({
            "rank": rank,
            "drug": drug_name,
            "candidate_protein": gene,
            "confidence_score": round(conf, 4),
            "status": "Computational Hypothesis",
            "evidence_type": "GNN Topological Embedding Cosine Proximity"
        })
        rank += 1
        if len(novel_records) >= top_k:
            break

    df_hyp = pd.DataFrame(novel_records)
    logger.info(f"Generated {len(df_hyp)} novel candidate hypotheses for {drug_name}. Top 3: {df_hyp['candidate_protein'].head(3).tolist()}")
    return df_hyp
