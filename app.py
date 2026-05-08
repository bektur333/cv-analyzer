import streamlit as st
import plotly.graph_objects as go

import cv_parser
import scorer
import llm

st.set_page_config(
    page_title="Analyzátor CV | Hodnocení & Odhad Mzdy",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Analyzátor CV — Hodnocení & Odhad Mzdy")
st.caption("Nahraj CV → získej skóre seniority, odhad mzdy na českém trhu a osobní plán růstu.")
st.divider()

col_in, col_hint = st.columns([1, 1], gap="large")

with col_in:
    uploaded_file = st.file_uploader(
        "Nahraj CV (PDF nebo DOCX)",
        type=["pdf", "docx"],
    )
    with st.expander("📋 Vložit popis pracovní pozice  *(volitelné — aktivuje skóre shody)*"):
        job_description = st.text_area(
            "job_description",
            height=180,
            placeholder="Vlož sem celý text pracovní nabídky...",
            label_visibility="collapsed",
        )
    analyze = st.button(
        "🔍 Analyzovat CV",
        type="primary",
        disabled=uploaded_file is None,
        use_container_width=True,
    )

with col_hint:
    if not uploaded_file:
        st.info(
            "**Co dostaneš:**\n\n"
            "- 📊 Skóre seniority (0–100) rozdělené podle dovedností, zkušeností, vzdělání a úrovně role\n"
            "- 💰 Odhad mzdy podle benchmarků českého IT trhu\n"
            "- 🎯 Skóre shody s pozicí % (pokud vložíš popis práce)\n"
            "- 🧠 AI analýza: silné stránky, mezery a konkrétní plán pro +30 % mzdy"
        )


def _render_metrics(cv_data, scores, salary, fit_data):
    st.divider()
    st.subheader(f"Výsledky pro: {cv_data.get('name', 'Kandidát')}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Skóre seniority", f"{scores.total} / 100")
    m2.metric("Tržní úroveň", salary["seniority"].capitalize())
    m3.metric("Mzda od", f"{salary['min']:,} CZK/měs.")
    m4.metric("Mzda do", f"{salary['max']:,} CZK/měs.")

    if fit_data:
        st.metric(
            "Shoda s pozicí",
            f"{fit_data.get('fit_score', 0)} %",
            help=fit_data.get("fit_summary", ""),
        )

    st.subheader("Rozložení skóre")
    labels = ["Dovednosti\n(max 30)", "Zkušenosti\n(max 30)", "Vzdělání\n(max 20)", "Seniorita\n(max 20)"]
    values = [scores.skills, scores.experience, scores.education, scores.seniority]
    maxes = [30, 30, 20, 20]
    colors = [
        "#4CAF50" if v / m >= 0.7 else "#FF9800" if v / m >= 0.4 else "#F44336"
        for v, m in zip(values, maxes)
    ]
    fig = go.Figure(go.Bar(
        x=labels, y=values, marker_color=colors,
        text=[f"{v}/{m}" for v, m in zip(values, maxes)],
        textposition="auto",
    ))
    fig.update_layout(
        yaxis=dict(range=[0, 35], title="Skóre"),
        showlegend=False, height=320,
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    if fit_data:
        st.subheader("Detail shody s pozicí")
        fa, fb = st.columns(2)
        with fa:
            if fit_data.get("matching_skills"):
                st.success("✅ **Shoda:** " + ", ".join(fit_data["matching_skills"]))
        with fb:
            if fit_data.get("missing_skills"):
                st.warning("⚠️ **Chybí:** " + ", ".join(fit_data["missing_skills"]))


if analyze and uploaded_file:
    try:
        with st.status("🔄 Spouštím analytickou pipeline...", expanded=True) as status:
            st.write("📄 **Krok 1/4** — Načítám dokument CV...")
            cv_text = cv_parser.extract_text_from_upload(uploaded_file)

            st.write("🤖 **Krok 2/4** — Extrahuji strukturu pomocí LLM...")
            cv_data = llm.extract_cv_structure(cv_text)

            st.write("📊 **Krok 3/4** — Počítám skóre seniority...")
            scores = scorer.calculate_scores(cv_data)
            salary = scorer.estimate_salary(scores.total, cv_data.get("role_category", "other"))

            fit_data = None
            jd = job_description.strip() if job_description else ""
            if jd:
                st.write("🎯 **Krok 4/4** — Počítám shodu s pozicí...")
                fit_data = llm.calculate_job_fit(cv_data, jd)
            else:
                st.write("⏭️ **Krok 4/4** — Přeskočeno (nebyl zadán popis pozice)")

            status.update(label="✅ Pipeline dokončena!", state="complete", expanded=False)

        _render_metrics(cv_data, scores, salary, fit_data)

        st.subheader("AI Analýza & Doporučení")
        explanation = st.write_stream(llm.stream_explanation(cv_data, scores, salary, jd or None))

        st.session_state.results = {
            "cv_data": cv_data,
            "scores": scores,
            "salary": salary,
            "fit_data": fit_data,
            "explanation": explanation,
        }

    except ValueError as e:
        st.error(f"❌ {e}")
    except Exception as e:
        st.error(f"❌ Neočekávaná chyba: {e}")
        with st.expander("Detail chyby"):
            st.exception(e)

elif st.session_state.get("results"):
    r = st.session_state.results
    _render_metrics(r["cv_data"], r["scores"], r["salary"], r["fit_data"])
    st.subheader("AI Analýza & Doporučení")
    st.markdown(r["explanation"])
