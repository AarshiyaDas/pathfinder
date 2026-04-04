import json
import os
from datetime import datetime

FEEDBACK_FILE = "data/feedback_log.json"


def log_feedback(claim_id, dna_scores, adjuster_decision, actual_outcome):
    os.makedirs("data", exist_ok=True)
    record = {
        "claim_id": claim_id,
        "timestamp": datetime.now().isoformat(),
        "predicted_scores": dna_scores,
        "adjuster_decision": adjuster_decision,
        "actual_outcome": actual_outcome,
    }
    log = []
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE) as f:
            log = json.load(f)
    log.append(record)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(log, f, indent=2)
    return {"logged": True, "total_feedback_records": len(log)}


def get_feedback_summary():
    if not os.path.exists(FEEDBACK_FILE):
        return {"total": 0, "decisions": {}}
    with open(FEEDBACK_FILE) as f:
        log = json.load(f)
    decisions = {}
    for r in log:
        d = r["adjuster_decision"]
        decisions[d] = decisions.get(d, 0) + 1
    return {
        "total": len(log),
        "decisions": decisions,
        "latest": log[-1]["timestamp"] if log else None,
    }
