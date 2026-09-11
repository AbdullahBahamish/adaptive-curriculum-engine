# ACE Development Roadmap & Research Milestones

## Completed Milestones (v0.2 Intelligence Upgrade)

- [x] **Probabilistic Learner Modeling**: Integrated 4-parameter Bayesian Knowledge Tracing ($P(L_0), P(T), P(G), P(S)$) with continuous assessment score updating.
- [x] **Local CPU Semantic Indexing**: Integrated `all-MiniLM-L6-v2` with precomputed canonical embeddings (`canonical_skill_embeddings.json`) and sub-millisecond cosine vector lookup.
- [x] **Multi-Factor Weighted Gap Scoring**: Implemented composite gap formulation incorporating importance, target relevance, prerequisite impact, and mastery state.
- [x] **Bounded Candidate Pathway Generation**: Implemented 5 diverse topological generators (Foundational, Goal-First, Quick-Wins, Domain-Clustered, Beam Search) maintaining 0.00% prerequisite violations.
- [x] **Multi-Objective Scoring & Pareto Frontier**: Normalized objective functions across goal alignment, smoothness, gap reduction, time fit, and domain continuity.
- [x] **Structured Explainability**: Algorithmic machine-readable reason codes (`CAREER_MANDATORY`, `PREREQUISITE_CLEARED`, `CRITICAL_UNBLOCKER`, `SMOOTH_STEP`, `QUICK_WIN`) and rich deterministic fallback explainers.
- [x] **Empirical Calibration & Ablation Suite**: Calibrated BKT on 173,912 OULAD student assessment scores in 0.64s; implemented 6-condition quantitative ablation evaluation harness.
- [x] **Comprehensive Test Suite**: 56 unit, property, and benchmark tests passing with 100% success rate.

---

## Future Research & Production Scaling (v0.3+)

- [ ] **Spaced Repetition Review Interleaving**: Interleave scheduled review steps for previously acquired skills using exponential forgetting curves ($R = e^{-t / S}$).
- [ ] **Dynamic Re-planning on Assessment Failures**: Real-time graph branch re-computation when a learner fails a post-module assessment quiz.
- [ ] **Fine-Tuned Domain Embedding Adapter**: Train lightweight LoRA / adapter weights for `all-MiniLM-L6-v2` over software engineering ontology taxonomies.
- [ ] **Multi-Learner Collaborative Graph Feedback**: Calibrate prerequisite edge difficulties and transition probabilities dynamically from aggregate learner pass rates.
