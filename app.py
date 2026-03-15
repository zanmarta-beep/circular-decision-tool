# app.py (v0.2.1)
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

# -------------------------------
# Sidebar — Sezione A (Input)
# -------------------------------
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

# -------------------------------
# Calcoli core
# -------------------------------
inp  = Inputs(
    product_category=category,
    price_segment=segment,
    quality_condition=quality,
    creative_potential=creative,
    material_quality=material
)

econ = compute_economic(inp, cfg)
oper = compute_operational(category, segment, cfg)   # v0.2: (category, segment, cfg)
env  = compute_environment(category, segment, cfg)

# -------------------------------
# Sezione B — Esito economico
# -------------------------------
st.subheader("Sezione B — Esito economico")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Margin Resale", f"{econ.margin_resale:.2f}")
c2.metric("Cost Resale", f"{econ.cost_resale:.2f}")
c3.metric("Score Resale (margin − cost)", f"{econ.econ_score_resale:.2f}", "PASS" if econ.feasible_resale else "FAIL")
c4.metric("Margin Upcycling", f"{econ.margin_upcycling:.2f}")
c5.metric("Cost Upcycling", f"{econ.cost_upcycling:.2f}")
c6.metric("Score Upcycling (margin − cost)", f"{econ.econ_score_upcycling:.2f}", "PASS" if econ.feasible_upcycling else "FAIL")

# Esito iniziale (B) — ci serve per la logica di D
if econ.feasible_resale and econ.feasible_upcycling:
    econ_initial = "Both feasible"
elif econ.feasible_resale and not econ.feasible_upcycling:
    econ_initial = "Resale only"
elif econ.feasible_upcycling and not econ.feasible_resale:
    econ_initial = "Upcycling only"
else:
    econ_initial = "None feasible"

# -------------------------------
# Sezione D — Operational feasibility (deterministica, allineata a Excel)
# -------------------------------
st.subheader("Sezione D — Operational feasibility")

S18  = oper.delta_resale_minus_up
band = cfg["operational_neutral_band"]

# Logica Sezione D (come Excel): se Step B non è Both feasible, D ripete l'esito economico
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

st.caption("Formula: Δ = (Resale Econ Gap − Upcycling Adjusted Gap) × Scale Context · Banda ±{b}".format(b=band))

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

# -------------------------------
# Sezione E — Environmental leverage (informativa)
# -------------------------------
st.subheader("Sezione E — Environmental leverage")
d1, d2, d3 = st.columns(3)
d1.metric("Impatto Resale (↓ meglio)", f"{env.env_resale:.2f}")
d2.metric("Impatto Upcycling (↓ meglio)", f"{env.env_upcycling:.2f}")
d3.metric("Δ (Resale − Upcycling)", f"{env.delta_resale_minus_up:.2f}")
st.caption("Rilevanza ambientale: **{t}** — banda ±{b}".format(t=env.tag, b=cfg["environment_neutral_band"]))

# -------------------------------
# Sezione F — Raccomandazione del modello
#   >>> PRENDE IL RISULTATO DALLA SEZIONE D <<<
# -------------------------------
# Mappa D → F
if d_status in ["Resale only", "Upcycling only", "None feasible"]:
    final_label = d_status
elif d_status == "Resale preferred":
    final_label = "Resale preferred"
elif d_status == "Upcycling preferred":
    final_label = "Upcycling preferred"
else:  # "Neutral"
    final_label = "Both feasible"

# Testo di supporto (executive hint)
if final_label == "Resale preferred":
    final_hint = "preferenza operativa verso Resale (fuori banda)."
elif final_label == "Upcycling preferred":
    final_hint = "preferenza operativa verso Upcycling (fuori banda)."
elif final_label == "Both feasible":
    final_hint = "scegliere in base a capacità operative/brand e posizionamento."
elif final_label == "None feasible":
    final_hint = "rivedere assunzioni, costi o leva di margin."
else:
    # "Resale only" o "Upcycling only"
    final_hint = "esito economico vincolante (gating)."

st.subheader("Sezione F — Raccomandazione del modello")
if final_label in ["Resale only", "Upcycling only"]:
    st.success(f"**{final_label}** — {final_hint}")
elif final_label in ["Resale preferred", "Upcycling preferred"]:
    st.info(f"**{final_label}** — {final_hint}")
elif final_label == "Both feasible":
    st.info(f"**Both feasible** — {final_hint}")
else:  # None feasible
    st.error(f"**None feasible** — {final_hint}")

# (Facoltativo: se vuoi lasciare traccia dettagliata)
with st.expander("Decision trace"):
    st.write(f"Economic initial (B): {econ_initial}")
    st.write(f"Operational (D): {d_status}")
    st.write(f"Environmental (E): {env.tag}")
