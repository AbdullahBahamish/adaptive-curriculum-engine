# Dataset Sourcing & Empirical Calibration

ACE integrates real-world educational datasets and precomputed vector stores to balance statistical accuracy with strict local execution efficiency.

---

## 1. OULAD (Open University Learning Analytics Dataset)

ACE leverages assessment records from the Open University Learning Analytics Dataset located in `data/raw/oulad/`:
- **`studentAssessment.csv`** (5.6 MB, 173,912 records): Contains student submission dates, banked credits, and continuous percentage scores across courses.
- **Selective Resource Ingestion**: Rather than loading the unindexed 453MB clickstream file (`studentVle.csv`) which causes memory freezes, ACE selectively parses `studentAssessment.csv` in **0.62 seconds**.

### Empirical Calibration Findings
Running `python scripts/calibrate_bkt.py` analyzes 173,912 scores across 23,291 students:
- $P(L_0)$ (Initial Prior Mastery): **0.2462**
- $P(T)$ (Learn / Transition Rate): **0.4000**
- $P(G)$ (Guess Probability): **0.1800**
- $P(S)$ (Slip Probability): **0.0400**

These empirically grounded parameters are stored in `data/processed/calibrated_bkt_params.json` and initialize the default `BKTModel`.

---

## 2. Canonical Skill Knowledge Base & Precomputed Embeddings

- **`data/seed/skills.json`**: 112 canonical software engineering and computer science skills across 7 domains (Foundations, Frontend, Backend, DevOps, AI/ML, Cloud, Cybersecurity).
- **`data/seed/careers.json`**: Standardized target career profiles (Frontend Developer, Backend Engineer, DevOps Specialist, ML Engineer, etc.) with importance weights.
- **`data/seed/prerequisites.json`**: 120+ directed prerequisite dependency edges validated as a cycle-free DAG.
- **`data/processed/canonical_skill_embeddings.json`**: Precomputed 384-dimensional unit-normalized dense vectors for all 112 skills generated via `all-MiniLM-L6-v2`. Allows zero-model startup and sub-millisecond retrieval on local CPU.
