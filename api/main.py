from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
import numpy as np
import joblib
import uuid
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.similarity import find_similar_claims
from ml.feedback_store import log_feedback, get_feedback_summary
from ml.policy_enrichment import enrich_from_policy

app = FastAPI(
    title="Pathfinder",
    description="Intelligent claim triage and decision support for Guidewire ClaimCenter",
    version="1.0.0"
)

print("Loading Pathfinder models...")
MODELS = {
    name: joblib.load(f"models/{name}_model.pkl")
    for name in ["fraud", "severity", "complexity", "urgency", "litigation"]
}
SCALER   = joblib.load("models/scaler.pkl")
FEATURES = joblib.load("models/features.pkl")
print("Models loaded.\n")


class ClaimInput(BaseModel):
    claim_amount:    float = Field(..., example=7500.0)
    vehicle_age:     int   = Field(..., example=5)
    driver_age:      int   = Field(..., example=34)
    years_insured:   int   = Field(..., example=3)
    prior_claims:    int   = Field(..., example=1)
    region_risk:     float = Field(..., example=1.4)
    repair_cost:     float = Field(..., example=4200.0)
    days_to_report:  int   = Field(..., example=12)
    num_parties:     int   = Field(..., example=2)
    injury_involved: int   = Field(..., example=1)
    description_len: int   = Field(..., example=320)
    loss_hour:       int   = Field(..., example=2)
    weekend_loss:    int   = Field(..., example=0)
    policy_type_num: float = Field(..., example=1.0)


class FeedbackInput(BaseModel):
    claim_id:          str
    adjuster_decision: str
    actual_outcome:    str


FEATURE_WEIGHTS = {
    "fraud": {
        "days_to_report":  ("Late filing",               0.25),
        "num_parties":     ("Multiple parties",           0.25),
        "claim_amount":    ("High claim amount",          0.15),
        "prior_claims":    ("Prior claim history",        0.15),
        "round_amount":    ("Suspiciously round amount",  0.10),
        "loss_hour":       ("Late night loss",            0.10),
    },
    "severity": {
        "claim_amount":    ("High claim amount",          0.45),
        "repair_cost":     ("High repair cost",           0.30),
        "injury_involved": ("Injury present",             0.25),
    },
    "complexity": {
        "num_parties":     ("Multiple parties",           0.35),
        "injury_involved": ("Injury present",             0.30),
        "policy_type_num": ("Complex policy type",        0.20),
        "description_len": ("Detailed description",       0.15),
    },
    "urgency": {
        "injury_involved": ("Injury present",             0.50),
        "severity_score":  ("High severity",              0.30),
        "region_risk":     ("High risk region",           0.20),
    },
    "litigation": {
        "injury_involved": ("Injury present",             0.40),
        "num_parties":     ("Multiple parties",           0.30),
        "prior_claims":    ("Prior claim history",        0.20),
        "policy_type_num": ("Complex policy type",        0.10),
    },
}

def explain_scores(claim: ClaimInput, dna_scores: dict) -> dict:
    raw_values = {
        "days_to_report":  min(claim.days_to_report / 30, 1.0),
        "num_parties":     min((claim.num_parties - 1) / 4, 1.0),
        "claim_amount":    min(claim.claim_amount / 25000, 1.0),
        "prior_claims":    min(claim.prior_claims / 5, 1.0),
        "round_amount":    1.0 if claim.claim_amount % 500 < 10 else 0.0,
        "loss_hour":       1.0 if claim.loss_hour < 5 else 0.0,
        "repair_cost":     min(claim.repair_cost / 18000, 1.0),
        "injury_involved": float(claim.injury_involved),
        "policy_type_num": claim.policy_type_num,
        "description_len": min(claim.description_len / 500, 1.0),
        "region_risk":     min((claim.region_risk - 0.5) / 1.5, 1.0),
        "severity_score":  dna_scores.get("severity", 0.0),
    }
    explanations = {}
    for dimension, feature_map in FEATURE_WEIGHTS.items():
        contributions = []
        for feature, (label, weight) in feature_map.items():
            value = raw_values.get(feature, 0.0)
            contribution = round(value * weight, 4)
            if contribution > 0.02:
                contributions.append({"factor": label, "contribution": contribution})
        contributions.sort(key=lambda x: x["contribution"], reverse=True)
        explanations[dimension] = contributions[:3]
    return explanations


def compute_uncertainty(model, X_scaled: np.ndarray) -> float:
    tree_preds = np.array([
        tree.predict(X_scaled)
        for tree in model.estimators_[-1]
    ])
    variance = float(np.var(tree_preds))
    return round(min(variance * 100, 1.0), 4)


def route_claim(scores: dict, uncertainty: float) -> dict:
    fraud      = scores["fraud"]
    severity   = scores["severity"]
    litigation = scores["litigation"]
    urgency    = scores["urgency"]

    if fraud > 0.70:
        return {"decision": "SIU_ESCALATION",    "reason": "High fraud probability detected"}
    if litigation > 0.75:
        return {"decision": "SIU_ESCALATION",    "reason": "High litigation risk"}
    if uncertainty > 0.40:
        return {"decision": "HUMAN_REVIEW",      "reason": "Low model confidence — ambiguous claim profile"}
    if severity > 0.65 or urgency > 0.70:
        return {"decision": "SENIOR_ADJUSTER",   "reason": "High severity or urgency requires senior review"}
    if severity > 0.35:
        return {"decision": "STANDARD_ADJUSTER", "reason": "Moderate complexity claim"}
    return {"decision": "AUTO_SETTLE",           "reason": "Low risk across all dimensions"}


@app.post("/score")
def score_claim(claim: ClaimInput):
    raw = np.array([[
        claim.claim_amount, claim.vehicle_age, claim.driver_age,
        claim.years_insured, claim.prior_claims, claim.region_risk,
        claim.repair_cost, claim.days_to_report, claim.num_parties,
        claim.injury_involved, claim.description_len, claim.loss_hour,
        claim.weekend_loss,
        (1 if claim.claim_amount % 500 < 10 else 0),
        claim.policy_type_num,
    ]])

    X_scaled = SCALER.transform(raw)

    dna_scores = {
        name: round(float(model.predict(X_scaled)[0]), 4)
        for name, model in MODELS.items()
    }

    uncertainty    = compute_uncertainty(MODELS["fraud"], X_scaled)
    similar        = find_similar_claims(X_scaled[0], top_k=5)
    similar_claims = similar.to_dict(orient="records")
    routing        = route_claim(dna_scores, uncertainty)
    explanations   = explain_scores(claim, dna_scores)
    claim_id       = str(uuid.uuid4())[:8]

    policy_context = enrich_from_policy({
        "claim_amount":    claim.claim_amount,
        "years_insured":   claim.years_insured,
        "prior_claims":    claim.prior_claims,
        "policy_type_num": claim.policy_type_num,
    })

    # Audit log
    audit_record = {
        "claim_id":           claim_id,
        "timestamp":          datetime.now().isoformat(),
        "dna_scores":         dna_scores,
        "uncertainty":        uncertainty,
        "confidence":         "LOW" if uncertainty > 0.4 else "HIGH",
        "decision":           routing["decision"],
        "reason":             routing["reason"],
        "top_fraud_factors":  explanations.get("fraud", []),
        "policy_context":     policy_context,
        "regulation_note":    "Decision generated by Pathfinder v1.0. Explainability provided under GDPR Article 22."
    }

    audit_path = "data/audit_log.json"
    audit = []
    if os.path.exists(audit_path):
        with open(audit_path) as f:
            try:
                audit = json.load(f)
            except:
                audit = []
    audit.append(audit_record)
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2)

    return {
        "claim_id":       claim_id,
        "dna_scores":     dna_scores,
        "uncertainty":    uncertainty,
        "confidence":     "LOW" if uncertainty > 0.4 else "HIGH",
        "routing":        routing,
        "similar_claims": similar_claims,
        "explanations":   explanations,
        "policy_context": policy_context,
        "guidewire_note": f"Routed via Pathfinder v1.0 | Decision: {routing['decision']}"
    }


@app.post("/score/batch")
async def score_batch(file: UploadFile = File(...)):
    import pandas as pd
    import io

    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    required = [
        "claim_amount","vehicle_age","driver_age","years_insured",
        "prior_claims","region_risk","repair_cost","days_to_report",
        "num_parties","injury_involved","description_len",
        "loss_hour","weekend_loss","policy_type_num"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    results = []
    for _, row in df.iterrows():
        raw = np.array([[
            row["claim_amount"], row["vehicle_age"], row["driver_age"],
            row["years_insured"], row["prior_claims"], row["region_risk"],
            row["repair_cost"], row["days_to_report"], row["num_parties"],
            row["injury_involved"], row["description_len"], row["loss_hour"],
            row["weekend_loss"],
            (1 if row["claim_amount"] % 500 < 10 else 0),
            row["policy_type_num"],
        ]])
        X_scaled   = SCALER.transform(raw)
        dna_scores = {
            name: round(float(model.predict(X_scaled)[0]), 4)
            for name, model in MODELS.items()
        }
        uncertainty = compute_uncertainty(MODELS["fraud"], X_scaled)
        routing     = route_claim(dna_scores, uncertainty)

        results.append({
            "claim_id":     str(uuid.uuid4())[:8],
            "claim_amount": row["claim_amount"],
            "fraud":        dna_scores["fraud"],
            "severity":     dna_scores["severity"],
            "complexity":   dna_scores["complexity"],
            "urgency":      dna_scores["urgency"],
            "litigation":   dna_scores["litigation"],
            "confidence":   "LOW" if uncertainty > 0.4 else "HIGH",
            "decision":     routing["decision"],
            "reason":       routing["reason"],
        })

    return {"total": len(results), "results": results}


@app.post("/feedback")
def submit_feedback(fb: FeedbackInput):
    result = log_feedback(
        claim_id=fb.claim_id,
        dna_scores={},
        adjuster_decision=fb.adjuster_decision,
        actual_outcome=fb.actual_outcome
    )
    return {"status": "logged", "records": result["total_feedback_records"]}


@app.get("/feedback/summary")
def feedback_summary():
    return get_feedback_summary()


@app.get("/audit")
def get_audit_log():
    audit_path = "data/audit_log.json"
    if not os.path.exists(audit_path):
        return {"total": 0, "records": []}
    with open(audit_path) as f:
        try:
            records = json.load(f)
        except:
            records = []
    return {"total": len(records), "records": records}


@app.get("/health")
def health():
    return {"status": "ok", "models_loaded": list(MODELS.keys())}
