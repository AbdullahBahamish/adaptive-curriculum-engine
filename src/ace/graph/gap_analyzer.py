"""Gap Analyzer — computes the skill gap between a learner and a career.

Gap analysis logic (binary model):
  - A skill is a GAP if:
      (a) it is required by the career, AND
      (b) the learner has NOT confirmed they have it.
  - Skills the learner already has are excluded from the learning path.
"""
from ace.domain.career import Career
from ace.domain.learner import LearnerProfile
from ace.domain.skill import Skill, SkillGap


def compute_skill_gaps(
    career: Career,
    learner: LearnerProfile,
    all_skills: dict[str, Skill],
) -> list[SkillGap]:
    """Return the ordered list of skills the learner still needs.

    Args:
        career: The selected target career with required skills.
        learner: The learner profile with confirmed skills.
        all_skills: Mapping of skill_id -> Skill for lookup.

    Returns:
        List of SkillGap objects, one per missing required skill.
        Sorted by importance (highest first) then by skill ID for stability.
    """
    confirmed_ids = learner.confirmed_skill_ids
    gaps: list[SkillGap] = []

    for req in career.required_skills:
        if req.skill_id not in confirmed_ids:
            skill = all_skills.get(req.skill_id)
            if skill is None:
                continue  # Unknown skill — skip gracefully
            gaps.append(
                SkillGap(
                    skill=skill,
                    is_missing=True,
                )
            )

    # Sort: mandatory first, then by importance desc, then alphabetically for stability
    mandatory_reqs = {r.skill_id: (r.is_mandatory, r.importance) for r in career.required_skills}

    def sort_key(gap: SkillGap) -> tuple[int, int, str]:
        is_mandatory, importance = mandatory_reqs.get(gap.skill.id, (True, 1))
        return (0 if is_mandatory else 1, -importance, gap.skill.id)

    gaps.sort(key=sort_key)
    return gaps