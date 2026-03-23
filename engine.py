# engine.py (v0.2) — allineato alla logica Excel
from dataclasses import dataclass
from typing import Dict, Any

# -------------------------------
# Data models
# -------------------------------
@dataclass
class Inputs:
    product_category: str      # "Abbigliamento" | "Accessori"
    price_segment: str         # "Luxury" | "Mass Market"
    quality_condition: str     # "Excellent" | "Good" | "Worn out"
    creative_potential: str    # "High" | "Medium" | "None"
    material_quality: str      # "High" | "Medium" | "Low"

@dataclass
class EconomicResult:
    margin_resale: float
    margin_upcycling: float
    cost_resale: float
    cost_upcycling: float
    econ_score_resale: float   # margin - cost
    econ_score_upcycling: float
    feasible_resale: bool
    feasible_upcycling: bool

@dataclass
class OperationalResult:
    adjusted_resale_gap: float
    adjusted_upcycling_gap: float
    delta_resale_minus_up: float   # positivo => favore Resale
    tag: str                       # "Neutral" | "Preference resale" | "Preference upcycling"

@dataclass
class EnvironmentalResult:
    env_resale: float
    env_upcycling: float
    delta_resale_minus_up: float   # positivo => Resale migliore (impatto minore)
    tag: str                       # "Neutral" | "Preference resale" | "Preference upcycling"

@dataclass
class Recommendation:
    label: str
    rationale_economic: str
    rationale_operational: str
    rationale_environment: str
    decision_trace: list[str]

# -------------------------------
# Economic block (Step B)
# -------------------------------
def compute_economic(inputs: Inputs, cfg: Dict[str, Any]) -> EconomicResult:
    # Baseline distinte per strategia
    base_resale = cfg["baseline_margin_resale"][inputs.product_category][inputs.price_segment]
    base_up     = cfg["baseline_margin_upcycling"][inputs.product_category][inputs.price_segment]

    # Adjust specifici
    resale_q_adj    = cfg["resale_adjust"]["quality_condition"][inputs.quality_condition]
    up_creative_adj = cfg["upcycling_adjust"]["creative_potential"][inputs.creative_potential]
    up_material_adj = cfg["upcycling_adjust"]["material_quality"][inputs.material_quality]

    # Margini finali
    margin_resale = base_resale + resale_q_adj + cfg["resale_bias"]
    margin_up     = base_up     + up_creative_adj + up_material_adj + cfg["upcycling_bias"]

    # Costi fissi per quadrante
    cost_resale = cfg["cost_resale"][inputs.product_category][inputs.price_segment]
    cost_up     = cfg["cost_upcycling"][inputs.product_category][inputs.price_segment]

    # Regola economica: PASS se (margin - cost) > threshold
    thr         = cfg["economic_threshold"]
    econ_resale = margin_resale - cost_resale
    econ_up     = margin_up     - cost_up

    feasible_resale     = econ_resale > thr
    feasible_upcycling  = econ_up     > thr

    return EconomicResult(
        margin_resale=margin_resale,
        margin_upcycling=margin_up,
        cost_resale=cost_resale,
        cost_upcycling=cost_up,
        econ_score_resale=econ_resale,
        econ_score_upcycling=econ_up,
        feasible_resale=feasible_resale,
        feasible_upcycling=feasible_upcycling
    )

# -------------------------------
# Operational block (Step D, deterministico)
# -------------------------------
def compute_operational(category: str, segment: str, cfg: Dict[str, Any], econ: EconomicResult) -> OperationalResult:
    """
    Dynamic Operational Feasibility (Excel-aligned) for BOTH strategies:

    For each strategy s:
      Gap_s   = Score_s = (Margin_s - Cost_s)
      Avg_s   = (Margin_s + Score_s) / 2
      SCR_s   = Avg_s / Cost_s
      Coeff_s = SCR_s / (1 + SCR_s)
      AdjGap_s = Gap_s * Coeff_s * ScaleContext

    Delta (Resale − Up):
      IF(OR(AdjUp < 0, AdjRes < 0), AdjRes + AdjUp, AdjRes − AdjUp)

    Classification with ± operational_neutral_band.
    """
    scale = cfg["operational"]["scale_context"][category][segment]
    band  = cfg["operational_neutral_band"]

    # --- Resale ---
    margin_r = econ.margin_resale
    cost_r   = econ.cost_resale
    gap_r    = econ.econ_score_resale  # = margin - cost (economic gap)

    avg_r = (margin_r + gap_r) / 2.0
    scr_r = avg_r / cost_r if cost_r != 0 else 0.0
    coeff_r = scr_r / (1.0 + scr_r) if scr_r > -1 else 0.0  # safe guard
    adj_r = gap_r * coeff_r * scale

    # --- Upcycling ---
    margin_u = econ.margin_upcycling
    cost_u   = econ.cost_upcycling
    gap_u    = econ.econ_score_upcycling  # = margin - cost (economic gap)

    avg_u = (margin_u + gap_u) / 2.0
    scr_u = avg_u / cost_u if cost_u != 0 else 0.0
    coeff_u = scr_u / (1.0 + scr_u) if scr_u > -1 else 0.0
    adj_u = gap_u * coeff_u * scale

    # --- Delta with your negative rule (Adjusted values!) ---
    if (adj_r < 0) or (adj_u < 0):
        delta = adj_r + adj_u
    else:
        delta = adj_r - adj_u

    # --- Neutral band classification ---
    if abs(delta) <= band:
        tag = "Neutral"
    elif delta > band:
        tag = "Preference resale"
    else:
        tag = "Preference upcycling"

    return OperationalResult(
        adjusted_resale_gap=round(adj_r, 4),
        adjusted_upcycling_gap=round(adj_u, 4),
        delta_resale_minus_up=round(delta, 4),
        tag=tag
    )
# -------------------------------
# Environmental block (Step E)
# -------------------------------
def compute_environment(category: str, segment: str, cfg: Dict[str, Any]) -> EnvironmentalResult:
    node        = cfg["environment_matrix"][category][segment]
    env_resale  = node["resale"]
    env_up      = node["upcycling"]
    delta       = env_resale - env_up                      # positivo => resale migliore (impatto minore)
    band        = cfg["environment_neutral_band"]

    if abs(delta) <= band:
        tag = "Neutral"
    elif delta > band:
        tag = "Preference resale"
    else:
        tag = "Preference upcycling"

    return EnvironmentalResult(env_resale, env_up, delta, tag)

# -------------------------------
# Recommendation (Step F)
# -------------------------------
def recommend(econ: EconomicResult, oper: OperationalResult, env: EnvironmentalResult, cfg: Dict[str, Any]) -> Recommendation:
    # 1) Gating economico
    if econ.feasible_upcycling and not econ.feasible_resale:
        label = "Upcycling only"
    elif econ.feasible_resale and not econ.feasible_upcycling:
        label = "Resale only"
    elif not econ.feasible_resale and not econ.feasible_upcycling:
        label = "None"
    else:
        # 2) Tie-breaker operativo
        if oper.tag == "Preference resale":
            label = "Resale only (operational preference)"
        elif oper.tag == "Preference upcycling":
            label = "Upcycling only (operational preference)"
        else:
            # 3) Tie-breaker ambientale
            if env.tag == "Preference resale":
                label = "Resale only (environmental preference)"
            elif env.tag == "Preference upcycling":
                label = "Upcycling only (environmental preference)"
            else:
                label = "Both feasible"

    # Rationale
    if label.startswith("Upcycling"):
        rationale_econ = (
            "Upcycling supera la regola economica (margin − cost > 0), resale no."
            if (econ.feasible_upcycling and not econ.feasible_resale)
            else "Entrambe le strategie superano la soglia: preferenza verso Upcycling per operativo/ambiente."
        )
    elif label.startswith("Resale"):
        rationale_econ = (
            "Resale supera la regola economica (margin − cost > 0), upcycling no."
            if (econ.feasible_resale and not econ.feasible_upcycling)
            else "Entrambe le strategie superano la soglia: preferenza verso Resale per operativo/ambiente."
        )
    elif label == "None":
        rationale_econ = "Nessuna strategia supera la regola economica (margin − cost ≤ 0)."
    else:
        rationale_econ = "Entrambe le strategie superano la regola economica (margin − cost > 0)."

    rationale_oper = (
        f"Operational: {oper.tag} "
        f"(Adj Res={oper.adjusted_resale_gap:.2f}, "
        f"Adj Up={oper.adjusted_upcycling_gap:.2f}, "
        f"Δ={oper.delta_resale_minus_up:.2f}, "
        f"banda ±{cfg['operational_neutral_band']})."
    )
    rationale_env  = (
        f"Environmental: {env.tag} "
        f"(Δ res−up = {env.delta_resale_minus_up:.2f}, "
        f"banda ±{cfg['environment_neutral_band']})."
    )

    trace = [
        f"Economic feasibility → resale={'PASS' if econ.feasible_resale else 'FAIL'}, "
        f"upcycling={'PASS' if econ.feasible_upcycling else 'FAIL'}",
        f"Operational → {oper.tag}",
        f"Environmental → {env.tag}",
    ]
    return Recommendation(label, rationale_economic=rationale_econ,
                          rationale_operational=rationale_oper,
                          rationale_environment=rationale_env,
                          decision_trace=trace)
