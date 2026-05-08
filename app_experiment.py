# app_experiment.py (v0.3.1) — Musthad-inspired UI: Plus Jakarta Sans, Resale=Indigo, Upcycling=Bordeaux
import json
import re
import streamlit as st
from typing import Literal
from engine import (
    Inputs, compute_economic, compute_operational, compute_environment
)

# ─────────────────────────────────────────────
# PAGE CONFIG + GLOBAL CSS
# ─────────────────────────────────────────────
st.set_page_config(page_title="Circular Strategy Advisor — Experimental", layout="wide")

st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

/* ── Root palette ── */
:root {
  --resale:        #3730A3;   /* indigo-700 */
  --resale-light:  #EEF2FF;   /* indigo-50  */
  --resale-mid:    #818CF8;   /* indigo-400 */

  /* Bordeaux palette */
  --up:            #7A1E2C;   /* bordeaux */
  --up-light:      #FDF2F4;   /* soft bordeaux tint */
  --up-mid:        #C9485B;   /* mid bordeaux */

  --neutral:       #0F172A;   /* slate-900 */
  --surface:       #F8FAFC;   /* slate-50  */
  --border:        #E2E8F0;   /* slate-200 */
  --text-muted:    #64748B;   /* slate-500 */
  --green:         #15803D;
  --green-bg:      #F0FDF4;
  --red:           #B91C1C;
  --red-bg:        #FEF2F2;
  --gray:          #475569;
  --gray-bg:       #F1F5F9;
}

/* ── Base font override ── */
html, body, [class*="css"] {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  color: var(--neutral);
}

/* ── App background ── */
.stApp { background: var(--surface); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: #fff;
  border-right: 1px solid var(--border);
}

/* ── Title block ── */
.csa-title {
  font-size: 2.25rem;
  font-weight: 700;
  letter-spacing: -0.6px;
  line-height: 1.12;
  color: var(--neutral);
  margin-bottom: 0.15rem;
}
.csa-subtitle {
  font-size: 0.86rem;
  color: var(--text-muted);
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

/* ── Section header ── */
.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 2.0rem 0 0.9rem 0;
  padding-bottom: 0.55rem;
  border-bottom: 2px solid var(--border);
}
.section-badge {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 3px 10px;
  border-radius: 6px;
  background: var(--neutral);
  color: #fff;
}
.section-title {
  font-size: 1.18rem;
  font-weight: 700;
  color: var(--neutral);
}

/* ── Metric cards ── */
.metric-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px 12px;
  position: relative;
  overflow: hidden;
}
.metric-label {
  font-size: 0.70rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.metric-value {
  font-size: 1.65rem;
  font-weight: 750;
  line-height: 1;
}
.metric-resale  { border-top: 3px solid var(--resale); }
.metric-up      { border-top: 3px solid var(--up); }
.metric-neutral { border-top: 3px solid var(--border); }
.metric-resale  .metric-value { color: var(--resale); }
.metric-up      .metric-value { color: var(--up); }
.metric-neutral .metric-value { color: var(--neutral); }

/* ── Pill inside metric card (top-right) ── */
.pill-inline {
  position: absolute;
  top: 12px;
  right: 12px;
  margin-top: 0;
  font-size: 0.72rem;
  padding: 2px 10px;
  border-radius: 999px;
  font-weight: 800;
  letter-spacing: 0.02em;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

/* ── Legend chips ── */
.legend-row {
  display: flex;
  gap: 18px;
  margin: 0.2rem 0 1rem;
  flex-wrap: wrap;
}
.legend-chip {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

/* ── Divider ── */
.section-divider {
  border: none;
  border-top: 1px dashed var(--border);
  margin: 1.6rem 0;
}

/* ── Output hero box ── */
.hero-box {
  border-radius: 12px;
  padding: 18px 20px;
  margin-top: 1rem;
  border-left: 5px solid;
}
.hero-box-label {
  font-size: 1.05rem;
  font-weight: 800;
  margin-bottom: 6px;
}
.hero-box-body {
  font-size: 0.92rem;
  line-height: 1.55;
  white-space: pre-line;
}

/* hero variants */
.hero-resale  { background: var(--resale-light); border-color: var(--resale); color: #1e1b4b; }
.hero-up      { background: var(--up-light);     border-color: var(--up);     color: #3f0d16; }
.hero-info    { background: #F0F9FF; border-color: #38BDF8; color: #0C4A6E; }
.hero-success { background: var(--green-bg); border-color: var(--green); color: #14532D; }
.hero-error   { background: var(--red-bg);   border-color: var(--red);   color: #7F1D1D; }

/* ── Final box ── */
.final-box {
  border-radius: 14px;
  padding: 22px 26px;
  margin-top: 1.1rem;
  border-left: 6px solid;
}
.final-box-label {
  font-size: 1.35rem;
  font-weight: 900;
  margin-bottom: 8px;
}
.final-box-body {
  font-size: 0.96rem;
  line-height: 1.6;
  white-space: pre-line;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
Tone = Literal["success", "info", "warn", "error", "resale", "upcycling"]

def _nl(text: str) -> str:
    """Newline after punctuation + remove indentation; keep existing newlines."""
    if not text:
        return ""
    s = text.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r'\.\s+', '.\n', s)
    s = re.sub(r'\?\s+', '?\n', s)
    s = re.sub(r'!\s+', '!\n', s)
    s = re.sub(r'(?m)^[ \t]+', '', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def _section(badge: str, title: str):
    st.markdown(f"""
<div class="section-header">
  <span class="section-badge">{badge}</span>
  <span class="section-title">{title}</span>
</div>
""", unsafe_allow_html=True)

def _divider():
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

def _hero(label: str, body: str, variant: str):
    body_fmt = _nl(body)
    st.markdown(f"""
<div class="hero-box hero-{variant}">
  <div class="hero-box-label">{label}</div>
  <div class="hero-box-body">{body_fmt}</div>
</div>
""", unsafe_allow_html=True)

def _final_box(label: str, body: str, variant: str):
    body_fmt = _nl(body)
    st.markdown(f"""
<div class="final-box hero-{variant}">
  <div class="final-box-label">{label}</div>
  <div class="final-box-body">{body_fmt}</div>
</div>
""", unsafe_allow_html=True)

def _pill_inline_html(text: str, color: str, bg: str) -> str:
    """Return HTML for a pill that sits inside a metric card (top-right)."""
    return f"""<span class="pill-inline" style="color:{color};background:{bg};">{text}</span>"""

def _status_pill_inline_html(ok: bool) -> str:
    if ok:
        return _pill_inline_html("✓ PASS", "#15803D", "#F0FDF4")
    return _pill_inline_html("✗ FAIL", "#B91C1C", "#FEF2F2")

def _env_pill_inline_html(is_lower) -> str:
    if is_lower is None:
        return _pill_inline_html("= Equal", "var(--gray)", "var(--gray-bg)")
    if is_lower:
        return _pill_inline_html("✓ Lower impact", "#15803D", "#F0FDF4")
    return _pill_inline_html("✗ Higher impact", "#B91C1C", "#FEF2F2")

def _metric_card(label: str, value: str, variant: str = "neutral", pill_html: str = ""):
    st.markdown(f"""
<div class="metric-card metric-{variant}">
  {pill_html}
  <div class="metric-label">{label}</div>
  <div class="metric-value">{value}</div>
</div>
""", unsafe_allow_html=True)

def _legend():
    st.markdown("""
<div class="legend-row">
  <div class="legend-chip">
    <div class="legend-dot" style="background:#3730A3;"></div>
    <span>🧥 Resale</span>
  </div>
  <div class="legend-chip">
    <div class="legend-dot" style="background:#7A1E2C;"></div>
    <span>♻️ Upcycling</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# OUTCOME TEXTS (same as your stable logic)
# ─────────────────────────────────────────────
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
    "Resale only":     "Only resale is economically sustainable.",
    "Upcycling only":  "Only upcycling is economically sustainable.",
    "✗ None feasible": "Neither model is economically viable under current assumptions."
}

def _econ_variant(econ_initial: str) -> str:
    if econ_initial == "Resale only":    return "resale"
    if econ_initial == "Upcycling only": return "up"
    if econ_initial == "Both feasible":  return "info"
    return "error"

def _oper_variant(d_status: str) -> str:
    if d_status in ["Resale only", "Resale preferred"]:       return "resale"
    if d_status in ["Upcycling only", "Upcycling preferred"]: return "up"
    if d_status == "None feasible": return "error"
    return "info"

def _final_variant(f_label: str) -> str:
    if f_label in ["Resale only", "Resale preferred"]:       return "resale"
    if f_label in ["Upcycling only", "Upcycling preferred"]: return "up"
    if f_label == "✗ None feasible": return "error"
    return "info"

def badge_final_from_operational(d_status: str) -> str:
    if d_status in ["Resale only", "Upcycling only", "Resale preferred", "Upcycling preferred"]:
        return d_status
    if d_status == "None feasible":
        return "✗ None feasible"
    return "Hybrid / Strategic use"

# ─────────────────────────────────────────────
# LOAD CONFIG
# ─────────────────────────────────────────────
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

# ─────────────────────────────────────────────
# SIDEBAR — Section A
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("Section A — Inputs")
    category = st.selectbox("Product category", ["Abbigliamento", "Accessori"])
    segment  = st.selectbox("Price segment", ["Luxury", "Mass Market"])

    st.markdown("**Product parameters (for Resale / Upcycling)**")
    quality_options  = ["Excellent", "Good", "Worn out"]
    creative_options = ["High", "Medium", "None"]
    material_options = ["High", "Medium", "Low"]

    quality  = st.selectbox("Quality / Condition", quality_options, index=quality_options.index("Good"))
    creative = st.selectbox("Creative potential",  creative_options, index=creative_options.index("None"))
    material = st.selectbox("Material quality",    material_options, index=material_options.index("Low"))

    st.caption("Baseline Scenario (Quality/Condition: Good, Creative Potential: None; Material Quality: Low)")
    run = st.button("Run assessment", use_container_width=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="padding: 1rem 0 0.5rem 0;">
  <div class="csa-title">Circular Strategy Advisor</div>
  <div class="csa-subtitle">Experimental UI · Resale vs Upcycling</div>
</div>
""", unsafe_allow_html=True)

if not run:
    st.markdown("""
<div style="margin-top:2rem; padding:22px 26px; background:#fff; border:1px solid #E2E8F0;
     border-radius:12px; color:#64748B; font-size:0.92rem; line-height:1.6;">
  <strong style="color:#0F172A; font-size:1.05rem;">Welcome</strong><br>
  Configure the product parameters in the left sidebar, then click <strong>Run assessment</strong>
  to generate the economic, operational and environmental analysis.
</div>
""", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────
# COMPUTE
# ─────────────────────────────────────────────
inp  = Inputs(
    product_category=category,
    price_segment=segment,
    quality_condition=quality,
    creative_potential=creative,
    material_quality=material
)
econ = compute_economic(inp, cfg)
oper = compute_operational(category, segment, cfg, econ)
env  = compute_environment(category, segment, cfg)

# ─────────────────────────────────────────────
# SECTION B — Economic Feasibility
# ─────────────────────────────────────────────
_section("B", "Economic Feasibility")
_legend()

c1, c2, c3, gap, c4, c5, c6 = st.columns([1.2, 1.2, 1.4, 0.15, 1.2, 1.2, 1.4])

with c1:
    _metric_card("Margin — 🧥 Resale", f"{econ.margin_resale:.2f}", "resale")
with c2:
    _metric_card("Cost — 🧥 Resale", f"{econ.cost_resale:.2f}", "resale")

with c3:
    pill = _status_pill_inline_html(econ.feasible_resale)
    _metric_card("Score — 🧥 Resale (margin − cost)", f"{econ.econ_score_resale:.2f}", "resale", pill_html=pill)

with gap:
    st.markdown('<div style="height:56px;border-left:1px dashed #E2E8F0;margin:0 auto;width:1px;"></div>', unsafe_allow_html=True)

with c4:
    _metric_card("Margin — ♻️ Upcycling", f"{econ.margin_upcycling:.2f}", "up")
with c5:
    _metric_card("Cost — ♻️ Upcycling", f"{econ.cost_upcycling:.2f}", "up")

with c6:
    pill = _status_pill_inline_html(econ.feasible_upcycling)
    _metric_card("Score — ♻️ Upcycling (margin − cost)", f"{econ.econ_score_upcycling:.2f}", "up", pill_html=pill)

# Econ outcome
if econ.feasible_resale and econ.feasible_upcycling:
    econ_initial = "Both feasible"
elif econ.feasible_resale and not econ.feasible_upcycling:
    econ_initial = "Resale only"
elif econ.feasible_upcycling and not econ.feasible_resale:
    econ_initial = "Upcycling only"
else:
    econ_initial = "None feasible"

b_expl   = ECON_EXPL[econ_initial]
b_rule   = {
    "Resale only":    "Economic pass: margin − cost (Resale) > 0.",
    "Upcycling only": "Economic pass: margin − cost (Upcycling) > 0.",
    "Both feasible":  "Both strategies meet margin − cost > 0.",
    "None feasible":  "No strategy meets margin − cost > 0.",
}[econ_initial]
b_label  = "✗ None feasible" if econ_initial == "None feasible" else econ_initial
b_variant = _econ_variant(econ_initial)

_hero(b_label, f"{b_rule}\n{b_expl}", b_variant)
_divider()

# ─────────────────────────────────────────────
# SECTION D — Operational Feasibility
# ─────────────────────────────────────────────
_section("D", "Operational Feasibility")

S18     = oper.delta_resale_minus_up
op_band = cfg["operational_neutral_band"]

if econ_initial in ["Resale only", "Upcycling only", "None feasible"]:
    d_status = econ_initial
else:
    if S18 > op_band:
        d_status = "Resale preferred"
    elif S18 < -op_band:
        d_status = "Upcycling preferred"
    else:
        d_status = "Neutral"

col1, col2, col3 = st.columns(3)
with col1:
    _metric_card("Adjusted 🧥 Resale Gap", f"{oper.adjusted_resale_gap:.2f}", "resale")
with col2:
    _metric_card("Adjusted ♻️ Upcycling Gap", f"{oper.adjusted_upcycling_gap:.2f}", "up")
with col3:
    _metric_card("Δ operational (Resale − Upcycling)", f"{S18:.2f}", "neutral")

with st.expander("Operational details (by quadrant)"):
    st.caption("Formula: Δ = (Resale Econ Gap − Upcycling Adjusted Gap) × Scale Context, compared against Band ±{b}".format(b=op_band))
    node  = cfg["operational"]["matrix"][category][segment]
    scale = cfg["operational"]["scale_context"][category][segment]
    resale_econ_gap = node["resale"]["econ_gap"]
    up_adj_gap_base = node["upcycling"]["adjusted_gap"]
    st.markdown((
        "- **Scale context**: `{scale}`\n"
        "- **Resale** — Econ gap: `{resale}` → Adjusted = `{adj_res}`\n"
        "- **Upcycling** — Adjusted gap (base): `{up_base}` → Adjusted = `{adj_up}`"
    ).format(
        scale=scale, resale=resale_econ_gap,
        adj_res=f"{oper.adjusted_resale_gap:.2f}",
        up_base=up_adj_gap_base,
        adj_up=f"{oper.adjusted_upcycling_gap:.2f}",
    ))

