import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScoreBreakdown:
    skills: int      # max 30
    experience: int  # max 30
    education: int   # max 20
    seniority: int   # max 20

    @property
    def total(self) -> int:
        return self.skills + self.experience + self.education + self.seniority


def calculate_scores(cv_data: dict) -> ScoreBreakdown:
    return ScoreBreakdown(
        skills=_score_skills(cv_data.get("skills", [])),
        experience=_score_experience(cv_data.get("experience_years", 0)),
        education=_score_education(cv_data.get("education_level", "none")),
        seniority=_score_seniority(cv_data.get("seniority_label", "junior")),
    )


def estimate_salary(score: int, role_category: str) -> dict:
    data_path = Path(__file__).parent / "salary_data.json"
    with open(data_path) as f:
        salary_data = json.load(f)

    level = _score_to_level(score)
    category = role_category if role_category in salary_data else "other"
    r = salary_data[category][level]
    return {"min": r["min"], "max": r["max"], "seniority": level, "category": category}


# --- private helpers ---

def _score_skills(skills: list) -> int:
    n = len(skills)
    if n >= 20: return 30
    if n >= 15: return 25
    if n >= 10: return 20
    if n >= 7:  return 15
    if n >= 5:  return 10
    if n >= 3:  return 7
    return max(0, n * 2)


def _score_experience(years) -> int:
    y = float(years or 0)
    if y >= 10: return 30
    if y >= 7:  return 25
    if y >= 5:  return 20
    if y >= 3:  return 15
    if y >= 2:  return 10
    if y >= 1:  return 5
    return 2


def _score_education(level: str) -> int:
    return {"none": 5, "bachelor": 12, "master": 17, "phd": 20}.get(
        (level or "none").lower(), 5
    )


def _score_seniority(label: str) -> int:
    return {
        "intern": 2, "junior": 5, "mid": 10, "senior": 15,
        "lead": 18, "principal": 18, "staff": 18,
        "director": 20, "vp": 20, "cto": 20,
    }.get((label or "junior").lower(), 5)


def _score_to_level(score: int) -> str:
    if score >= 76: return "lead"
    if score >= 51: return "senior"
    if score >= 26: return "mid"
    return "junior"
