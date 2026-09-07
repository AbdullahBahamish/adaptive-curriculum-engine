# Curriculum Dataset Sourcing & Taxonomy

## 1. Overview & Pedagogical Standards

The Adaptive Curriculum Engine (ACE) seed dataset provides a curated taxonomy of **112 technical skills**, **144 prerequisite relationships**, and **6 career profiles**. 

The dataset was curated following international educational guidelines and industry-standard competency frameworks:
1. **ACM / IEEE-CS Computing Curricula (CC2020)**: Curriculum guidelines for undergraduate degree programs in computer science, software engineering, and cybersecurity.
2. **NICE Cybersecurity Workforce Framework (NIST SP 800-181)**: Standard work roles and competency requirements for information security analysts and penetration testers.
3. **Industry Engineering Roadmaps (developer-roadmap / roadmap.sh)**: Empirical practitioner consensus on real-world hiring prerequisites and modern cloud/web stacks.

---

## 2. Skill Classification & Taxonomy

Skills are organized into 7 fundamental domains:

| Domain | Slug | Skill Count | Description |
| :--- | :--- | :---: | :--- |
| **CS Foundations** | `cs_foundations` | 12 | Algorithmic logic, discrete mathematics, OS concepts, networking, Git, and database fundamentals. |
| **Frontend Development** | `frontend` | 18 | HTML5, CSS3, JavaScript ES6+, TypeScript, React, Next.js, web accessibility, and performance. |
| **Backend Development** | `backend` | 18 | Python, C# / .NET, SQL, NoSQL, RESTful design, authentication (JWT/OAuth2), caching, and microservices. |
| **Cloud & DevOps** | `cloud_devops` | 18 | Docker, Kubernetes, Terraform IaC, AWS/Azure/GCP core, CI/CD pipelines, and Prometheus observability. |
| **Cybersecurity** | `cybersecurity` | 16 | CIA triad, cryptography, network security, OS hardening, penetration testing, SOC operations, and incident response. |
| **Data & AI/ML** | `data_ai_ml` | 20 | NumPy/Pandas, classical ML, PyTorch deep learning, NLP, Transformers, LLMs, Vector DBs, and RAG systems. |
| **Software Engineering Practices** | `software_engineering_practices` | 10 | Clean Code & SOLID, design patterns, architecture, TDD, Agile/Scrum, and API contract design. |

---

## 3. Cognitive Difficulty & Acquisition Hours

Each skill includes:
- **Difficulty Rating (1 to 5)** mapped to Bloom's Revised Taxonomy:
  - `1 - Beginner`: Remember & Understand (e.g. `html5`, `git_version_control`, `prog_logic`).
  - `2 - Elementary`: Apply basic concepts (e.g. `css3`, `linux_cli`, `database_fundamentals`).
  - `3 - Intermediate`: Analyze & Integrate (e.g. `react_hooks`, `sql_relational_db`, `ci_cd_pipelines`).
  - `4 - Advanced`: Evaluate & Architect (e.g. `microservices_architecture`, `penetration_testing`, `transformer_architectures`).
  - `5 - Expert`: Synthesize large-scale distributed systems.
- **Estimated Acquisition Hours**: Empirically estimated hours of focused deliberate practice required for an average undergraduate student to achieve working competency.

---

## 4. Career Profiles & Coverage

The dataset comprehensively supports all 6 core careers:

| Career ID | Career Title | Total Required Skills | Key Focus Areas |
| :--- | :--- | :---: | :--- |
| `frontend_developer` | Frontend Developer | 20 | TypeScript, React, Next.js, responsive layouts, web accessibility |
| `backend_developer` | Backend Developer | 25 | C#, Python, SQL, REST APIs, microservices, Docker, caching |
| `fullstack_developer` | Full Stack Developer | 23 | React, Next.js, REST APIs, SQL, auth security, Docker |
| `ai_ml_engineer` | AI / ML Engineer | 25 | Linear algebra, PyTorch, transformers, LLMs, RAG, MLOps |
| `cybersecurity_analyst` | Cybersecurity Analyst | 20 | Network defense, Wireshark, SIEM, penetration testing, IAM, GRC |
| `cloud_engineer` | Cloud & DevOps Engineer | 23 | AWS, Kubernetes, Terraform, Docker, CI/CD, Prometheus |

---

## 5. Dataset Persistence & Idempotency

All data resides in version-controlled JSON definitions in `data/seed/`:
- `data/seed/skills.json`
- `data/seed/prerequisites.json`
- `data/seed/careers.json`

The automated database seeder (`scripts/seed.py`) uses SQLAlchemy primary key merging (`Session.merge()`), ensuring that seeding operations are 100% idempotent and can be safely executed repeatedly in local development, CI pipelines, and Docker startup hooks.
