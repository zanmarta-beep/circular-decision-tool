# app.py
import json
import streamlit as st
from engine import (
    Inputs, compute_economic, compute_operational, compute_environment, recommend
)

st.set_page_config(page_title="Circular Strategy Advisor", layout="wide")

st.title("Circular Strategy Advisor")
st.caption("Strumento di supporto decisionale per orientarsi tra resale e upcycling")

# Carica configurazione
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

with st.sidebar:
    st.header("Sezione A — Input")
    category = st.selectbox("Categoria prodotto", ["Abbigliamento", "Accessori"])
    segment  = st.selectbox("Fascia prezzo", ["Luxury", "Mass Market"])

    st.markdown("**Parametri prodotto (per Resale/Upcycling)**")
    quality   = st.selectbox("Qualità / Condizione", ["Excellent", "Good", "Worn out"])
    creative  = st.selectbox("Potenziale creativo", ["High", "Medium", "None"])
    material  = st.selectbox("Qualità materiale", ["High", "Medium", "Low"])

    st.divider()
    st.markdown("**Operational feasibility (delta res−up)**")
    st.caption("Usato come tie‑breaker quando entrambe sono economicamente fattibili.")
    oper_delta = st.slider("Δ operativo (Resale − Upcycling)", min_value=-2.0, max_value=2.0, value=0.0, step=0.05)

    run = st.button("Esegui valutazione", use_container_width=True)

if not run:
    st.info("Imposta i parametri nella barra laterale e clicca **Esegui valutazione**.")
    st.stop()

# --- Calcolo
inp = Inputs(
    product_category=category,
    price_segment=segment,
    quality_condition=quality,
    creative_potential=creative,
    material_quality=material
)

econ = compute_economic(inp, cfg)
oper = compute_operational(oper_delta, cfg)
env  = compute_environment(category, segment, cfg)
rec  = recommend(econ, oper, env, cfg)

# --- Sezione B: Economia
st.subheader("Sezione B — Esito economico")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Margin Resale", f"{econ.margin_resale:.2f}")
c2.metric("Cost Resale", f"{econ.cost_resale:.2f}")
c3.metric("Score Resale (margin − cost)", f"{econ.econ_score_resale:.2f}", "PASS" if econ.feasible_resale else "FAIL")
c4.metric("Margin Upcycling", f"{econ.margin_upcycling:.2f}")
c5.metric("Cost Upcycling", f"{econ.cost_upcycling:.2f}")
c6.metric("Score Upcycling (margin − cost)", f"{econ.econ_score_upcycling:.2f}", "PASS" if econ.feasible_upcycling else "FAIL")

# --- Sezione C: Interpretazione economica
st.subheader("Sezione C — Interpretazione economica")
if econ.feasible_upcycling and not econ.feasible_resale:
    st.info("Solo **Upcycling** supera la regola economica (margin − cost > 0).")
elif econ.feasible_resale and not econ.feasible_upcycling:
    st.info("Solo **Resale** supera la regola economica (margin − cost > 0).")
elif econ.feasible_resale and econ.feasible_upcycling:
    st.info("**Entrambe** le strategie superano la regola economica.")
else:
    st.warning("**Nessuna** strategia è economicamente fattibile con i parametri attuali del quadrante.")

# --- Sezione D: Operational feasibility
st.subheader("Sezione D — Operational feasibility")
b1, b2 = st.columns(2)
b1.metric("Δ operativo (Resale − Upcycling)", f"{oper.delta_resale_minus_up:.2f}")
b2.metric("Stato", oper.tag)
st.caption(f"Banda di neutralità ±{cfg['operational_neutral_band']} — fuori banda funge da tie‑breaker se entrambe sono economicamente fattibili.")

# --- Sezione E: Environmental leverage
st.subheader("Sezione E — Environmental leverage")
d1, d2, d3 = st.columns(3)
d1.metric("Impatto Resale (↓ meglio)", f"{env.env_resale:.2f}")
d2.metric("Impatto Upcycling (↓ meglio)", f"{env.env_upcycling:.2f}")
d3.metric("Δ (Resale − Upcycling)", f"{env.delta_resale_minus_up:.2f}")
st.caption(f"Rilevanza ambientale: **{env.tag}** — banda di neutralità ±{cfg['environment_neutral_band']}")

# --- Sezione F: Raccomandazione
st.subheader("Sezione F — Raccomandazione del modello")
if rec.label.startswith("Upcycling"):
    st.success(f"**{rec.label}**")
elif rec.label.startswith("Resale"):
    st.success(f"**{rec.label}**")
elif rec.label == "Both feasible":
    st.info("**Both feasible** — scegliere in base a capacità operative/brand e posizionamento.")
else:
    st.error("**None** — rivedere le assunzioni o intervenire su leve di margin/operatività.")

# --- Sezione G: Motivazioni e trace
st.subheader("Sezione G — Motivazioni e trace")
st.markdown(f"- **Economico**: {rec.rationale_economic}")
st.markdown(f"- **Operativo**: {rec.rationale_operational}")
st.markdown(f"- **Ambientale**: {rec.rationale_environment}")

with st.expander("Decision trace"):
    for step in rec.decision_trace:
        st.write("• " + step)
