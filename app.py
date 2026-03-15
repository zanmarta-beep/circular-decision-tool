# app.py (v0.2.7) — D box = only your comment; line breaks after periods in all boxes
import json
import re
import streamlit as st
from typing import Literal
from engine import (
    Inputs, compute_economic, compute_operational, compute_environment
)

st.set_page_config(page_title="Circular Strategy Advisor", layout="wide")

st.title("Circular Strategy Advisor")
st.caption("Decision-support tool to orient between resale and upcycling")

# -------------------------------
# Helpers (badges, pills, text formatting)
# -------------------------------
Tone = Literal["success", "info", "warn", "error", "neutral"]

def _nl_after_period(text: str) -> str:
    """
    Insert line breaks after '.', '?', '!' followed by a space.
    Keeps existing newlines and ensures a final period if missing
    (only for non-empty lines).
    """
    if text is None:
        return ""
    # Normalize Windows CRLF → LF
    s = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    # Split existing lines, then enforce breaks after punctuation within each line
    lines = []
    for raw in s.split("\n"):
        t = raw.strip()
        if not t:
            continue
        # Add newline after punctuation tokens followed by space
        t = re.sub(r'\.\s+', '.\n', t)
        t = re.sub(r'\?\s+', '?\n', t)
        t = re.sub(r'!\s+', '!\n', t)
        # If the line has no ending punctuation, leave as is
        lines.append(t)
    return "\n".join(lines)

def _box(label: str, subtitle: str = "", tone: Tone = "info"):
    """
    Unified badge renderer.
    tone: success=green, info=blue, warn=yellow, error=red, neutral=grey (caption)
    Subtitle supports '\\n' line breaks; after formatting, we ensure breaks after periods.
    """
    subtitle_fmt = _nl_after_period(subtitle)
    content = f"**{label}**" + (f"\n{subtitle_fmt}" if subtitle_fmt else "")
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

def _status_pill(ok: bool, ok_text: str = "PASS", ko_text: str = "FAIL"):
    """
    Renders a rounded pill: green '✓ PASS' or red '✗ FAIL' with no arrow.
    """
    color = "#16a34a" if ok else "#dc2626"   # green-600 / red-600
    bg    = f"{color}1A"                     # translucent background
    text  = f"✓ {ok_text}" if ok else f"✗ {ko_text}"
    st.markdown(
        f"""
        <span style="
            display:inline-block;
            padding:.15rem .55rem;
            border-radius:999px;
            background:{bg};
            color:{color};
            font-weight:600;
            font-size:0.80rem;">
            {text}
        </span>
        """,
        unsafe_allow_html=True
    )

# --- Exact explanatory texts (B, D) with punctuation ---
ECON_EXPL = {
    "Resale only":    "Only resale passes the economic feasibility threshold.",
    "Upcycling only": "Only upcycling passes the economic feasibility threshold.",
    "Both feasible":  "Both models are economically admissible at this stage.",
    "None feasible":  "Neither model is economically viable under current assumptions.",
}

OPER_EXPL = {
    "Resale only":    "Only resale passes the economic feasibility threshold.",
    "Upcycling only": "Only upcycling passes the economic feasibility threshold.",
    "Both feasible":  "Both models are economically admissible at this stage.",
    "None feasible":  "Neither model is economically viable under current assumptions.",
    "Resale preferred": (
        "Resale more capable of absorbing increasing operational complexity and volumes.\n"
        "Upcycling remains economically viable (playing a complementary or selective role)."
    ),
    "Upcycling preferred": (
        "Upcycling more capable of absorbing increasing operational complexity and volumes.\n"
        "Resale remains economically viable (playing a complementary or selective role)."
    ),
    "Neutral": "No dominant model; hybrid or parallel adoption possible.",
}

# Colors per your preferences
def badge_economic_label(econ_initial: str) -> tuple[str, str, Tone]:
    """
    Section B colors: Green (only), Blue (both), Red (none).
    Returns (label, short_rule, tone).
    """
    if econ_initial == "Resale only":
        return ("Resale only", "Economic pass: margin − cost (Resale) > 0.", "success")
    if econ_initial == "Upcycling only":
        return ("Upcycling only", "Economic pass: margin − cost (Upcycling) > 0.", "success")
    if econ_initial == "Both feasible":
        return ("Both feasible", "Both strategies meet margin − cost > 0.", "info")
    return ("✗ None feasible", "No strategy meets margin − cost > 0.", "error")  # red

def badge_operational_label(econ_initial: str, d_status: str, S18: float, band: float) -> tuple[str, Tone]:
    """
    Section D colors: Green (only & preferred), Blue (neutral), Red (none).
    Returns (label, tone).  (Subtitle is REMOVED by request: only user's comment will be shown.)
    """
    if econ_initial in ["Resale only", "Upcycling only", "None feasible"]:
        label = "✗ None feasible" if econ_initial == "None feasible" else econ_initial
        tone = "error" if econ_initial == "None feasible" else "success"
        return (label, tone)
    if d_status == "Resale preferred":
        return ("Resale preferred", "success")
    if d_status == "Upcycling preferred":
        return ("Upcycling preferred", "success")
    return ("Neutral", "info")

def badge_final_from_operational(d_status: str) -> tuple[str, Tone]:
    """
    Section F mirrors D for color; Neutral becomes “Hybrid / Strategic use”.
    Returns (final_label, tone).  Subtitle is entirely the user's long text.
    """
    if d_status in ["Resale only", "Upcycling only"]:
        return (d_status, "success")
    if d_status in ["Resale preferred", "Upcycling preferred"]:
        return (d_status, "success")
    if d_status == "None feasible":
        return ("✗ None feasible", "error")
    return ("Hybrid / Strategic use", "info")

# Long recommendation texts (F) — user wording with explicit line breaks
FINAL_LONG_TEXT = {
    "Resale preferred": (
        "Resale emerges as the preferred circular strategy due to its superior scalability and more attractive economic performance.\n"
        "Upcycling remains viable but is not structurally central."
    ),
    "Upcycling preferred": (
        "Upcycling emerges as the preferred strategy as product-specific value enhancers compensate for higher operational intensity, enabling superior value creation.\n"
        "Resale remains viable but is not structurally central."
    ),
    "Hybrid / Strategic use": (
        "No dominant circular configuration emerges.\n"
        "Resale and upcycling can coexist strategically, enabling flexibility in value capture across different product subsets."
    ),
    "Resale only": "Only resale is economically sustainable.",
    "Upcycling only": "Only Upcycling is economically sustainable.",
    "✗ None feasible": "Neither model is economically viable under current assumptions."
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

# Resale margin & cost
c1.metric("Margin Resale", f"{econ.margin_resale:.2f}")
c2.metric("Cost Resale",   f"{econ.cost_resale:.2f}")

# Resale score: value + PASS/FAIL pill (no arrow)
c3.metric("Score Resale (margin − cost)", f"{econ.econ_score_resale:.2f}")
with c3:
    _status_pill(econ.feasible_resale)

# Upcycling margin & cost
c4.metric("Margin Upcycling", f"{econ.margin_upcycling:.2f}")
c5.metric("Cost Upcycling",   f"{econ.cost_upcycling:.2f}")

# Upcycling score: value + PASS/FAIL pill (no arrow)
c6.metric("Score Upcycling (margin − cost)", f"{econ.econ_score_upcycling:.2f}")
with c6:
    _status_pill(econ.feasible_upcycling)

# Economic outcome (for D logic too)
if econ.feasible_resale and econ.feasible_upcycling:
    econ_initial = "Both feasible"
elif econ.feasible_resale and not econ.feasible_upcycling:
    econ_initial = "Resale only"
elif econ.feasible_upcycling and not econ.feasible_resale:
    econ_initial = "Upcycling only"
else:
    econ_initial = "None feasible"

# End-of-section colored box (B) — rule line + explanatory line, with line breaks enforced
b_label, b_rule, b_tone = badge_economic_label(econ_initial)
b_expl = ECON_EXPL["None feasible" if econ_initial == "None feasible" else econ_initial]
_box(b_label, f"{b_rule}\n{b_expl}", b_tone)

# -------------------------------
# Section D — Operational Feasibility (deterministic, aligned with Excel)
# -------------------------------
st.subheader("Section D — Operational Feasibility")

S18  = oper.delta_resale_minus_up
op_band = cfg["operational_neutral_band"]

# D logic (Excel): if B != Both feasible → D repeats economic outcome
if econ_initial in ["Resale only", "Upcycling only", "None feasible"]:
    d_status = econ_initial
else:
    if S18 > op_band:
        d_status = "Resale preferred"
    elif S18 < -op_band:
        d_status = "Upcycling preferred"
    else:
        d_status = "Neutral"

# KPIs (status block removed; only 3 metrics remain)
col1, col2, col3 = st.columns(3)
col1.metric("Adjusted Resale Gap", f"{oper.adjusted_resale_gap:.2f}")
col2.metric("Adjusted Upcycling Gap", f"{oper.adjusted_upcycling_gap:.2f}")
col3.metric("Δ operational (Resale − Up)", f"{S18:.2f}")

# Formula moved inside expander, with your wording
with st.expander("Operational details (by quadrant)"):
    st.caption("Formula: Δ = (Resale Econ Gap − Upcycling Adjusted Gap) × Scale Context, compared against Band ±{b}".format(b=op_band))
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
        adj_res=f"{oper.adjusted_upcycling_gap:.2f}" if False else f"{oper.adjusted_resale_gap:.2f}",
        up_base=up_adj_gap_base,
        adj_up=f"{oper.adjusted_upcycling_gap:.2f}",
    )
    st.markdown(details_md)

# End-of-section colored box (D) — ONLY your comment inside (no status/delta line)
d_label, d_tone = badge_operational_label(econ_initial, d_status, S18, op_band)
d_expl = OPER_EXPL[d_status]
_box(d_label, d_expl, d_tone)

# -------------------------------
# Section E — Environmental Leverage
# -------------------------------
st.subheader("Section E — Environmental Leverage")

d1, d2, d3 = st.columns(3)
d1.metric("Impact Resale (↓ is better)", f"{env.env_resale:.2f}")
d2.metric("Impact Upcycling (↓ is better)", f"{env.env_upcycling:.2f}")
d3.metric("Δ (Resale − Upcycling)", f"{env.delta_resale_minus_up:.2f}")

env_band = cfg["environment_neutral_band"]
delta_env = env.delta_resale_minus_up

# Direction + relevance (two lines)
direction_line = (
    "Upcycling has a lower environmental impact" if delta_env > 0
    else ("Resale has a lower environmental impact" if delta_env < 0 else "Same environmental impact")
)
relevance_applied = abs(delta_env) > env_band
relevance_line = (
    "Environmental performance relevant under the current configuration."
    if relevance_applied else
    "Environmental impact is NOT decision-relevant under the current configuration."
)

# End-of-section colored box (E) — two lines, with normalized breaks
e_label = "Environmental leverage applied" if relevance_applied else "Environmental neutral"
e_tone  = "info"  # keep blue
_box(e_label, f"{direction_line}.\n{relevance_line}", e_tone)

# -------------------------------
# Section F — Model Recommendation (mirrors D label; adds trade-off if needed)
# -------------------------------
st.subheader("Section F — Model Recommendation")

f_label, f_tone = badge_final_from_operational(d_status)

# Trade-off note if chosen model ≠ lower-impact model
chosen_model = None
if f_label in ["Resale only", "Resale preferred"]:
    chosen_model = "Resale"
elif f_label in ["Upcycling only", "Upcycling preferred"]:
    chosen_model = "Upcycling"

env_lower = "Upcycling" if delta_env > 0 else ("Resale" if delta_env < 0 else None)
tradeoff_note = ""
if chosen_model and env_lower and (chosen_model != env_lower):
    tradeoff_note = "\nTrade-off between economic feasibility and environmental performance."

final_text = FINAL_LONG_TEXT[f_label] + tradeoff_note
_box(f_label, final_text, f_tone)

# -------------------------------
# Decision trace — compact checklist
# -------------------------------
with st.expander("Decision trace"):
    econ_check = "✓" if econ_initial != "None feasible" else "✗"
    # If economic is none feasible, scalability is not applicable → mark ✗
    scal_check = "✓" if d_status in ["Resale preferred", "Upcycling preferred", "Neutral", "Resale only", "Upcycling only"] else "✗"
    env_label = "Environmental leverage applied" if relevance_applied else "Environmental neutral"

    st.write(f"- **Economic feasibility** {econ_check}")
    st.write(f"- **Scalability** {scal_check}")
    st.write(f"- **{env_label}**")
