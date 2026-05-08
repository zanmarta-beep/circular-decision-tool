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
