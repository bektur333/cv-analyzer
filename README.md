# CV Job Fit & Salary Estimator

An AI pipeline that takes a CV (PDF or DOCX), scores seniority, estimates Czech market salary, and generates a personalised growth roadmap.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

That's it. Open `http://localhost:8501` in your browser.

## Setup

Copy `.env.example` to `.env` and add your [Groq API key](https://console.groq.com) (free):

```
GROQ_API_KEY=your_key_here
```

## Pipeline

```
PDF / DOCX
    │
    ▼
[1] cv_parser.py   — extract raw text (pdfplumber / python-docx)
    │
    ▼
[2] llm.py         — LLM call #1: parse CV into structured JSON
    │               (name, skills, experience_years, education, roles, category, seniority)
    ▼
[3] scorer.py      — rule-based seniority scoring 0–100
    │               Skills (30) + Experience (30) + Education (20) + Seniority (20)
    │             — salary estimation from salary_data.json (Czech IT market benchmarks)
    ▼
[4] llm.py         — LLM call #2 (optional): job fit % against a pasted job description
    │
    ▼
[5] llm.py         — LLM call #3: streaming explanation
                    (Overall assessment · Strengths · Gaps · +30% salary roadmap)
```

## Data approach

Salary ranges live in `salary_data.json` — a synthetic benchmark dataset covering 7 IT role categories × 4 seniority levels, calibrated to Czech market data from Platy.cz and Jobs.cz (2024–2025). The scoring formula maps the 0–100 seniority score to a level (junior / mid / senior / lead), then looks up the range for the candidate's detected role category.

## Tech stack

| Tool | Purpose |
|------|---------|
| [Groq](https://groq.com) | Free LLM API — LLaMA 3 70B |
| Streamlit | Web UI + streaming output |
| pdfplumber | PDF text extraction |
| python-docx | DOCX text extraction |
| Plotly | Score breakdown chart |

## Deploying to Streamlit Community Cloud (free)

1. Push this repo to GitHub (exclude `.env` — it's in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select repo → `app.py`
3. In **Advanced settings → Secrets**, add:
   ```
   GROQ_API_KEY = "your_key_here"
   ```
4. Deploy — you get a public URL to share
