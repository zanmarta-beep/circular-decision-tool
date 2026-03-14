
# Circular Strategy Advisor (Streamlit)

Strumento di supporto decisionale per orientarsi tra **resale** e **upcycling**.
Replica la logica del modello Excel (sezioni A→G) in un'app web semplice e spiegabile.

## Avvio locale

```bash
python -m venv .venv
# Attiva l'ambiente:
#   Windows: .venv\Scripts\activate
#   macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Apri il browser su `http://localhost:8501`.

## Deploy su Streamlit Community Cloud

1. Crea un repository GitHub e carica questi file (root del repo):
   - `app.py`
   - `engine.py`
   - `config.json`
   - `requirements.txt`
   - `README.md`
2. Vai su https://share.streamlit.io → **New app** → collega il repo → seleziona `app.py` → **Deploy**.
3. Attendi il build (1–2 minuti). Otterrai un **URL pubblico**.

## Parametri chiave
- **Costi fissi** per quadrante (Categoria × Fascia) e strategia (Resale/Upcycling): definiti in `config.json`.
- **Fattibilità economica**: `margin − cost > 0`.
- **Operational feasibility**: slider `Δ (Resale − Upcycling)` con **banda di neutralità ±0,35** (tie‑breaker).
- **Ambientale**: matrice per quadrante, confronto `Δ = Env_resale − Env_upcycling` con **banda ±0,25**.

> Nota: i decimali in `config.json` devono usare il **punto** (es. `3.55`), non la virgola.

## Struttura logica
- `engine.py` contiene il motore decisionale (economico/operativo/ambientale) e la funzione `recommend(...)`.
- `app.py` gestisce la UI Streamlit (input, output, rationale, trace).
- `config.json` contiene pesi, baseline, costi fissi e bande di neutralità.

## Licenza
MIT
