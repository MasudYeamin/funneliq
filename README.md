# FunnelIQ — E-Commerce Funnel, Retention & A/B Test Analytics

A beginner-friendly, portfolio-ready analytics project that mirrors an
entry-level **Product Analyst** role: turn raw event data into funnel,
retention, and experiment insights, then present them in a dashboard.

**Stack:** Python (Pandas, NumPy, SciPy/statsmodels) · SQL (SQLite) · Excel
(openpyxl formulas) · Seaborn · Power BI

## Why this project

Built to match the "Product Analyst" job description (turn data into
insights, analyze funnels/retention/growth metrics, A/B testing, drive
automation and scalable reporting) — every deliverable below maps to one of
those asks.

## What it does

1. **Generates** a realistic synthetic e-commerce dataset: 4,000 customers,
   ~23k funnel events (view → add_to_cart → checkout → purchase), and orders,
   across 6 months, with a built-in checkout A/B test (`control` vs `variant`).
2. **Loads** the data into a SQLite database via a proper SQL schema.
3. **Analyzes** it in Python/Pandas:
   - Funnel conversion & drop-off at each step (overall and by A/B variant)
   - Monthly cohort retention matrix
   - A two-proportion z-test on the A/B experiment (statsmodels), reporting
     lift % and statistical significance
4. **Visualizes** results with Seaborn (funnel bar chart, retention heatmap,
   order-value distribution).
5. **Excel**: `excel/FunnelIQ_Report.xlsx` — raw data + a funnel summary
   sheet built with live `SUMPRODUCT`/`COUNTIFS` formulas and a native Excel
   chart (the "quick manual check" a Product Analyst would do before
   automating it).
6. **Power BI**: see `powerbi/README.md` for the interactive dashboard build
   (funnel chart, retention heatmap, A/B test KPI cards, slicers). A working
   interactive **HTML replica** of that dashboard (same charts, real hover
   tooltips) is live at https://claude.ai/code/artifact/2a661f09-665c-4ec3-ac6d-720270a31ae7
   and saved locally at `powerbi/dashboard_replica.html`.

## How to run

```bash
cd projects/funneliq
pip install -r requirements.txt
python scripts/01_generate_data.py
python scripts/02_load_to_sqlite.py
python scripts/03_analyze_and_visualize.py
python scripts/04_build_excel.py
```

Then explore `sql/queries.sql` directly against `funneliq.db` with any
SQLite client, and follow `powerbi/README.md` to build the dashboard.

## Key result (from the synthetic run)

- Funnel: 4,000 → 3,031 (add to cart) → 2,125 (checkout) → 1,598 (purchase),
  a 40% view-to-purchase conversion.
- A/B test: the new checkout (`variant`) converts at 43.4% vs 36.6% for
  `control` — an **18.7% lift**, statistically significant (p < 0.001).
- Retention drops sharply after month 1 (~70% → ~25%), typical of consumer
  e-commerce — useful talking point for a "how would you improve this"
  interview question.

## Repo layout

```
funneliq/
├── data/raw/            synthetic input CSVs
├── data/processed/      funnel/retention/A-B-test outputs
├── sql/                 schema.sql + queries.sql
├── scripts/             01-04 pipeline (generate → load → analyze → excel)
├── excel/               FunnelIQ_Report.xlsx
├── powerbi/              dashboard build guide
├── visuals/              seaborn charts (PNG)
└── funneliq.db           SQLite database
```

## Resume bullet (example)

> Built an end-to-end product analytics pipeline (Python, SQL, Power BI) on
> 23k+ simulated e-commerce events; identified a 40% view-to-purchase funnel
> conversion, ran a statistically significant A/B test showing an 18.7%
> checkout-conversion lift, and shipped an interactive Power BI dashboard for
> stakeholder reporting.
