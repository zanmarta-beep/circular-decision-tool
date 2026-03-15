
# Circular Strategy Advisor (Streamlit) — v0.2

Questa versione implementa la **logica operativa deterministica** allineata a Excel:

```
Adjusted Resale Gap     = Resale Economic Gap × Scale Context
Adjusted Upcycling Gap  = (Adjusted Upcycling Gap da tabella) × Scale Context
Δ operativo             = (Resale Economic Gap − Adjusted Upcycling Gap) × Scale Context
```

La Sezione D mostra **Resale only / Upcycling only / None feasible** se lo Step B non è "Both feasible".
Se lo Step B è "Both feasible", applica la banda ±0,35 per classificare **Resale preferred / Upcycling preferred / Neutral**.
