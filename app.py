# app.py (v0.2.9) — section cards + perfectly aligned multi-line comments in all boxes
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

# -------------------------------------------------
# Global CSS (section cards)
# -------------------------------------------------
if "_css_029" not in st.session_state:
    st.session_state["_css_029"] = True
    st.markdown(
        """
        <style>
          .sec-card{
            border:1px solid #E5E7EB; /* gray-200 */
            border-radius:12px;
            padding:16px 18px;
            margin:18px 0;
            background:#FFFFFF;
          }
          .sec-title{
            font-weight:700;
            font-size:1.05rem;
            margin:0 0 12px 0;
          }
          /* Make numbers look clean inside cards */
          .kv-grid{
            display:grid;
            grid-template-columns: repeat(6, minmax(0,1fr));
            gap:14px;
            margin-bottom:10px;
          }
          .kv{
            background:#F9FAFB; /* gray-50 */
            border:1px solid #F3F4F6; /* gray-100 */
            border-radius:10px;
            padding:10px 12px;
          }
          .kv .k{
            font-size:0.82rem;
            color:#4B5563; /* gray-600 */
            margin-bottom:4px;
          }
          .kv .v{
            font-weight:700;
            font-size:1.05rem;
            color:#111827; /* gray-900 */
          }
          /* 3-col grid used in Section D and E */
          .kv-grid-3{
            display:grid;
            grid-template-columns: repeat(3, minmax(0,1fr));
            gap:14px;
            margin-bottom:10px;
          }
        </style>
        """,
        unsafe_allow_html=True
    )

# -------------------------------------------------
# Helpers (HTML boxes, pills, text formatting)
# -------------------------------------------------
Tone = Literal["success", "info", "warn", "error"]

def _nl_after_period(text: str) -> str:
    """
    Insert explicit line breaks after '.', '?', '!' followed by space.
    Remove any leading spaces at the start of each line (alignment).
    """
    if not text:
        return ""
    s = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    s = re.sub(r'\.\s+', '.\n', s)
    s = re.sub(r'\?\s+', '?\n', s)
    s = re.sub(r'!\s+', '!\n', s)
    # remove leading spaces at start of EACH line → perfect left alignment
    s = re.sub(r'(?m)^[ \t]+', '', s)
    # collapse excessive blank lines
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def _tone_colors(tone: Tone) -> tuple[str, str, str]:
    """
    Returns (bg, border, text) HEX colors for the info box.
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
      - subtitle honoring newlines (white-space: pre-wrap)
    """
    bg, border, text = _tone_colors(tone)
    subtitle_fmt = _nl_after_period(subtitle)
    html = f"""
    <div style="
        border:1px solid {border};
        background:{bg};
        color:{text};
        padding:12px 14px;
        border-radius:10px;
        line-height:1.35;">
        <div style="font-weight:700;">{label}</div>
        <div style="white-space:pre-wrap;margin-top:6px;">
            {subtitle_fmt}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def _status_pill(ok: bool, ok_text: str = "PASS", ko_text: str = "FAIL"):
    """Rounded pill: green '✓ PASS' or red '✗ FAIL' with no arrow."""
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

# Exact explanatory texts (B, D)
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
        "Resale more capable of absorbing increasing operational complexity and volumes. "
        "Upcycling remains economically viable (playing a complementary or selective role)."
    ),
    "Upcycling preferred": (
        "Upcycling more capable of absorbing increasing operational complexity and volumes. "
        "Resale remains economically viable (playing a complementary or selective role)."
    ),
    "Neutral": "No dominant model; hybrid or parallel adoption possible.",
}

# Colors per your preferences
def badge_economic_label(econ_initial: str) -> tuple[str, str, Tone]:
    """Section B colors: Green (only), Blue (both), Red (none)."""
    if econ_initial == "Resale only":
        return ("Resale only", "Economic pass: margin − cost (Resale) > 0.", "success")
    if econ_initial == "Upcycling only":
        return ("Upcycling only", "Economic pass: margin − cost (Upcycling) > 0.", "success")
    if econ_initial == "Both feasible":
        return ("Both feasible", "Both strategies meet margin − cost > 0.", "info")
    return ("✗ None feasible", "No strategy meets margin − cost > 0.", "error")

def badge_operational_label(econ_initial: str, d_status: str) -> tuple[str, Tone]:
    """Section D colors: Green (only & preferred), Blue (neutral), Red (none)."""
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
    """Section F mirrors D; Neutral → 'Hybrid / Strategic use' (blue)."""
    if d_status in ["Resale only", "Upcycling only"]:
        return (d_status, "success")
    if d_status in ["Resale preferred", "Upcycling preferred"]:
        return (d_status, "success")
    if d_status == "None feasible":
        return ("✗ None feasible", "error")
    return ("Hybrid / Strategic use", "info")

# Long recommendation texts (F)
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

# =================================================
# Section B — Economic Feasibility  (wrapped in card)
# =================================================
st.markdown('<div class="sec-card">', unsafe_allow_html=True)
st.markdown('<div class="sec-title">Section B — Economic Feasibility</div>', unsafe_allow_html=True)

# 6 metrics as simple key-value cards (for perfect card containment)
st.markdown(
    f"""
    <div class="kv-grid">
      <div class="kv"><div class="k">Margin Resale</div><div class="v">{econ.margin_resale:.2f}</div></div>
      <div class="kv"><div class="k">Cost Resale</div><div class="v">{econ.cost_resale:.2f}</div></div>
      <div class="kv"><div class="k">Score Resale (margin − cost)</div><div class="v">{econ.econ_score_resale:.2f}</div></div>
      <div class="kv"><div class="k">Margin Upcycling</div><div class="v">{econ.margin_upcycling:.2f}</div></div>
      <div class="kv"><div class="k">Cost Upcycling</div><div class="v">{econ.cost_upcycling:.2f}</div></div>
      <div class="kv"><div class="k">Score Upcycling (margin − cost)</div><div class="v">{econ.econ_score_upcycling:.2f}</div></div>
    </div>
    """,
    unsafe_allow_html=True
)
# PASS/FAIL pills under each score
colA, colB, colC, colD, colE, colF = st.columns(6)
with colC: _status_pill(econ.feasible_resale)
with colF: _status_pill(econ.feasible_upcycling)

# Economic outcome → label + explanation inside info box
if econ.feasible_resale and econ.feasible_upcycling:
    econ_initial = "Both feasible"
elif econ.feasible_resale and not econ.feasible_upcycling:
    econ_initial = "Resale only"
elif econ.feasible_upcycling and not econ.feasible_resale:
    econ_initial = "Upcycling only"
else:
    econ_initial = "None feasible"

b_label, b_rule, b_tone = badge_economic_label(econ_initial)
b_expl = ECON_EXPL["None feasible" if econ_initial == "None feasible" else econ_initial]
_box(b_label, f"{b_rule}\n{b_expl}", b_tone)

st.markdown("</div>", unsafe_allow_html=True)  # close section card

# =================================================
# Section D — Operational Feasibility  (wrapped in card)
# =================================================
st.markdown('<div class="sec-card">', unsafe_allow_html=True)
st.markdown('<div class="sec-title">Section D — Operational Feasibility</div>', unsafe_allow_html=True)

S18  = oper.delta_resale_minus_up
op_band = cfg["operational_neutral_band"]

# D logic (Excel): gating or preferred/neutral
if econ_initial in ["Resale only", "Upcycling only", "None feasible"]:
    d_status = econ_initial
else:
    if S18 > op_band:
        d_status = "Resale preferred"
    elif S18 < -op_band:
        d_status = "Upcycling preferred"
    else:
        d_status = "Neutral"

# KPIs row (3 columns)
st.markdown(
    f"""
    <div class="kv-grid-3">
      <div class="kv"><div class="k">Adjusted Resale Gap</div><div class="v">{oper.adjusted_resale_gap:.2f}</div></div>
      <div class="kv"><div class="k">Adjusted Upcycling Gap</div><div class="v">{oper.adjusted_upcycling_gap:.2f}</div></div>
      <div class="kv"><div class="k">Δ operational (Resale − Up)</div><div class="v">{S18:.2f}</div></div>
    </div>
    """,
    unsafe_allow_html=True
)

# Formula & details in expander (not in the comment box)
with st.expander("Operational details (by quadrant)"):
    st.caption("Formula: Δ = (Resale Econ Gap − Upcycling Adjusted Gap) × Scale Context, compared against Band ±{b}".format(b=op_band))
    node  = cfg["operational"]["matrix"][category][segment]
    scale = cfg["operational"]["scale_context"][category][segment]
    resale_econ_gap = node["resale"]["econ_gap"]
    up_adj_gap_base = node["upcycling"]["adjusted_gap"]
    st.markdown(
        f"- **Scale context**: `{scale}`\n"
        f"- **Resale** — Econ gap: `{resale_econ_gap}` → Adjusted = `{oper.adjusted_resale_gap:.2f}`\n"
        f"- **Upcycling** — Adjusted gap (base): `{up_adj_gap_base}` → Adjusted = `{oper.adjusted_upcycling_gap:.2f}`"
    )

# Only your comment inside the colored box
d_label, d_tone = badge_operational_label(econ_initial, d_status)
d_expl = OPER_EXPL[d_status]
_box(d_label, d_expl, d_tone)

st.markdown("</div>", unsafe_allow_html=True)  # close section card

# =================================================
# Section E — Environmental Leverage  (wrapped in card)
# =================================================
st.markdown('<div class="sec-card">', unsafe_allow_html=True)
st.markdown('<div class="sec-title">Section E — Environmental Leverage</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="kv-grid-3">
      <div class="kv"><div class="k">Impact Resale (↓ is better)</div><div class="v">{env.env_resale:.2f}</div></div>
      <div class="kv"><div class="k">Impact Upcycling (↓ is better)</div><div class="v">{env.env_upcycling:.2f}</div></div>
      <div class="kv"><div class="k">Δ (Resale − Upcycling)</div><div class="v">{env.delta_resale_minus_up:.2f}</div></div>
    </div>
    """,
    unsafe_allow_html=True
)

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

st.markdown("</div>", unsafe_allow_html=True)  # close section card

# =================================================
# Section F — Model Recommendation  (wrapped in card)
# =================================================
st.markdown('<div class="sec-card">', unsafe_allow_html=True)
st.markdown('<div class="sec-title">Section F — Model Recommendation</div>', unsafe_allow_html=True)

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

# Final colored box with your text (multi-line perfectly aligned)
_box(f_label, final_text, f_tone)

# Decision trace expander (unchanged logic)
with st.expander("Decision trace"):
    econ_check = "✓" if econ_initial != "None feasible" else "✗"
    scal_check = "✓" if d_status in ["Resale preferred", "Upcycling preferred", "Neutral", "Resale only", "Upcycling only"] else "✗"
    env_label = "Environmental leverage applied" if relevance_applied else "Environmental neutral"
    st.write(f"- **Economic feasibility** {econ_check}")
    st.write(f"- **Scalability** {scal_check}")
    st.write(f"- **{env_label}**")

st.markdown("</div>", unsafe_allow_html=True)  # close section card
