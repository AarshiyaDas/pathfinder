# ml/policy_enrichment.py
# ─────────────────────────────────────────────────────────
# POLICYCENTER ENRICHMENT LAYER
# In production this would be a real API call to Guidewire
# PolicyCenter via the Integration Framework REST gateway.
# Here we simulate the enrichment with realistic derived data.
#
# Why this matters: ClaimCenter alone sees the claim.
# PolicyCenter adds context — how long has this policy existed,
# what's the premium tier, any prior disputes, payment history.
# Cross-system context dramatically improves triage accuracy.
# ─────────────────────────────────────────────────────────

import random
import hashlib

def enrich_from_policy(claim_data: dict) -> dict:
    """
    Simulates a PolicyCenter API call.
    Uses claim fields to derive realistic policy context.
    In production: GET /pc/rest/v1/policies/{policy_id}
    """

    # Use claim amount + years insured as a seed for consistency
    seed = int(claim_data.get("claim_amount", 5000)) + \
           int(claim_data.get("years_insured", 3)) * 1000
    rng = random.Random(seed)

    years_insured   = claim_data.get("years_insured", 3)
    prior_claims    = claim_data.get("prior_claims", 0)
    policy_type_num = claim_data.get("policy_type_num", 0.6)
    claim_amount    = claim_data.get("claim_amount", 5000)

    # Derive premium tier from policy type and years insured
    if policy_type_num == 0.3 and years_insured > 5:
        premium_tier = "PLATINUM"
    elif policy_type_num == 0.3 or years_insured > 3:
        premium_tier = "GOLD"
    elif policy_type_num == 0.6:
        premium_tier = "SILVER"
    else:
        premium_tier = "STANDARD"

    # Payment history score (0-100, higher = better)
    base_payment_score = max(0, 95 - (prior_claims * 12) - rng.randint(0, 10))

    # Policy age risk flag
    policy_age_flag = "NEW_BUSINESS_RISK" if years_insured < 1 else \
                      "RECENT_POLICY" if years_insured < 3 else "ESTABLISHED"

    # Claims frequency risk
    claims_per_year = prior_claims / max(years_insured, 1)
    claims_frequency = "HIGH" if claims_per_year > 0.5 else \
                       "MODERATE" if claims_per_year > 0.2 else "LOW"

    # Coverage adequacy — is claim amount close to or over policy limit
    estimated_limit = {"PLATINUM": 100000, "GOLD": 50000,
                       "SILVER": 25000, "STANDARD": 15000}[premium_tier]
    coverage_ratio  = round(claim_amount / estimated_limit, 3)
    coverage_flag   = "NEAR_LIMIT" if coverage_ratio > 0.7 else \
                      "MODERATE"   if coverage_ratio > 0.4 else "ADEQUATE"

    # Overall policy risk score (0-1)
    policy_risk_score = round(
        (1 - base_payment_score / 100) * 0.3 +
        (1 if policy_age_flag == "NEW_BUSINESS_RISK" else
         0.5 if policy_age_flag == "RECENT_POLICY" else 0) * 0.3 +
        (1 if claims_frequency == "HIGH" else
         0.5 if claims_frequency == "MODERATE" else 0) * 0.2 +
        min(coverage_ratio, 1.0) * 0.2,
        4
    )

    return {
        "policy_source":       "Guidewire PolicyCenter (simulated)",
        "premium_tier":        premium_tier,
        "payment_score":       base_payment_score,
        "policy_age_flag":     policy_age_flag,
        "claims_frequency":    claims_frequency,
        "coverage_ratio":      coverage_ratio,
        "coverage_flag":       coverage_flag,
        "estimated_limit":     estimated_limit,
        "policy_risk_score":   policy_risk_score,
        "pc_recommendation":   _pc_recommendation(policy_risk_score, policy_age_flag, claims_frequency),
    }


def _pc_recommendation(risk_score: float, age_flag: str, freq: str) -> str:
    if risk_score > 0.6 or age_flag == "NEW_BUSINESS_RISK":
        return "ENHANCED_SCRUTINY"
    if risk_score > 0.35 or freq == "HIGH":
        return "STANDARD_REVIEW"
    return "FAST_TRACK_ELIGIBLE"
