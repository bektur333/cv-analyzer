import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

_api_key = os.environ.get("GROQ_API_KEY")
if not _api_key:
    raise EnvironmentError("GROQ_API_KEY není nastaven. Zkopíruj .env.example do .env a doplň svůj klíč.")

_client = Groq(api_key=_api_key)
MODEL = "llama-3.3-70b-versatile"


def extract_cv_structure(cv_text: str) -> dict:
    prompt = f"""You are a CV parsing expert. Extract structured information from the CV text below.

Return ONLY valid JSON with exactly these fields:
{{
  "name": "candidate full name or Unknown",
  "skills": ["list every technical and soft skill mentioned"],
  "experience_years": <total years of professional work experience as a number>,
  "education_level": "none or bachelor or master or phd",
  "education_field": "field of study or Unknown",
  "roles": [{{"title": "job title", "company": "company name", "years": <years in role as number>}}],
  "role_category": "developer or devops or data or ai_ml or pm or designer or other",
  "seniority_label": "intern or junior or mid or senior or lead or director"
}}

CV TEXT:
{cv_text[:4000]}"""

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return _parse_json(response.choices[0].message.content)


def calculate_job_fit(cv_data: dict, job_description: str) -> dict:
    skills_list = ", ".join(cv_data.get("skills", []))
    prompt = f"""Porovnej profil kandidáta s popisem pracovní pozice níže.
Vrať POUZE platný JSON — žádný jiný text.

KANDIDÁT:
- Dovednosti: {skills_list}
- Zkušenosti: {cv_data.get("experience_years", 0)} let
- Kategorie: {cv_data.get("role_category", "unknown")}
- Seniorita: {cv_data.get("seniority_label", "unknown")}

POPIS POZICE:
{job_description[:2000]}

Vrať:
{{
  "fit_score": <celé číslo 0-100>,
  "matching_skills": ["dovednosti kandidáta které odpovídají pozici"],
  "missing_skills": ["důležité dovednosti z popisu které kandidátovi chybí"],
  "fit_summary": "jedna věta shrnující celkovou shodu"
}}"""

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return _parse_json(response.choices[0].message.content)


def stream_explanation(cv_data: dict, scores, salary: dict, job_description: str = None):
    skills_list = ", ".join(cv_data.get("skills", [])[:15])
    roles_text = "\n".join(
        f"  - {r['title']} ve firmě {r['company']} ({r.get('years', '?')} let)"
        for r in cv_data.get("roles", [])
    ) or "  - Žádné role neuvedeny"

    jd_block = ""
    jd_section = ""
    if job_description:
        jd_block = f"\n\nPOPIS POZICE (pro analýzu shody):\n{job_description[:1500]}"
        jd_section = "\n\n## Shoda s pozicí\n(Jak dobře kandidát odpovídá výše uvedenému popisu? Co by bylo potřeba doplnit?)"

    prompt = f"""Jsi zkušený tech recruiter s hlubokou znalostí českého IT trhu práce (2024/2025).
Piš výhradně česky.

PROFIL KANDIDÁTA:
- Jméno: {cv_data.get("name", "Neznámý")}
- Celková praxe: {cv_data.get("experience_years", 0)} let
- Vzdělání: {cv_data.get("education_level", "neznámé")} v oboru {cv_data.get("education_field", "neznámém")}
- Kategorie role: {cv_data.get("role_category", "neznámá")}
- Seniorita: {cv_data.get("seniority_label", "neznámá")}
- Klíčové dovednosti: {skills_list}
- Pracovní historie:
{roles_text}

SKÓRE SENIORITY: {scores.total}/100
  - Dovednosti:  {scores.skills}/30
  - Zkušenosti:  {scores.experience}/30
  - Vzdělání:    {scores.education}/20
  - Seniorita:   {scores.seniority}/20

ODHAD MZDY: {salary["min"]:,}–{salary["max"]:,} CZK/měsíc
  (Úroveň: {salary["seniority"].upper()}, Kategorie: {salary["category"].upper()}){jd_block}

Napiš strukturovanou analýzu s těmito přesnými nadpisy:

## Celkové hodnocení
(2-3 věty: kdo je tento kandidát a kde stojí na českém IT trhu?)

## Silné stránky
(3 odrážky — konkrétní, odkazuj na skutečné dovednosti a zkušenosti z CV)

## Mezery a oblasti ke zlepšení
(3 odrážky — upřímné mezery, ne obecné rady)

## Plán pro +30 % mzdy
(4-5 konkrétních, realizovatelných kroků přizpůsobených profilu kandidáta a českému IT trhu){jd_section}

Buď přímý a konkrétní. Používej kontext českého trhu (CZK mzdy, česká/EU tech scéna)."""

    stream = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        stream=True,
    )

    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def _parse_json(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if match:
            return json.loads(match.group(1).strip())
        raise ValueError("Nepodařilo se zpracovat odpověď LLM jako JSON.")
