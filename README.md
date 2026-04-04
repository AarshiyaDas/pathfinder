# Pathfinder — Intelligent Claim Triage & Decision Support

> Built for enterprise insurance on Guidewire ClaimCenter

Pathfinder is an ML-powered claim triage engine that scores every incoming
claim across 5 risk dimensions simultaneously at intake — before any human
touches it. It replaces manual, inconsistent triage with a structured,
auditable, confidence-aware decision system.

---

## The Problem

Guidewire ClaimCenter stores everything needed to make a smart triage
decision at claim intake. But today, that decision is still made manually,
inconsistently, and too late. Adjusters spend 20-40% of their time just
reading and sorting claims — not working them.

---

## What Pathfinder Does Differently

### 1. 5-Dimension DNA Scoring
Every claim is scored across 5 dimensions simultaneously:
- **Fraud** — anomaly signals, late filing, suspicious patterns
- **Severity** — claim amount, repair cost, injury presence
- **Complexity** — parties involved, policy type, description depth
- **Urgency** — injury, region risk, severity interaction
- **Litigation** — injury, prior claims, multi-party exposure

### 2. Uncertainty Quantification
The system knows when it doesn't know. Claims scoring near decision
boundaries are flagged as LOW CONFIDENCE and escalated to human review
rather than forcing a bad automated decision. This is rare in student
projects and critical in production insurance AI.

### 3. Claim Similarity Search
Every scored claim is matched against 8,000 historical claims using
cosine similarity on feature embeddings — the same technique used in
vector databases like Pinecone. Adjusters see what happened to similar
past claims before making a decision.

### 4. Adjuster Feedback Loop
Adjuster outcomes are logged against model predictions. This builds the
foundation of an MLOps retraining pipeline — the model improves as
adjusters confirm or override decisions.

### 5. Batch Scoring
Upload a CSV of claims and score all of them in one request. Downloadable
results table with decision breakdown and risk score averages.

---

## Architecture
Guidewire ClaimCenter
│
▼
FastAPI Microservice (api/main.py)
│
├── 5x GradientBoosting Models (ml/train.py)
├── Cosine Similarity Search (ml/similarity.py)
└── Feedback Store (ml/feedback_store.py)
│
▼
Streamlit Dashboard (dashboard/app.py)

The API is self-documenting via OpenAPI spec at `/docs` — exactly how
Guidewire's Integration Framework would discover this microservice in a
real cloud deployment.

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Models | Scikit-learn GradientBoostingRegressor |
| API | FastAPI + Uvicorn |
| Dashboard | Streamlit + Plotly |
| Similarity Search | NumPy cosine similarity (production: Pinecone/pgvector) |
| Data | Actuarially-derived synthetic claims (8,000 records) |

---

## Running Locally
```bash
# 1. Clone and setup
git clone https://github.com/YOUR_USERNAME/pathfinder.git
cd pathfinder
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt

# 2. Train models
python ml/train.py

# 3. Start API (Terminal 1)
uvicorn api.main:app --reload

# 4. Start Dashboard (Terminal 2)
streamlit run dashboard/app.py
```

Open `http://localhost:8501` in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/score` | Score a single claim |
| POST | `/score/batch` | Score a CSV of claims |
| POST | `/feedback` | Log adjuster outcome |
| GET | `/feedback/summary` | Feedback pipeline stats |
| GET | `/health` | Service health check |
| GET | `/docs` | Interactive API documentation |

---

## Key Concepts (for interviews)

**Target Engineering** — In real insurance ML, clean labels rarely exist.
We derive 5 proxy scores from actuarial domain knowledge encoded as
weighted feature combinations. This is standard practice at insurers like
AXA, Allianz, and Zurich.

**Uncertainty Quantification** — We estimate prediction uncertainty from
the variance across individual trees in the final boosting stage. High
variance = ambiguous claim = human review. Almost no student project
implements this.

**Production Gap** — The similarity search currently runs in-memory on
8,000 claims. In production this would be replaced with a vector database
bringing search time from ~2s to <50ms at millions of claims scale.

---

## Built For

Guidewire Enterprise Cloud Engineering Elective
