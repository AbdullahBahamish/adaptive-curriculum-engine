# ACE API Contract & Integration Specification

## 1. System Architecture & Topology

The **Adaptive Curriculum Engine (ACE)** functions as a standalone intelligence microservice for client applications and upstream systems:

```
[ Client Application / Consumer ]
            │  (HTTPS / JSON)
            ▼
[ ACE Python AI Service (Graph & Curriculum Engine) ] ─── [ PostgreSQL DB ]
```

### Key Principles:
1. **Separation of Concerns**: Upstream services or consumer applications manage user authentication, profile storage, and course progress. ACE manages curriculum graph validation, skill gap analysis, and topological path generation.
2. **Database Isolation**: ACE owns its curriculum and prerequisite database, exposing clean REST APIs.
3. **Deterministic Core with Optional AI**: Core decision-making relies on strict Directed Acyclic Graph (DAG) traversal algorithms to eliminate hallucinations, augmented by optional LLM natural language explanations.

---

## 2. Authentication

All requests to `/api/v1/*` must include the internal service secret in the HTTP header:

```http
X-Service-API-Key: <SERVICE_API_KEY>
```

| Status Code | Reason |
| :--- | :--- |
| `401 Unauthorized` | Missing `X-Service-API-Key` header |
| `403 Forbidden` | Invalid or mismatched API key |

*(Note: `/health` and `/docs` are unauthenticated for monitoring and inspection).*

---

## 3. Endpoints Specification

### 3.1 Skill Gap Analysis

**`POST /api/v1/gap-analysis`**

Calculates missing skills and completion percentage for a given learner against a target career.

#### Request Body
```json
{
  "learner_id": "learner-guid-12345",
  "career_id": "frontend_developer",
  "confirmed_skills": [
    { "skill_id": "html5" },
    { "skill_id": "css3" },
    { "skill_id": "javascript_basics" }
  ]
}
```

#### Response Body (`200 OK`)
```json
{
  "learner_id": "learner-guid-12345",
  "career_id": "frontend_developer",
  "career_name": "Frontend Developer",
  "total_required_skills": 20,
  "skills_confirmed": 3,
  "skills_missing": 17,
  "completion_percentage": 15.0,
  "gaps": [
    {
      "skill_id": "dom_manipulation",
      "skill_name": "DOM Manipulation & Browser Events",
      "category": "frontend",
      "difficulty": 2,
      "estimated_hours": 20,
      "is_mandatory": true
    },
    {
      "skill_id": "javascript_async",
      "skill_name": "Asynchronous JavaScript & Event Loop",
      "category": "frontend",
      "difficulty": 3,
      "estimated_hours": 25,
      "is_mandatory": true
    }
  ]
}
```

---

### 3.2 Personalized Learning Path Generation

**`POST /api/v1/learning-path`**

Computes the topologically sorted, step-by-step curriculum path. Expands gaps to include all transitive prerequisites missing from the learner's profile.

#### Request Body
```json
{
  "learner_id": "learner-guid-12345",
  "career_id": "frontend_developer",
  "confirmed_skills": [
    "html5",
    "css3"
  ]
}
```

#### Response Body (`200 OK`)
```json
{
  "learner_id": "learner-guid-12345",
  "career_id": "frontend_developer",
  "career_name": "Frontend Developer",
  "total_skills": 18,
  "total_estimated_hours": 465,
  "steps": [
    {
      "order": 1,
      "skill_id": "prog_logic",
      "skill_name": "Programming Logic & Problem Solving",
      "category": "cs_foundations",
      "estimated_hours": 20,
      "rationale": "'Programming Logic & Problem Solving' has no prerequisites — start here.",
      "prerequisites_satisfied": []
    },
    {
      "order": 2,
      "skill_id": "javascript_basics",
      "skill_name": "Modern JavaScript (ES6+)",
      "category": "frontend",
      "estimated_hours": 35,
      "rationale": "Requires 'prog_logic' to be completed first.",
      "prerequisites_satisfied": ["prog_logic"]
    },
    {
      "order": 3,
      "skill_id": "dom_manipulation",
      "skill_name": "DOM Manipulation & Browser Events",
      "category": "frontend",
      "estimated_hours": 20,
      "rationale": "Requires 'html5', 'javascript_basics' to be completed first.",
      "prerequisites_satisfied": ["javascript_basics"]
    }
  ]
}
```

---

### 3.3 Administrative Sync Endpoints (Skills, Careers, Prerequisites)

Used by the C# backend to sync or modify curriculum data:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/skills` | List all skills with optional `category` or `search` query |
| `POST` | `/api/v1/skills` | Create a new skill |
| `GET` | `/api/v1/skills/{skill_id}` | Retrieve skill details |
| `PUT` | `/api/v1/skills/{skill_id}` | Update skill attributes |
| `DELETE` | `/api/v1/skills/{skill_id}` | Delete a skill and cascade-delete its edges |
| `GET` | `/api/v1/careers` | List all 6 careers with their required skills |
| `GET` | `/api/v1/careers/{career_id}` | Retrieve single career profile |
| `POST` | `/api/v1/careers` | Create new career profile |
| `POST` | `/api/v1/careers/{career_id}/skills` | Attach/update a skill requirement on a career |
| `DELETE` | `/api/v1/careers/{career_id}/skills/{skill_id}` | Detach skill requirement |
| `GET` | `/api/v1/prerequisites` | List all prerequisite DAG edges |
| `POST` | `/api/v1/prerequisites` | Add prerequisite edge (**automated cycle prevention**) |
| `DELETE` | `/api/v1/prerequisites` | Delete prerequisite edge |

---

## 4. Error Handling Contract

All non-2xx responses follow the standard FastAPI / RFC 7807 error format:

```json
{
  "detail": "Error description or cycle path"
}
```

### Automated Cycle Prevention Example
If an administrator attempts to add an edge that creates circular dependencies (e.g. `B -> A` when `A -> B` exists), ACE aborts the transaction and returns:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "Cannot add prerequisite: introduces a cycle ['skill_a', 'skill_b', 'skill_a']"
}
```
