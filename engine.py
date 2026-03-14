# engine.py
from dataclasses import dataclass
from typing import Dict, Any

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

def compute_economic(inputs: Inputs, cfg: Dict[str, Any]) -> EconomicResult:
    # Baseline distinte per strategia
    base_resale = cfg["baseline_margin_resale"][inputs.product_category][inputs.price_segment]
    base_up = cfg["baseline_margin_upcycling"][inputs.product_category][inputs.price_segment]

    # Adjust specifici
    resale_q_adj = cfg["resale_adjust"]["quality_condition"][inputs.quality_condition]
    up_creative_adj = cfg["upcycling_adjust"]["creative_potential"][inputs.creative_potential]
    up_material_adj = cfg["upcycling_adjust"]["material_quality"][inputs.material_quality]

    # Margini finali
    margin_resale = base_resale + resale_q_adj + cfg["resale_bias"]
    margin_up = base_up + up_creative_adj + up_material_adj + cfg["upcycling_bias"]

    # Costi fissi da config (per quadrante)
    cost_resale = cfg["cost_resale"][inputs.product_category][inputs.price_segment]
    cost_up = cfg["cost_upcycling"][inputs.product_category][inputs.price_segment]

    # Regola economica: Pass se (margin - cost) > threshold (qui threshold=0)
    thr = cfg["economic_threshold"]
    econ_resale = margin_resale - cost_resale
    econ_up = margin_up - cost_up
    feasible_resale = econ_resale > thr
    feasible_upcycling = econ_up > thr

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

def compute_operational(delta_resale_minus_up: float, cfg: Dict[str, Any]) -> OperationalResult:
    band = cfg["operational_neutral_band"]
    if abs(delta_resale_minus_up) <= band:
        tag = "Neutral"
    elif delta_resale_minus_up > band:
        tag = "Preference resale"
    else:
        tag = "Preference upcycling"
    return OperationalResult(delta_resale_minus_up, tag)

def compute_environment(category: str, segment: str, cfg: Dict[str, Any]) -> EnvironmentalResult:
    node = cfg["environment_matrix"][category][segment]
    env_resale = node["resale"]
    env_up = node["upcycling"]
    delta = env_resale - env_up  # positivo => Resale migliore (impatto minore)
    band = cfg["environment_neutral_band"]

    if abs(delta) <= band:
        tag = "Neutral"
    elif delta > band:
        tag = "Preference resale"
    else:
        tag = "Preference upcycling"

    return EnvironmentalResult(env_resale, env_up, delta, tag)

def recommend(econ: EconomicResult, oper: OperationalResult, env: EnvironmentalResult, cfg: Dict[str, Any]) -> Recommendation:
    # 1) vincolo economico (gating)
    if econ.feasible_upcycling and not econ.feasible_resale:
        label = "Upcycling only"
    elif econ.feasible_resale and not econ.feasible_upcycling:
        label = "Resale only"
    elif not econ.feasible_resale and not econ.feasible_upcycling:
        label = "None"
    else:
        # 2) tie-breaker: operativo fuori banda
        if oper.tag == "Preference resale":
            label = "Resale only (operational preference)"
        elif oper.tag == "Preference upcycling":
            label = "Upcycling only (operational preference)"
        else:
            # 3) tie-breaker: ambientale fuori banda
            if env.tag == "Preference resale":
                label = "Resale only (environmental preference)"
            elif env.tag == "Preference upcycling":
                label = "Upcycling only (environmental preference)"
            else:
                label = "Both feasible"

    # Rationale (parlante)
    if label.startswith("Upcycling"):
        rationale_econ = "Upcycling supera la regola economica (margin − cost > 0), resale no."             if (econ.feasible_upcycling and not econ.feasible_resale) else             "Entrambe le strategie superano la soglia: preferenza verso Upcycling per operativo/ambiente."
    elif label.startswith("Resale"):
        rationale_econ = "Resale supera la regola economica (margin − cost > 0), upcycling no."             if (econ.feasible_resale and not econ.feasible_upcycling) else             "Entrambe le strategie superano la soglia: preferenza verso Resale per operativo/ambiente."
    elif label == "None":
        rationale_econ = "Nessuna strategia supera la regola economica (margin − cost ≤ 0)."
    else:
        rationale_econ = "Entrambe le strategie superano la regola economica (margin − cost > 0)."

    rationale_oper = f"Operational: {oper.tag} (Δ res−up = {oper.delta_resale_minus_up:.2f}, banda ±{cfg['operational_neutral_band']})."
    rationale_env = f"Environmental: {env.tag} (Δ res−up = {env.delta_resale_minus_up:.2f}, banda ±{cfg['environment_neutral_band']})."

    trace = [
        f"Economic feasibility → resale={'PASS' if econ.feasible_resale else 'FAIL'}, upcycling={'PASS' if econ.feasible_upcycling else 'FAIL'}",
        f"Operational → {oper.tag}",
        f"Environmental → {env.tag}"
    ]
    return Recommendation(label, rationale_econ, rationale_oper, rationale_env, trace)
