# app.py (v0.2.4) — English UI + defaults + section explanations + updated colors
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
# Helpers for end-of-section badges & explanations
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

# Explanations requested by Marta
ECON_EXPL = {
    "Resale only":   "Only resale passes the economic feasibility threshold",
    "Upcycling only":"Only upcycling passes the economic feasibility threshold",
    "Both feasible": "Both models are economically admissible at this stage",
    "None feasible": "Neither model is economically viable under current assumptions",
}

OPER_EXPL = {
    "Resale only":   "Only resale passes the economic feasibility threshold",
    "Upcycling only":"Only upcycling passes the economic feasibility threshold",
    "Both feasible": "Both models are economically admissible at this stage",
    "None feasible": "Neither model is economically viable under current assumptions",
    "Resale preferred": (
        "Resale more capable of absorbing increasing operational complexity and volumes.\n"
        "Upcycling remains economically viable (playing a complementary or selective role)."
    ),
    "Upcycling preferred": (
        "Upcycling more capable of absorbing increasing operational complexity and volumes.\n"
        "Resale remains economically viable (playing a complementary or selective role)."
    ),
    "Neutral": "No dominant model; hybrid or parallel adoption possible",
}

# Sections D and F color rules (requested)
def badge_operational_label(econ_initial: str, d_status: str, S18: float, band: float) -> tuple[str, str, Tone]:
    """
    End label for Section D (Operational Feasibility).
    Colors:
      - Green: Resale only / Upcycling only / Resale preferred / Upcycling preferred
      - Blue:  Neutral
      - Red:   None feasible
    """
    if econ_initial in ["Resale only", "Upcycling only", "None feasible"]:
        label = econ_initial
        subtitle = "Economic gating."
        tone = "error" if label == "None feasible" else "success"
        return (label, subtitle, tone)

    if d_status == "Resale preferred":
        return ("Resale preferred", f"Δ = {S18:.2f} · band ±{band}", "success")
    if d_status == "Upcycling preferred":
        return ("Upcycling preferred", f"Δ = {S18:.2f} · band ±{band}", "success")
    return ("Neutral", f"Δ = {S18:.2f} · band ±{band}", "info")

def badge_economic_label(econ_initial: str) -> tuple[str, str, Tone]:
    """
    End label for Section B (Economic Feasibility).
    Colors for B unchanged:
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

def badge_final_from_operational(d_status: str) -> tuple[str, str, Tone]:
    """
    Section F mirrors D for label, except:
      - D=Neutral -> F label becomes 'Hybrid / Strategic use' (blue)
    Other colors:
      - Green: Resale only / Upcycling only / Resale preferred / Upcycling preferred
      - Red:   None feasible
    """
    if d_status in ["Resale only", "Upcycling only"]:
        return (d_status, "Economic gating.", "success")
    if d_status in ["Resale preferred", "Upcycling preferred"]:
        return (d_status, "Operational preference (Δ out of band).", "success")
    if d_status == "None feasible":
        return ("None feasible", "Revisit assumptions, costs or margin levers.", "error")
    # Neutral -> Hybrid / Strategic use
    return ("Hybrid / Strategic use", "Choose based on operational capacity and brand positioning.", "info")

# Long recommendation texts (Section F)
FINAL_LONG_TEXT = {
    "Resale preferred": (
        "Resale emerges as the preferred circular strategy due to its superior scalability "
        "and more attractive economic performance.\n"
        "Upcycling remains viable but is not structurally central."
    ),
    "Upcycling preferred": (
        "Upcycling emerges as the preferred strategy as product-specific value enhancers compensate "
        "for higher operational intensity, enabling superior value creation.\n"
        "Resale remains viable but is not structurally central."
    ),
    "Hybrid / Strategic use": (
        "No dominant circular configuration emerges. Resale and upcycling can coexist strategically, "
        "enabling flexibility in value capture across different product subsets."
    ),
    "Resale only": "Only resale is economically sustainable.",
    "Upcycling only": "Only upcycling is economically sustainable.",
    "None feasible": "Neither model is economically viable under current assumptions."
}

# -------------------------------
# Load configuration
# -------------------------------
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

# -------------------------------
# Sidebar — Section A (Inputs) with defaults + baseline note
# -------------------------------
with st.sidebar:
    st.header("Section A — Inputs")
    category = st.selectbox("Product category", ["Abbigliamento", "Accessori"])
    segment  = st.selectbox("Price segment", ["Luxury", "Mass Market"])

    st.markdown("**Product parameters (for Resale / Upcycling)**")
    quality_options  = ["Excellent", "Good", "Worn out"]
    creative_options = ["High", "Medium", "None"]
    material_options = ["High", "Medium", "Low"]

    # Defaults: Good / None / Low
    quality  = st.selectbox("Quality / Condition", quality_options, index=quality_options.index("Good"))
    creative = st.selectbox("Creative potential",  creative_options, index=creative_options.index("None"))
    material = st.selectbox("Material quality",    material_options, index=material_options.index("Low"))

    st.caption("Baseline Scenario (Quality/Condition: Good, Creative Potential: None; Material Quality: Low)")

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
oper = compute_operational(category, segment, cfg)
env  = compute_environment(category, segment, cfg)

# -------------------------------
# Section B — Economic Feasibility
# -------------------------------
st.subheader("Section B — Economic Feasibility")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Margin Resale", f"{econ.margin_resale:.2f}")
c2.metric("Cost Resale", f"{econ.cost_resale:.2f}")
c3.metric("Score Resale (margin − cost)", f"{econ.econ_score_resale:.2f}", "PASS" if econ.feasible_resale else "FAIL")
c4.metric("Margin Upcycling", f"{econ.margin_upcycling:.2f}")
c5.metric("Cost Upcycling", f"{econ.cost_upcycling:.2f}")
c6.metric("Score Upcycling (margin − cost)", f"{econ.econ_score_upcycling:.2f}", "PASS" if econ.feasible_upcycling else "FAIL")

# Economic outcome (for D logic too)
if econ.feasible_resale and econ.feasible_upcycling:
    econ_initial = "Both feasible"
elif econ.feasible_resale and not econ.feasible_upcycling:
    econ_initial = "Resale only"
elif econ.feasible_upcycling and not econ.feasible_resale:
    econ_initial = "Upcycling only"
else:
    econ_initial = "None feasible"

# End-of-section badge + explanation (B)
b_label, b_sub, b_tone = badge_economic_label(econ_initial)
_box(b_label, b_sub, b_tone)
st.markdown(f"*{ECON_EXPL[econ_initial]}*")

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

# End-of-section badge + explanation (D)
d_label, d_sub, d_tone = badge_operational_label(econ_initial, d_status, S18, band)
_box(d_label, d_sub, d_tone)
st.markdown(f"*{OPER_EXPL[d_status]}*")

# -------------------------------
# Section E — Environmental Leverage (informative)
# -------------------------------
st.subheader("Section E — Environmental Leverage")
d1, d2, d3 = st.columns(3)
d1.metric("Impact Resale (↓ is better)", f"{env.env_resale:.2f}")
d2.metric("Impact Upcycling (↓ is better)", f"{env.env_upcycling:.2f}")
d3.metric("Δ (Resale − Upcycling)", f"{env.delta_resale_minus_up:.2f}")

# Replace previous captions/badges with two explanatory lines
delta_env = env.delta_resale_minus_up
line1 = "Upcycling has a lower environmental impact" if delta_env > 0 else \
        ("Resale has a lower environmental impact" if delta_env < 0 else "Same environmental impact")
line2 = ("Environmental performance relevant under the current configuration."
         if abs(delta_env) > cfg["environment_neutral_band"]
         else "Environmental impact is NOT decision-relevant under the current configuration.")
st.markdown(f"**{line1}.**")
st.markdown(line2)

# -------------------------------
# Section F — Model Recommendation (mirrors D for label; richer text)
# -------------------------------
st.subheader("Section F — Model Recommendation")

f_label, f_sub, f_tone = badge_final_from_operational(d_status)
_box(f_label, f_sub, f_tone)

# Long explanatory text (your wording)
st.markdown(FINAL_LONG_TEXT[f_label])

# Optional: Decision trace
with st.expander("Decision trace"):
    st.write(f"Step B → {econ_initial}")
    st.write(f"Step D → {d_status}")
    st.write(f"Step E → Δ={delta_env:.2f}")
