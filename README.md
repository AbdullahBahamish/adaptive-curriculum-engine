# Adaptive Curriculum Engine (ACE)

> **Standalone AI Intelligence Engine for Personalized Academic & Career Roadmaps**  
> Fast, deterministic Directed Acyclic Graph (DAG) topological curriculum sequencing, semantic skill matching, and gap analysis engine.

[![CI Pipeline](https://github.com/AbdullahBahamish/adaptive-curriculum-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/AbdullahBahamish/adaptive-curriculum-engine/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.4+-orange.svg)](https://networkx.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Executive Summary

Many students and aspiring software professionals struggle when preparing for technical careers because they lack a clear understanding of role competencies and prerequisite dependencies. Studying topics in an unsuitable order leads to cognitive overload, overlooked fundamentals, and high abandonment rates.

**ACE** is a standalone, production-ready AI and curriculum optimization engine. It analyzes a learner's confirmed competencies against target career profiles, identifies missing skills, resolves deep transitive prerequisite chains, and computes mathematically sound, topologically sorted learning sequences.

```
┌─────────────────────────────────────────────────────────────┐
│                 Client Applications / Consumers             │
│            (Web / Mobile Apps, EdTech Platforms, LMS)       │
└──────────────────────────────┬──────────────────────────────┘
                               │  REST API (X-Service-API-Key)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Adaptive Curriculum Engine (ACE)                │
│                                                             │
│   ┌──────────────────────────┐   ┌──────────────────────┐   │
│   │ Graph Engine (DAG / DFS) │   │ AI & Semantic Layer  │   │
│   │ • Kahn's Topological Sort│   │ • Sentence-Xformers  │   │
│   │ • Transitive Closure     │   │ • LLM Explainers     │   │
│   │ • Cycle Detection O(V+E) │   │ • Skill Matcher      │   │
│   └────────────┬─────────────┘   └──────────┬───────────┘   │
└────────────────┼────────────────────────────┼───────────────┘
                 ▼                            ▼
      [ PostgreSQL Database ]     [ External LLM APIs / Local ]
```

---

- **Probabilistic Learner Modeling (BKT)**: Replaces binary knowledge with standard 4-parameter Bayesian Knowledge Tracing ($P(L_0), P(T), P(G), P(S)$) and continuous confidence tracking, empirically calibrated on 173,912 student scores.
- **Bounded Candidate Pathway Generation**: Generates 5 diverse topological pathway archetypes (*Foundational-First*, *Career-Goal-First*, *Quick-Wins*, *Domain-Clustered*, *Bounded Beam Search*) with a strict **0.00% prerequisite violation rate**.
- **Multi-Objective Scoring & Pareto Frontier**: Optimizes paths across 5 normalized pedagogical objectives (Goal Alignment, Gap Reduction, Difficulty Smoothness, Time Fit, Domain Continuity) and identifies non-dominated Pareto alternatives with human-readable trade-off explanations.
- **Sub-Millisecond Vector Retrieval**: CPU-optimized `all-MiniLM-L6-v2` dense vector index with precomputed canonical embeddings, enabling instant startup and $< 0.5\text{ms}$ cosine similarity search.
- **Multi-Factor Weighted Gap Analysis**: Computes prioritized skill gaps incorporating career weight, target relevance, prerequisite centrality impact ($1 + \ln(1 + |\text{Descendants}|)$), and mastery state.
- **Deterministic Explainability**: Generates machine-readable reason codes (`CAREER_MANDATORY`, `PREREQUISITE_CLEARED`, `CRITICAL_UNBLOCKER`, `SMOOTH_STEP`, `QUICK_WIN`) and rich structured markdown walkthroughs with zero LLM dependency.
- **Automated Cycle Detection & Strict DAG Invariants**: Enforces cycle-free Directed Acyclic Graphs ($O(V + E)$) with memoized transitive closures and depth metrics.
- **Curated Multi-Domain Dataset**: Pre-populated with **112 technical skills**, **144 prerequisite edges**, and **6 industry career tracks**.


---

## 3. Supported Career Tracks

ACE comes pre-loaded with comprehensive skill benchmarks across 6 core industry roles:

1. **Frontend Developer** (`frontend_developer`) — HTML5, CSS3, Modern JS, TypeScript, React, Next.js, Web Accessibility, Performance.
2. **Backend Developer** (`backend_developer`) — Python, C# / .NET Core, Relational SQL, NoSQL, REST APIs, Microservices, Docker.
3. **Full Stack Developer** (`fullstack_developer`) — End-to-end integration across Next.js frontend, REST APIs, SQL, Docker, and CI/CD.
4. **AI / ML Engineer** (`ai_ml_engineer`) — Linear Algebra, Calculus, Scikit-Learn, PyTorch, Transformers, LLMs, Vector DBs, RAG.
5. **Cybersecurity Analyst** (`cybersecurity_analyst`) — Network Defense, OS Hardening, Wireshark, Penetration Testing, SOC SIEM, Incident Response.
6. **Cloud & DevOps Engineer** (`cloud_engineer`) — AWS/Azure/GCP, Docker, Kubernetes, Terraform IaC, GitHub Actions CI/CD, Prometheus.

---

## 4. Empirical Benchmark & Ablation Study

ACE was evaluated across 6 experimental conditions on a cohort of 50 simulated learners with varying competencies, mastery levels, and pacing preferences:

| Experimental Condition | Prereq Violations | Goal Alignment@10 | Smoothness Index | NDCG@10 | Latency (CPU) | RAM Overhead |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **C1: Baseline (v0.1)** | **0.00%** | 0.8621 | 0.8861 | 0.5719 | 2.75 ms | 2.81 MB |
| **C2: Baseline + Semantic** | **0.00%** | 0.8621 | 0.8861 | 0.5719 | 2.83 ms | 2.81 MB |
| **C3: Baseline + BKT** | **0.00%** | 0.8584 | 0.8809 | 0.5332 | 3.01 ms | 2.81 MB |
| **C4: BKT + Weighted Gaps** | **0.00%** | 0.8584 | 0.8809 | 0.5332 | 2.43 ms | 2.81 MB |
| **C5: Candidate Gen + Ranking** | **0.00%** | **0.8784** | **0.9135** | **0.7519** | 31.66 ms | 2.81 MB |
| **C6: Full Hybrid System (Pareto)** | **0.00%** | 0.8711 | 0.8945 | 0.6627 | 56.53 ms | 2.81 MB |

- **Zero Prerequisite Violations**: Strict DAG invariance ($0.00\%$) across all conditions and candidates.
- **NDCG@10 Improvement**: +31.5% improvement in ranking quality over baseline.
- **Cognitive Smoothness**: Increases from 0.8861 to 0.9135, eliminating steep difficulty spikes.
- **Ultra-Low Memory Footprint**: Minimal 2.81 MB RAM overhead, well below the 150MB local constraint ceiling.

---

## 5. Quickstart Guide

### Option A: Using Docker Compose (Recommended)

Start PostgreSQL and the ACE AI service with a single command:

```bash
docker compose up -d --build
```

The service will automatically:
1. Initialize the PostgreSQL database container.
2. Run schema migrations via Alembic.
3. Seed the 112 skills, 144 prerequisites, and 6 career tracks.
4. Expose the REST API at `http://localhost:8000`.
5. Provide interactive Swagger API documentation at `http://localhost:8000/docs`.

---

### Option B: Local Virtual Environment

#### 1. Clone & Setup
```bash
git clone https://github.com/AbdullahBahamish/adaptive-curriculum-engine.git
cd adaptive-curriculum-engine

# Requires Python 3.13
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install --upgrade pip
pip install -e ".[dev]"
```

#### 2. Configure Environment
```bash
cp .env.example .env
```

#### 3. Generate & Seed Data
```bash
# Validate and generate seed JSON files
python scripts/generate_seed_data.py

# Seed into database
python scripts/seed.py
```

#### 4. Run Development Server
```bash
uvicorn ace.api.main:app --reload --port 8000
```

---

## 5. API Reference

All protected endpoints require the service secret header:  
`X-Service-API-Key: <SERVICE_API_KEY>`

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health and version status |
| `POST` | `/api/v1/gap-analysis` | Compute missing skills & readiness percentage |
| `POST` | `/api/v1/learning-path` | Generate topologically ordered curriculum path |
| `GET` | `/api/v1/skills` | List skills (filter by category / search) |
| `POST` | `/api/v1/skills` | Register a new skill |
| `GET` | `/api/v1/careers` | List all careers and required skills |
| `POST` | `/api/v1/prerequisites` | Add prerequisite edge (**with automated cycle prevention**) |

*For complete request/response contracts and JSON schemas, see [docs/api-contract.md](docs/api-contract.md).*

---

## 6. Testing & Quality Assurance

ACE includes a comprehensive automated test suite spanning graph algorithms, database repositories, seed integrity, and REST API routes:

```bash
# Run full test suite
pytest -v

# Run with test coverage report
pytest --cov=ace --cov-report=term-missing
```

All 27 automated tests run in sub-second execution (< 0.6s) using in-memory SQLite and mock dependencies.

---

## 7. Architecture & Documentation

- [System Architecture & API Integration Contract](docs/api-contract.md)
- [Algorithmic Graph Theory & Complexity Analysis](docs/graph-algorithm.md)
- [Dataset Taxonomy & Sourcing Framework](docs/dataset-sourcing.md)

---

## 8. License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
