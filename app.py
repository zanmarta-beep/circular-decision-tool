# app.py (v0.2)
import json
import streamlit as st
from engine import (
    Inputs, compute_economic, compute_operational, compute_environment, recommend
)

st.set_page_config(page_title="Circular Strategy Advisor", layout="wide")

st.title("Circular Strategy Advisor")
st.caption("Strumento di supporto decisionale per orientarsi tra resale e upcycling")

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

    run = st.button("Esegui valutazione", use_container_width=True)

if not run:
    st.info("Imposta i parametri e clicca **Esegui valutazione**.")
    st.stop()

inp = Inputs(
    product_category=category,
    price_segment=segment,
    quality_condition=quality,
    creative_potential=creative,
    material_quality=material
)

econ = compute_economic(inp, cfg)
oper = compute_operational(category, segment, cfg)
env  = compute_environment(category, segment, cfg)
rec  = recommend(econ, oper, env, cfg)

# Sezione B — Economico
st.subheader("Sezione B — Esito economico")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Margin Resale", f"{econ.margin_resale:.2f}")
c2.metric("Cost Resale", f"{econ.cost_resale:.2f}")
c3.metric("Score Resale (margin − cost)", f"{econ.econ_score_resale:.2f}", "PASS" if econ.feasible_resale else "FAIL")
c4.metric("Margin Upcycling", f"{econ.margin_upcycling:.2f}")
c5.metric("Cost Upcycling", f"{econ.cost_upcycling:.2f}")
c6.metric("Score Upcycling (margin − cost)", f"{econ.econ_score_upcycling:.2f}", "PASS" if econ.feasible_upcycling else "FAIL")

# Stato economico iniziale (per coerenza con Step D)
if econ.feasible_resale and econ.feasible_upcycling:
    econ_initial = "Both feasible"
elif econ.feasible_resale and not econ.feasible_upcycling:
    econ_initial = "Resale only"
elif econ.feasible_upcycling and not econ.feasible_resale:
    econ_initial = "Upcycling only"
else:
    econ_initial = "None feasible"

# Sezione D — Operatività
st.subheader("Sezione D — Operational feasibility")
S18 = oper.delta_resale_minus_up
band = cfg["operational_neutral_band"]

if econ_initial in ["Resale only", "Upcycling only", "None feasible"]:
    d_status = econ_initial
else:
    if S18 > band:
        d_status = "Resale preferred"
    elif S18 < -band:
        d_status = "Upcycling preferred"
    else:
        d_status = "Neutral"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Adjusted Resale Gap", f"{oper.adjusted_resale_gap:.2f}")
col2.metric("Adjusted Upcycling Gap", f"{oper.adjusted_upcycling_gap:.2f}")
col3.metric("Δ operativo (Resale − Up)", f"{S18:.2f}")
col4.metric("Stato", d_status)

st.caption(f"Formula: Δ = (Resale Econ Gap − Upcycling Adjusted Gap) × Scale Context · Banda ±{band}")
with st.expander("Dettaglio calcolo operatività (per quadrante)"):
    node  = cfg["operational"]["matrix"][category][segment]
    scale = cfg["operational"]["scale_context"][category][segment]

    resale_econ_gap = node["resale"]["econ_gap"]
    up_adj_gap_base = node["upcycling"]["adjusted_gap"]

    details_md = (
        "- **Scale context**: `{scale}`\n"
        "- **Resale** — Econ gap: `{resale}` → Adjusted = `{adj_res}`\n"
        "- **Upcycling** — Adjusted gap (base): `{up_base}` → Adjusted = `{adj_up}`"
    ).format(
        scale=scale,
        resale=resale_econ_gap,
        adj_res=f"{oper.adjusted_resale_gap:.2f}",
        up_base=up_adj_gap_base,
        adj_up=f"{oper.adjusted_upcycling_gap:.2f}",
    )

    st.markdown(details_md)

# Sezione E — Ambientale
st.subheader("Sezione E — Environmental leverage")
d1, d2, d3 = st.columns(3)
d1.metric("Impatto Resale (↓ meglio)", f"{env.env_resale:.2f}")
d2.metric("Impatto Upcycling (↓ meglio)", f"{env.env_upcycling:.2f}")
d3.metric("Δ (Resale − Upcycling)", f"{env.delta_resale_minus_up:.2f}")
st.caption(f"Rilevanza ambientale: **{env.tag}** — banda ±{cfg['environment_neutral_band']}")

# Sezione F — Raccomandazione
st.subheader("Sezione F — Raccomandazione del modello")
if rec.label.startswith("Upcycling"):
    st.success(f"**{rec.label}**")
elif rec.label.startswith("Resale"):
    st.success(f"**{rec.label}**")
elif rec.label == "Both feasible":
    st.info("**Both feasible** — scegliere in base a capacità operative/brand e posizionamento.")
else:
    st.error("**None** — rivedere le assunzioni o intervenire su leve di margin/operatività.")

# Sezione G — Motivazioni e trace
st.subheader("Sezione G — Motivazioni e trace")
st.markdown(f"- **Economico**: {rec.rationale_economic}")
st.markdown(f"- **Operativo**: {rec.rationale_operational}")
st.markdown(f"- **Ambientale**: {rec.rationale_environment}")
with st.expander("Decision trace"):
    st.write(f"Economic initial: {econ_initial}")
    st.write(f"Operational status: {d_status}")
