# app.py (v0.2.8a) — v0.2.8 layout + fix: first line aligned in all boxes
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
# Helpers (HTML boxes, pills, text formatting)
# -------------------------------
Tone = Literal["success", "info", "warn", "error"]

def _nl_after_period(text: str) -> str:
    """
    Insert explicit line breaks after '.', '?', '!' followed by a space.
    Preserve existing newlines. Remove leading spaces at the start of EVERY line
    to ensure the first line is aligned with the following ones.
    """
    if not text:
        return ""
    s = text.replace("\r\n", "\n").replace("\r", "\n")
    # Insert newline after sentence-ending punctuation
    s = re.sub(r'\.\s+', '.\n', s)
    s = re.sub(r'\?\s+', '?\n', s)
    s = re.sub(r'!\s+', '!\n', s)
    # Remove leading spaces/tabs at the start of each line → perfect left alignment
    s = re.sub(r'(?m)^[ \t]+', '', s)
    # Collapse triple newlines
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def _tone_colors(tone: Tone) -> tuple[str, str, str]:
    """
    Returns (bg, border, text) HEX colors for the box.
    success=green, info=blue, warn=yellow, error=red.
    """
    if tone == "success":
        return ("#ECFDF5", "#34D399", "#065F46")  # green-50, green-400, green-800
    if tone == "error":
        return ("#FEF2F2", "#F87171", "#7F1D1D")  # red-50, red-400, red-900
    if tone == "warn":
        return ("#FFFBEB", "#FBBF24", "#92400E")  # amber-50, amber-400, amber-900
    # info (default)
    return ("#EFF6FF", "#60A5FA", "#1E3A8A")      # blue-50, blue-400, blue-900

def _box(label: str, subtitle: str = "", tone: Tone = "info"):
    """
    Render a colored HTML box with:
      - bold label on first line
      - subtitle honoring line breaks, perfectly aligned with the label (no leading-space indent).
    Uses white-space: pre-line to keep '\n' but collapse leading spaces.
    """
    bg, border, text = _tone_colors(tone)
    subtitle_fmt = _nl_after_period(subtitle)  # <- mantiene i \n e rimuove spazi/tabs a inizio riga

    # ATTENZIONE: NESSUNA indentazione prima di {subtitle_fmt} per evitare spazi testuali.
    html = f"""
<div style="border:1px solid {border};background:{bg};color:{text};padding:12px 14px;border-radius:10px;line-height:1.35;">
  <div style="font-weight:700;">{label}</div>
  <div style="white-space:pre-line;margin-top:4px;">{subtitle_fmt}</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)

def _status_pill(ok: bool, ok_text: str = "PASS", ko_text: str = "FAIL"):
    """
    Renders a rounded pill: green '✓ PASS' or red '✗ FAIL' with no arrow.
    """
    color = "#16a34a" if ok else "#dc2626"   # green-600 / red-600
    bg    = f"{color}1A"
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

# --- Environmental “lower is better” pill (under each impact metric) ---
def _env_pill(is_lower: bool | None):
    """
    Pill to indicate environmental desirability:
      - True  -> ✓ Lower (better)  [green]
      - False -> ✗ Higher (worse)  [red]
      - None  -> = Equal           [grey]
    """
    if is_lower is None:
        # equal
        color = "#4B5563"  # gray-600
        bg    = "#4B55631A"
        text  = "= Equal"
    elif is_lower:
        color = "#16a34a"  # green-600
        bg    = "#16a34a1A"
        text  = "✓ Lower (better)"
    else:
        color = "#dc2626"  # red-600
        bg    = "#dc26261A"
        text  = "✗ Higher (worse)"

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

def badge_operational_label(econ_initial: str, d_status: str) -> tuple[str, Tone]:
    """
    Section D colors: Green (only & preferred), Blue (neutral), Red (none).
    Returns (label, tone).  (No 'status/delta' line inside the box, by request.)
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
    Returns (final_label, tone).  Subtitle will be the long user text.
    """
    if d_status in ["Resale only", "Upcycling only"]:
        return (d_status, "success")
    if d_status in ["Resale preferred", "Upcycling preferred"]:
        return (d_status, "success")
    if d_status == "None feasible":
        return ("✗ None feasible", "error")
    return ("Hybrid / Strategic use", "info")

# Long recommendation texts (F) — user wording (line breaks handled by _nl_after_period)
FINAL_LONG_TEXT = {
    "Resale preferred": (
        "Resale emerges as the preferred circular strategy due to its superior scalability and more attractive economic performance. "
        "Upcycling remains viable but is not structurally central."
    ),
    "Upcycling preferred": (
        "Upcycling emerges as the preferred strategy as product-specific value enhancers compensate for higher operational intensity, enabling superior value creation. "
        "Resale remains viable but is not structurally central."
    ),
    "Hybrid / Strategic use": (
        "No dominant circular configuration emerges. "
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

# --- DEBUG (temporary): verify engine delta rule when negatives appear ---
with st.expander("DEBUG — Operational delta check (temporary)"):
    st.write("Adjusted Resale Gap (P18):", oper.adjusted_resale_gap)
    st.write("Adjusted Upcycling Gap (Q18):", oper.adjusted_upcycling_gap)

    P18 = oper.adjusted_resale_gap
    Q18 = oper.adjusted_upcycling_gap

    delta_expected = (P18 + Q18) if (P18 < 0 or Q18 < 0) else (P18 - Q18)

    st.write("Delta returned by engine:", oper.delta_resale_minus_up)
    st.write("Delta expected (Excel rule):", round(delta_expected, 4))
    st.write("Negatives trigger:", (P18 < 0 or Q18 < 0))
    
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

# End-of-section HTML box (B): rule line + explanatory line, with breaks and aligned first line
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

# Top KPIs (status block removed as requested)
col1, col2, col3 = st.columns(3)
col1.metric("Adjusted Resale Gap", f"{oper.adjusted_resale_gap:.2f}")
col2.metric("Adjusted Upcycling Gap", f"{oper.adjusted_upcycling_gap:.2f}")
col3.metric("Δ operational (Resale − Up)", f"{S18:.2f}")

# Formula inside the expander (not inside the comment box)
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
        adj_res=f"{oper.adjusted_resale_gap:.2f}",
        up_base=up_adj_gap_base,
        adj_up=f"{oper.adjusted_upcycling_gap:.2f}",
    )
    st.markdown(details_md)

# End-of-section HTML box (D): ONLY your comment inside (first line aligned)
d_label, d_tone = badge_operational_label(econ_initial, d_status)
d_expl = OPER_EXPL[d_status]
_box(d_label, d_expl, d_tone)

# -------------------------------
# Section E — Environmental Leverage
# -------------------------------
st.subheader("Section E — Environmental Leverage")

# 3 metriche come prima
d1, d2, d3 = st.columns(3)
d1.metric("Impact Resale (↓ is better)", f"{env.env_resale:.2f}")
d2.metric("Impact Upcycling (↓ is better)", f"{env.env_upcycling:.2f}")
d3.metric("Δ (Resale − Upcycling)", f"{env.delta_resale_minus_up:.2f}")

# NEW: pill “lower is better” sotto i due impatti
with d1:
    if env.env_resale < env.env_upcycling:
        _env_pill(True)
    elif env.env_resale > env.env_upcycling:
        _env_pill(False)
    else:
        _env_pill(None)

with d2:
    if env.env_upcycling < env.env_resale:
        _env_pill(True)
    elif env.env_upcycling > env.env_resale:
        _env_pill(False)
    else:
        _env_pill(None)

# Il resto della sezione E resta identico (direction + relevance nel box)
env_band = cfg["environment_neutral_band"]
delta_env = env.delta_resale_minus_up

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

e_label = "Environmental leverage applied" if relevance_applied else "Environmental neutral"
_box(e_label, f"{direction_line}.\n{relevance_line}", "info")

# -------------------------------
# Section F — Model Recommendation (mirrors D label; adds Trade-off if needed)
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
    tradeoff_note = "Trade-off between economic feasibility and environmental performance."

final_text = FINAL_LONG_TEXT[f_label]
if tradeoff_note:
    if not final_text.strip().endswith("."):
        final_text = final_text.strip() + "."
    final_text = f"{final_text} {tradeoff_note}"

# Final colored box with your text (multi-line, first line aligned)
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
