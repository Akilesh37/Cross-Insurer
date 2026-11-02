# Cross-Insurer Fraud Detection & Claim Deduplication Framework

A privacy-preserving, distributed framework for detecting exact duplicate claims and near-duplicate fraud across multiple competing insurance providers (consortium) without leaking PII or raw claim details.

---

## 🏛 Architecture Overview

```
                                 [ Insurer Nodes ]
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │   API Gateway (Port 8000)     │
                        │   - Reverse Proxy & Routing   │
                        │   - Dashboard Static Host     │
                        └───────┬───────────────┬───────┘
                                │               │
                ┌───────────────┘               └───────────────┐
                ▼                                               ▼
   ┌─────────────────────────┐                     ┌─────────────────────────┐
   │ Ingestion Service (8004)│                     │ Decision Service (8003) │
   │ - Batch Claim JSON      │                     │ - Pipeline Orchestrator │
   │ - Bulk CSV Upload       │                     │ - Postgres & Storage    │
   └────────────┬────────────┘                     └────────────┬────────────┘
                │                                               │
                └───────────────────────┬───────────────────────┘
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                     ▼
        ┌─────────────────────────┐           ┌─────────────────────────┐
        │Fingerprint Service(8001)│           │ Similarity Service(8002)│
        │- Deterministic Normaliz.│           │ - Amount diff heuristic │
        │- SHA-256 Consortium Salt│           │ - Date delta distance   │
        │- PII Hashing (SSN, etc) │           │ - Text fuzzy matching   │
        └─────────────────────────┘           └─────────────────────────┘
                     │                                     │
                     ▼                                     ▼
        ┌─────────────────────────┐           ┌─────────────────────────┐
        │   ClaimRegistry.sol     │           │   PostgreSQL Database   │
        │ - Blockchain Registry   │           │ - Historical Claims DB  │
        │ - DuplicateAlert events │           │ - pgdata persistent vol │
        └─────────────────────────┘           └─────────────────────────┘
```

---

## 🚀 Microservices Breakdown

| Service | Port | Description |
| :--- | :--- | :--- |
| **Gateway** | `8000` | Unified API entrypoint, health diagnostics, and dashboard host. |
| **Fingerprint Service** | `8001` | Canonicalizes claim attributes, hashes PII (SSN), and generates deterministic salted SHA-256 hashes. |
| **Similarity Service** | `8002` | Computes fuzzy similarity scores across amounts, incident dates, and descriptions. |
| **Decision Service** | `8003` | Orchestrates the deduplication pipeline, checks exact registry, runs near-duplicate matching, and registers claims. |
| **Ingestion Service** | `8004` | Batch processing and bulk CSV upload support. |
| **PostgreSQL** | `5432` | Durable database for claim history and exact hash registry. |

---

## ⚙️ Quick Start

### Option A: Run with Docker Compose (Recommended)

Start all services, database, and the web dashboard with a single command:

```bash
docker compose up --build
```

- Open the Dashboard: **[http://localhost:8000](http://localhost:8000)**
- Health check: **[http://localhost:8000/health](http://localhost:8000/health)**

---

### Option B: Run Locally with Virtualenv

1. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Run the end-to-end pipeline test script:
   ```bash
   chmod +x run_all.sh
   ./run_all.sh
   ```

3. Open `dashboard/index.html` in your web browser.

---

## 🧪 Synthetic Dataset Generation & Testing

Generate synthetic claims with Faker:
```bash
python scripts/generate_synthetic_dataset.py --count 1000 --output claims.csv
```

Inject exact and near duplicates with configurable perturbation rates:
```bash
python scripts/inject_duplicates.py --input claims.csv --output final_claims.csv --ground_truth truth.csv --rate 0.15
```

You can then drag and drop `final_claims.csv` directly into the Dashboard's **Batch Ingestion** panel or post to `/ingest/csv`.

---

## 📜 Smart Contract Deployment

To deploy `contracts/ClaimRegistry.sol` to a local test network (e.g., Hardhat, Ganache, Anvil):

```bash
pip install web3
python scripts/deploy_contract.py
```

---

## 🎓 Academic Features & Teacher Presentation Guide

This framework implements publication-grade capabilities designed for academic demonstration and grading:

1. **🕸️ Fraud Ring / Syndicate Network Analytics (`/graph/analytics`)**:
   - Analyzes claims across competing carriers to discover collusive provider rings and multi-carrier double-dippers.
   - Computes degree centrality and categorizes risk levels (`CRITICAL`, `HIGH`, `LOW`).
   - Visualized in the web dashboard using an interactive Cytoscape network graph.

2. **🔬 Explainable AI (XAI) & Semantic NLP Cosine (`/similarity`)**:
   - Replaces raw character matching with TF-IDF Vector Space Model, character n-grams, and domain synonym normalization.
   - Provides a multi-dimensional scorecard: Payout Delta (25%), Temporal Delta (25%), Narrative NLP Cosine (30%), and Entity Overlap (20%).
   - Generates natural language explanations justifying why claims were flagged.

3. **⛓️ Immutable Consortium Blockchain Ledger (`/blockchain/ledger`)**:
   - Simulates smart contract deployment (`ClaimRegistry.sol`).
   - Mints cryptographic blocks with transaction receipts, gas usage, caller addresses (`0x8920...`), and on-chain `DuplicateAlert` events.

4. **🚀 1-Click Multi-Carrier Fraud Attack Simulator (`/simulate/multi_insurer`)**:
   - Choreographed 4-stage demonstration stepping through Insurer A, B, C, and D.
   - Shows live defense at the cryptographic hash layer, semantic AI layer, and graph syndicate layer.

5. **📊 Empirical Benchmark & Evaluation Suite (`/benchmark/stats`)**:
   - Evaluates labeled ground truth test cases.
   - Produces Confusion Matrix (TP, FP, TN, FN), Precision, Recall, F1 Score, and ROC curve coordinates across threshold sweeps.
   - One-click exportable academic evaluation report.

---

## 🛣 Future Roadmap

- [x] Vector Space Model & Semantic NLP embeddings for incident description matching.
- [x] Explainable AI (XAI) multi-vector fraud scorecard.
- [x] Smart Contract event logging (`DuplicateAlert`, `ClaimRegistered`).
- [x] Knowledge Graph and collusive fraud ring detection.
- [x] Empirical evaluation benchmark suite (Confusion Matrix, Precision/Recall, ROC).
- [ ] Multimodal photo verification (perceptual hashing & EXIF metadata on vehicle damage images).
- [ ] Zero-Knowledge Proofs (ZK-SNARKs via ZoKrates/snarkjs) for blinded range proofs.

