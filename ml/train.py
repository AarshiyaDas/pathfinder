# ml/train.py
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib
import os

os.makedirs("models", exist_ok=True)
os.makedirs("data", exist_ok=True)

np.random.seed(42)
n = 8000

df = pd.DataFrame({
    "claim_amount":    np.random.exponential(4000, n),
    "vehicle_age":     np.random.randint(0, 20, n),
    "driver_age":      np.random.randint(18, 80, n),
    "years_insured":   np.random.randint(0, 30, n),
    "prior_claims":    np.random.poisson(0.3, n),
    "region_risk":     np.random.uniform(0.5, 2.0, n),
    "repair_cost":     np.random.exponential(2500, n),
    "days_to_report":  np.random.exponential(3, n).astype(int),
    "num_parties":     np.random.randint(1, 5, n),
    "injury_involved": np.random.choice([0, 1], n, p=[0.7, 0.3]),
    "description_len": np.random.randint(10, 500, n),
    "loss_hour":       np.random.randint(0, 24, n),
    "weekend_loss":    np.random.choice([0, 1], n, p=[0.71, 0.29]),
    "round_amount":    np.zeros(n),
    "policy_type_num": np.random.choice([0.3, 0.6, 1.0], n),
})

df["round_amount"] = ((df["claim_amount"] % 500) < 10).astype(int)

# ── Target engineering ─────────────────────────────────────
df["fraud_score"] = np.clip(
    (df["days_to_report"] / 30) * 0.25 +
    ((df["num_parties"] - 1) / 4) * 0.25 +
    (df["claim_amount"] / 25000) * 0.15 +
    (df["prior_claims"] / 5) * 0.15 +
    df["round_amount"] * 0.10 +
    ((df["loss_hour"] < 5).astype(int)) * 0.10,
    0, 1
)

df["severity_score"] = np.clip(
    (df["claim_amount"] / 25000) * 0.45 +
    (df["repair_cost"] / 18000) * 0.30 +
    df["injury_involved"] * 0.25,
    0, 1
)

df["complexity_score"] = np.clip(
    ((df["num_parties"] - 1) / 4) * 0.35 +
    df["injury_involved"] * 0.30 +
    df["policy_type_num"] * 0.20 +
    (df["description_len"] / 500) * 0.15,
    0, 1
)

df["urgency_score"] = np.clip(
    df["injury_involved"] * 0.50 +
    df["severity_score"] * 0.30 +
    ((df["region_risk"] - 0.5) / 1.5) * 0.20,
    0, 1
)

df["litigation_score"] = np.clip(
    df["injury_involved"] * 0.40 +
    ((df["num_parties"] - 1) / 4) * 0.30 +
    (df["prior_claims"] / 5) * 0.20 +
    df["policy_type_num"] * 0.10,
    0, 1
)

# ── Features ───────────────────────────────────────────────
FEATURES = [
    "claim_amount", "vehicle_age", "driver_age", "years_insured",
    "prior_claims", "region_risk", "repair_cost", "days_to_report",
    "num_parties", "injury_involved", "description_len",
    "loss_hour", "weekend_loss", "round_amount", "policy_type_num"
]

TARGETS = {
    "fraud":      "fraud_score",
    "severity":   "severity_score",
    "complexity": "complexity_score",
    "urgency":    "urgency_score",
    "litigation": "litigation_score",
}

X = df[FEATURES]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ── Train ──────────────────────────────────────────────────
print("\n── Training Claim DNA models ──\n")

for name, target_col in TARGETS.items():
    y = df[target_col]
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )
    model = GradientBoostingRegressor(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42
    )
    model.fit(X_train, y_train)
    mae = mean_absolute_error(y_test, model.predict(X_test))
    print(f"  {name:<12} MAE: {mae:.4f}")
    joblib.dump(model, f"models/{name}_model.pkl")

# ── Save embeddings for similarity search ─────────────────
df_save = df[FEATURES + list(TARGETS.values())].copy()
df_save.to_pickle("data/claim_history.pkl")
np.save("data/embeddings.npy", X_scaled)

joblib.dump(scaler, "models/scaler.pkl")
joblib.dump(FEATURES, "models/features.pkl")

print("\n✓ All 5 models saved")
print("✓ Claim history + embeddings saved")
print("✓ Ready for Phase 2\n")
