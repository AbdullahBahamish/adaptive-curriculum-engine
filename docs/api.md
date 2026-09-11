# ACE REST API Reference

The ACE AI Engine provides RESTful endpoints consumed by client applications (such as C# ASP.NET Core backends or web frontends).

Authentication:
All protected endpoints require the `X-Service-API-Key` HTTP header matching `settings.service_api_key`.

---

## 1. Gap Analysis Endpoint

### `POST /api/v1/gap-analysis`
Computes multi-factor weighted skill gaps between a learner and a target career.

**Request Body**:
```json
{
  "learner_id": "learner_123",
  "career_id": "frontend_developer",
  "confirmed_skills": [
    {"skill_id": "html5"}
  ],
  "mastery_states": {
    "css3": 0.45
  }
}
```

**Response Body**:
```json
{
  "learner_id": "learner_123",
  "career_id": "frontend_developer",
  "career_name": "Frontend Developer",
  "total_required_skills": 12,
  "skills_confirmed": 1,
  "skills_missing": 11,
  "completion_percentage": 8.3,
  "gaps": [
    {
      "skill_id": "js_fundamentals",
      "skill_name": "JavaScript Fundamentals",
      "category": "Frontend",
      "difficulty": 2,
      "estimated_hours": 25,
      "is_mandatory": true,
      "gap_score": 14.8,
      "status": "READY_TO_LEARN",
      "reason_codes": ["CAREER_MANDATORY", "PREREQUISITE_CLEARED", "CRITICAL_UNBLOCKER"],
      "mastery": 0.0,
      "prerequisite_impact": 2.96
    }
  ]
}
```

---

## 2. Learning Path Generation Endpoint

### `POST /api/v1/learning-path`
Generates an ordered, prerequisite-safe, multi-objective personalized learning path.

**Request Body**:
```json
{
  "learner_id": "learner_123",
  "career_id": "frontend_developer",
  "confirmed_skills": ["html5"],
  "pace_preference": "balanced",
  "weekly_hours_budget": 15,
  "return_alternatives": true,
  "explain": true
}
```

**Response Body**:
```json
{
  "learner_id": "learner_123",
  "career_id": "frontend_developer",
  "career_name": "Frontend Developer",
  "total_skills": 11,
  "total_estimated_hours": 240,
  "strategy": "foundational_first",
  "composite_score": 0.8945,
  "objective_scores": {
    "goal_alignment": 0.88,
    "difficulty_smoothness": 0.94,
    "gap_reduction": 0.85,
    "time_budget_fit": 0.90,
    "category_continuity": 0.82
  },
  "steps": [
    {
      "order": 1,
      "skill_id": "prog_logic",
      "skill_name": "Programming Logic",
      "category": "Foundations",
      "estimated_hours": 15,
      "rationale": "Essential foundation for Programming Logic. Unblocks 7 downstream skills.",
      "prerequisites_satisfied": [],
      "reason_codes": ["FOUNDATION_START", "NO_PREREQUISITES", "CRITICAL_UNBLOCKER"],
      "unblocks_count": 7,
      "gap_score": 12.5,
      "difficulty_step": 0
    }
  ],
  "pareto_tradeoffs": [
    {
      "strategy": "career_goal_first",
      "is_recommended": false,
      "composite_score": 0.842,
      "key_strengths": ["High early career goal alignment"],
      "tradeoffs_vs_primary": ["+12% higher early career goal alignment", "-14% steeper difficulty gradient"]
    }
  ],
  "explanation": "## Personalized Curriculum Roadmap: Frontend Developer\n..."
}
```

---

## 3. Mastery Tracking Endpoints

### `POST /api/v1/mastery/update`
Record a quiz or practice observation and update BKT probability.

**Request Body**:
```json
{
  "learner_id": "learner_123",
  "skill_id": "prog_logic",
  "evidence": 0.85,
  "difficulty": 2
}
```

### `GET /api/v1/mastery/{learner_id}`
Retrieve all estimated mastery states for a learner.

---

## 4. Semantic Search Endpoint

### `POST /api/v1/semantic/match`
Retrieve skills matching free-form text using cosine vector similarity.

**Request Body**:
```json
{
  "query": "React state management and hooks",
  "top_k": 5,
  "min_score": 0.35
}
```
