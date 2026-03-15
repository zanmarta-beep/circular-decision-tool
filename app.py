# app.py (v0.2.3) — English UI + end-of-section badges w/ color rules
import json
import streamlit as st
from typing import Literal
from engine import (
    Inputs, compute_economic, compute_operational, compute_environment
)

st.set_page_config(page_title="Circular Strategy Advisor", layout="wide")

st.title("Circular Strategy Advisor")
st.caption("Decision-support tool to orient between resale and upcycling")

# -------------------------------
# Helpers for end-of-section badges
# -------------------------------
Tone = Literal["success", "info", "warn", "error", "neutral"]

def _box(label: str, subtitle: str = "", tone: Tone = "info"):
    """
    Unified badge renderer.
    tone: success=green, info=blue, warn=yellow, error=red, neutral=grey
    """
    content = f"**{label}**" + (f" — {subtitle}" if subtitle else "")
    if tone == "success":
        st.success(content)
    elif tone == "error":
        st.error(content)
    elif tone == "warn":
        st.warning(content)
    elif tone == "neutral":
        st.caption(content)
    else:  # info
        st.info(content)

def badge_economic_label(econ_initial: str, econ) -> tuple[str, str, Tone]:
    """
    End label for Section B (Economic outcome).
    Colors remain as defined earlier for Section B:
      - Green: Resale only / Upcycling only
      - Blue:  Both feasible
      - Red:   None feasible
    """
    if econ_initial == "Resale only":
        return ("Resale only", "Economic pass: margin − cost (Resale) > 0", "success")
    if econ_initial == "Upcycling only":
        return ("Upcycling only", "Economic pass: margin − cost (Upcycling) > 0", "success")
    if econ_initial == "Both feasible":
        return ("Both feasible", "Both strategies meet margin − cost > 0", "info")
    return ("None feasible", "No strategy meets margin − cost > 0", "error")

def badge_operational_label(econ_initial: str, d_status: str, S18: float, band: float) -> tuple[str, str, Tone]:
    """
    End label for Section D (Operational feasibility).
    Your requested colors:
      - Green:  Resale only / Upcycling only / Resale preferred / Upcycling preferred
      - Blue:   Neutral
      - Red:    None feasible (kept as red to flag failure)
    """
    # Economic gating: if B != Both feasible, D repeats B
    if econ_initial in ["Resale only", "Upcycling only", "None feasible"]:
        label = econ_initial
        subtitle = "Economic gating."
        tone = "error" if label == "None feasible" else "success"
        return (label, subtitle, tone)

    # Otherwise use Δ
    if d_status == "Resale preferred":
        return ("Resale preferred", f"Δ = {S18:.2f} · band ±{band}", "success")
    if d_status == "Upcycling preferred":
        return ("Upcycling preferred", f"Δ = {S18:.2f} · band ±{band}", "success")
    return ("Neutral", f"Δ = {S18:.2f} · band ±{band}", "info")

def badge_environment_label(env, band: float) -> tuple[str, str, Tone]:
    """
    End label for Section E (informative).
      - Blue:   Preference resale/upcycling
      - Grey:   Neutral
    """
    if env.tag == "Preference resale":
        return ("Environmental: Preference resale", f"Δ res−up = {env.delta_resale_minus_up:.2f} · band ±{band}", "info")
    if env.tag == "Preference upcycling":
        return ("Environmental: Preference upcycling", f"Δ res−up = {env.delta_resale_minus_up:.2f} · band ±{band}", "info")
    return ("Environmental: Neutral", f"Δ res−up = {env.delta_resale_minus_up:.2f} · band ±{band}", "neutral")

def badge_final_from_operational(d_status: str) -> tuple[str, str, Tone]:
    """
    Section F mirrors Section D (as requested).
      - Green:  Resale only / Upcycling only / Resale preferred / Upcycling preferred
      - Blue:   Both feasible (since D=Neutral)
      - Red:    None feasible
    """
    if d_status in ["Resale only", "Upcycling only"]:
        return (d_status, "Economic gating.", "success")
    if d_status in ["Resale preferred", "Upcycling preferred"]:
        return (d_status, "Operational preference (Δ out of band).", "success")
    if d_status == "None feasible":
        return ("None feasible", "Revisit assumptions, costs or margin levers.", "error")
    return ("Both feasible", "Choose based on operational capacity and brand positioning.", "info")

# -------------------------------
# Load configuration
# -------------------------------
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

# -------------------------------
# Sidebar — Section A (Inputs)
# -------------------------------
with st.sidebar:
    st.header("Section A — Inputs")
    category = st.selectbox("Product category", ["Abbigliamento", "Accessori"])
    segment  = st.selectbox("Price segment", ["Luxury", "Mass Market"])

    st.markdown("**Product parameters (for Resale / Upcycling)**")
    quality   = st.selectbox("Quality / Condition", ["Excellent", "Good", "Worn out"])
    creative  = st.selectbox("Creative potential", ["High", "Medium", "None"])
    material  = st.selectbox("Material quality", ["High", "Medium", "Low"])

    run = st.button("Run assessment", use_container_width=True)

if not run:
    st.info("Set the inputs in the left sidebar and click **Run assessment**.")
    st.stop()

# -------------------------------
# Core computations
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
# Section B — Economic Outcome
# -------------------------------
st.subheader("Section B — Economic Outcome")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Margin Resale", f"{econ.margin_resale:.2f}")
c2.metric("Cost Resale", f"{econ.cost_resale:.2f}")
c3.metric("Score Resale (margin − cost)", f"{econ.econ_score_resale:.2f}", "PASS" if econ.feasible_resale else "FAIL")
c4.metric("Margin Upcycling", f"{econ.margin_upcycling:.2f}")
c5.metric("Cost Upcycling", f"{econ.cost_upcycling:.2f}")
c6.metric("Score Upcycling (margin − cost)", f"{econ.econ_score_upcycling:.2f}", "PASS" if econ.feasible_upcycling else "FAIL")

# Economic outcome label (for D logic as well)
if econ.feasible_resale and econ.feasible_upcycling:
    econ_initial = "Both feasible"
elif econ.feasible_resale and not econ.feasible_upcycling:
    econ_initial = "Resale only"
elif econ.feasible_upcycling and not econ.feasible_resale:
    econ_initial = "Upcycling only"
else:
    econ_initial = "None feasible"

# End-of-section badge (B)
b_label, b_sub, b_tone = badge_economic_label(econ_initial, econ)
_box(b_label, b_sub, b_tone)

# -------------------------------
# Section D — Operational Feasibility (deterministic, aligned with Excel)
# -------------------------------
st.subheader("Section D — Operational Feasibility")

S18  = oper.delta_resale_minus_up
band = cfg["operational_neutral_band"]

# D logic (Excel): if B != Both feasible → D repeats economic outcome
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
col3.metric("Δ operational (Resale − Up)", f"{S18:.2f}")
col4.metric("Status", d_status)

st.caption("Formula: Δ = (Resale Econ Gap − Upcycling Adjusted Gap) × Scale Context · Band ±{b}".format(b=band))

with st.expander("Operational details (by quadrant)"):
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

# End-of-section badge (D)
d_label, d_sub, d_tone = badge_operational_label(econ_initial, d_status, S18, band)
_box(d_label, d_sub, d_tone)

# -------------------------------
# Section E — Environmental Leverage (informative)
# -------------------------------
st.subheader("Section E — Environmental Leverage")
d1, d2, d3 = st.columns(3)
d1.metric("Impact Resale (↓ is better)", f"{env.env_resale:.2f}")
d2.metric("Impact Upcycling (↓ is better)", f"{env.env_upcycling:.2f}")
d3.metric("Δ (Resale − Upcycling)", f"{env.delta_resale_minus_up:.2f}")
st.caption("Environmental relevance: **{t}** — band ±{b}".format(t=env.tag, b=cfg["environment_neutral_band"]))

# End-of-section badge (E)
e_label, e_sub, e_tone = badge_environment_label(env, cfg["environment_neutral_band"])
_box(e_label, e_sub, e_tone)

# -------------------------------
# Section F — Model Recommendation (mirrors Section D)
# -------------------------------
st.subheader("Section F — Model Recommendation")
f_label, f_sub, f_tone = badge_final_from_operational(d_status)
_box(f_label, f_sub, f_tone)

# Optional: Decision trace
with st.expander("Decision trace"):
    st.write(f"Step B → {econ_initial}")
    st.write(f"Step D → {d_status}")
    st.write(f"Step E → {env.tag}")
