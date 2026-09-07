"""Database seeding script for ACE.

Loads:
  - data/seed/skills.json
  - data/seed/prerequisites.json
  - data/seed/careers.json

Populates the database using SQLAlchemy with idempotent upserts.
Can be executed via CLI:
  python scripts/seed.py
"""
import json
import logging
from pathlib import Path
import sys

# Ensure src/ is in path if executed directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from ace.infrastructure.database.base import Base
from ace.infrastructure.database.models import (
    CareerModel,
    CareerSkillModel,
    PrerequisiteModel,
    SkillModel,
)
from ace.infrastructure.database.session import SessionLocal, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ace.seed")

SEED_DIR = project_root / "data" / "seed"


def seed_database():
    """Seed the database with all skills, prerequisites, and careers."""
    logger.info("Ensuring database schema exists...")
    Base.metadata.create_all(bind=engine)

    skills_file = SEED_DIR / "skills.json"
    prereqs_file = SEED_DIR / "prerequisites.json"
    careers_file = SEED_DIR / "careers.json"

    if not (skills_file.exists() and prereqs_file.exists() and careers_file.exists()):
        raise FileNotFoundError(
            "Seed JSON files not found in data/seed/. Please run scripts/generate_seed_data.py first."
        )

    with open(skills_file, "r", encoding="utf-8") as f:
        skills_data = json.load(f)

    with open(prereqs_file, "r", encoding="utf-8") as f:
        prereqs_data = json.load(f)

    with open(careers_file, "r", encoding="utf-8") as f:
        careers_data = json.load(f)

    db = SessionLocal()
    try:
        # 1. Seed Skills
        logger.info("Seeding %d skills...", len(skills_data))
        for item in skills_data:
            skill = SkillModel(
                id=item["id"],
                name=item["name"],
                category=item["category"],
                description=item.get("description", ""),
                difficulty=item.get("difficulty", 1),
                estimated_hours=item.get("estimated_hours", 0),
            )
            db.merge(skill)
        db.commit()
        logger.info("Skills seeded successfully.")

        # 2. Seed Prerequisites
        logger.info("Seeding %d prerequisites...", len(prereqs_data))
        for item in prereqs_data:
            prereq = PrerequisiteModel(
                skill_id=item["skill_id"],
                requires_skill_id=item["requires_skill_id"],
            )
            db.merge(prereq)
        db.commit()
        logger.info("Prerequisites seeded successfully.")

        # 3. Seed Careers & Requirements
        logger.info("Seeding %d careers and their skill requirements...", len(careers_data))
        for item in careers_data:
            career = CareerModel(
                id=item["id"],
                name=item["name"],
                description=item.get("description", ""),
            )
            db.merge(career)
            db.flush()

            for req in item.get("required_skills", []):
                career_skill = CareerSkillModel(
                    career_id=item["id"],
                    skill_id=req["skill_id"],
                    is_mandatory=req.get("is_mandatory", True),
                    importance=req.get("importance", 1),
                )
                db.merge(career_skill)
        db.commit()
        logger.info("Careers and skill requirements seeded successfully.")

        # Verification summary
        skill_count = db.query(SkillModel).count()
        prereq_count = db.query(PrerequisiteModel).count()
        career_count = db.query(CareerModel).count()
        career_skill_count = db.query(CareerSkillModel).count()

        logger.info("================ SEEDING COMPLETE ================")
        logger.info("Skills in database: %d", skill_count)
        logger.info("Prerequisites in database: %d", prereq_count)
        logger.info("Careers in database: %d", career_count)
        logger.info("Career-Skill links in database: %d", career_skill_count)
        logger.info("==================================================")

    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed database: %s", exc, exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
