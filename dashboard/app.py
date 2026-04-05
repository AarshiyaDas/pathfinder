import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd

API_URL = "http://127.0.0.1:8000"

SCENARIOS = {
    "Select a scenario...": None,
    "Clean Low-Risk Claim": {
        "claim_amount": 1200.0, "repair_cost": 950.0, "vehicle_age": 3,
        "driver_age": 45, "years_insured": 12, "prior_claims": 0,
        "region_risk": 0.7, "days_to_report": 1, "num_parties": 1,
        "injury_involved": 0, "loss_hour": 14, "weekend_loss": 0,
        "description_len": 180, "policy_type_num": 0.3,
        "_note": "Long-term customer, single party, daytime loss, no injury. Expected: AUTO SETTLE"
    },
    "Suspected Fraud": {
        "claim_amount": 14500.0, "repair_cost": 1100.0, "vehicle_age": 14,
        "driver_age": 26, "years_insured": 0, "prior_claims": 3,
        "region_risk": 1.9, "days_to_report": 42, "num_parties": 4,
        "injury_involved": 1, "loss_hour": 2, "weekend_loss": 1,
        "description_len": 45, "policy_type_num": 1.0,
        "_note": "New policy, 3am loss, 42 days to report, 4 parties. Expected: SIU ESCALATION"
    },
    "High Litigation Risk": {
        "claim_amount": 22000.0, "repair_cost": 15000.0, "vehicle_age": 2,
        "driver_age": 34, "years_insured": 3, "prior_claims": 2,
        "region_risk": 1.6, "days_to_report": 5, "num_parties": 3,
        "injury_involved": 1, "loss_hour": 8, "weekend_loss": 0,
        "description_len": 420, "policy_type_num": 1.0,
        "_note": "Injury, 3 parties, prior claims, high amount. Expected: SENIOR ADJUSTER"
    },
    "Ambiguous — Low Confidence": {
        "claim_amount": 4500.0, "repair_cost": 3800.0, "vehicle_age": 7,
        "driver_age": 38, "years_insured": 5, "prior_claims": 1,
        "region_risk": 1.1, "days_to_report": 8, "num_parties": 2,
        "injury_involved": 0, "loss_hour": 19, "weekend_loss": 1,
        "description_len": 210, "policy_type_num": 0.6,
        "_note": "Mixed signals across all dimensions. Expected: HUMAN REVIEW"
    },
    "Mass Casualty Event": {
        "claim_amount": 85000.0, "repair_cost": 42000.0, "vehicle_age": 1,
        "driver_age": 29, "years_insured": 2, "prior_claims": 0,
        "region_risk": 2.0, "days_to_report": 0, "num_parties": 5,
        "injury_involved": 1, "loss_hour": 17, "weekend_loss": 0,
        "description_len": 490, "policy_type_num": 1.0,
        "_note": "Maximum severity — multi-vehicle, injuries, catastrophic loss. Expected: SIU ESCALATION"
    },
}

st.set_page_config(page_title="Pathfinder", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    .block-container { padding: 2rem 3rem; }
    .pf-header {
        background: #1a3a2a;
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .pf-title { font-size: 28px; font-weight: 700; letter-spacing: -0.5px; margin: 0; }
    .pf-subtitle { font-size: 14px; opacity: 0.7; margin: 4px 0 0 0; }
    .decision-box {
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 1rem;
        border-left: 5px solid;
    }
    .auto-settle   { background:#f0faf4; color:#1a5c35; border-color:#2d8653; }
    .senior        { background:#fffbf0; color:#7a5c00; border-color:#c49a00; }
    .standard      { background:#f0f5ff; color:#1a3a7a; border-color:#2d5be3; }
    .escalate      { background:#fff0f0; color:#7a1a1a; border-color:#e33d2d; }
    .human-review  { background:#f5f0ff; color:#3d1a7a; border-color:#7c3de3; }
    .why-card {
        background: #f8faf9;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 6px;
        border-left: 3px solid #2d8653;
        font-size: 13px;
        color: #2c3e30;
    }
    .pf-section-label {
        font-size: 13px;
        font-weight: 600;
        color: #1a3a2a;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 0.5rem 0;
        border-bottom: 2px solid #1a3a2a;
        margin-bottom: 1rem;
        margin-top: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #e8ede9; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 8px 20px; font-weight: 600; color: #6b7b6e; }
    .stTabs [aria-selected="true"] { background: #1a3a2a !important; color: white !important; }
    .stButton > button {
        background: #1a3a2a; color: white; border: none;
        border-radius: 8px; padding: 0.6rem 2rem;
        font-weight: 600; font-size: 15px; width: 100%;
    }
    .stButton > button:hover { background: #2d8653; color: white; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="pf-header">
    <div class="pf-title">Pathfinder</div>
    <div class="pf-subtitle">Intelligent Claim Triage & Decision Support · Powered by Guidewire ClaimCenter</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Score a Claim", "Batch Scoring", "Audit Log"])

# ════════════════════════════════════════════════
# TAB 1 — Single claim
# ════════════════════════════════════════════════
with tab1:

    # Scenario selector
    selected_scenario = st.selectbox(
        "Quick-load a demo scenario",
        list(SCENARIOS.keys()),
        index=0
    )
    scenario_data = SCENARIOS[selected_scenario]
    if scenario_data:
        st.info(f"Scenario note: {scenario_data.get('_note','')}")

    def get_val(key, default):
        if scenario_data and key in scenario_data:
            return scenario_data[key]
        return default

    st.markdown('<div class="pf-section-label">Claim Details</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        claim_amount = st.number_input("Claim Amount ($)", 500.0, 100000.0,
            float(get_val("claim_amount", 7500.0)), step=500.0)
    with c2:
        repair_cost = st.number_input("Repair Cost ($)", 0.0, 50000.0,
            float(get_val("repair_cost", 4200.0)), step=200.0)
    with c3:
        policy_type_num = st.selectbox("Policy Type", [0.3, 0.6, 1.0],
            index=[0.3,0.6,1.0].index(float(get_val("policy_type_num", 1.0))),
            format_func=lambda x: {0.3:"Comprehensive",0.6:"Fire & Theft",1.0:"Third Party"}[x])
    with c4:
        days_to_report = st.slider("Days to Report", 0, 60,
            int(get_val("days_to_report", 12)))

    st.markdown('<div class="pf-section-label">Vehicle & Driver</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        vehicle_age = st.slider("Vehicle Age (years)", 0, 20,
            int(get_val("vehicle_age", 5)))
    with c2:
        driver_age = st.slider("Driver Age", 18, 80,
            int(get_val("driver_age", 34)))
    with c3:
        years_insured = st.slider("Years Insured", 0, 30,
            int(get_val("years_insured", 3)))
    with c4:
        prior_claims = st.slider("Prior Claims", 0, 10,
            int(get_val("prior_claims", 1)))

    st.markdown('<div class="pf-section-label">Incident Details</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        num_parties = st.slider("Number of Parties", 1, 5,
            int(get_val("num_parties", 2)))
    with c2:
        injury_involved = st.selectbox("Injury Involved", [0,1],
            index=int(get_val("injury_involved", 1)),
            format_func=lambda x: "Yes" if x else "No")
    with c3:
        loss_hour = st.slider("Hour of Loss (0-23)", 0, 23,
            int(get_val("loss_hour", 2)))
    with c4:
        weekend_loss = st.selectbox("Weekend Loss", [0,1],
            index=int(get_val("weekend_loss", 0)),
            format_func=lambda x: "Yes" if x else "No")
    with c5:
        region_risk = st.slider("Region Risk", 0.5, 2.0,
            float(get_val("region_risk", 1.4)), step=0.1)

    description_len = st.slider("Claim Description Length (chars)", 10, 500,
        int(get_val("description_len", 320)))

    st.markdown("<br>", unsafe_allow_html=True)
    score_btn = st.button("Run Pathfinder Analysis")

    if score_btn:
        payload = {
            "claim_amount": claim_amount, "vehicle_age": vehicle_age,
            "driver_age": driver_age, "years_insured": years_insured,
            "prior_claims": prior_claims, "region_risk": region_risk,
            "repair_cost": repair_cost, "days_to_report": days_to_report,
            "num_parties": num_parties, "injury_involved": injury_involved,
            "description_len": description_len, "loss_hour": loss_hour,
            "weekend_loss": weekend_loss, "policy_type_num": policy_type_num,
        }

        with st.spinner("Pathfinder is analysing this claim..."):
            try:
                res  = requests.post(f"{API_URL}/score", json=payload)
                data = res.json()
            except Exception as e:
                st.error(f"API error: {e}")
                st.stop()

        scores       = data["dna_scores"]
        routing      = data["routing"]
        decision     = routing["decision"]
        similar      = data["similar_claims"]
        explanations = data.get("explanations", {})

        css_map = {
            "AUTO_SETTLE":"auto-settle","SENIOR_ADJUSTER":"senior",
            "STANDARD_ADJUSTER":"standard","SIU_ESCALATION":"escalate",
            "HUMAN_REVIEW":"human-review"
        }
        emoji_map = {
            "AUTO_SETTLE":"✓","SENIOR_ADJUSTER":"!",
            "STANDARD_ADJUSTER":"→","SIU_ESCALATION":"✗","HUMAN_REVIEW":"?"
        }

        st.divider()

        st.markdown(f"""
        <div class="decision-box {css_map.get(decision,'standard')}">
            {emoji_map.get(decision,'')} {decision.replace('_',' ')}
            <div style="font-size:14px;font-weight:400;margin-top:4px">{routing['reason']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.caption(
            f"Claim ID: `{data['claim_id']}` · "
            f"Confidence: `{data['confidence']}` · "
            f"Uncertainty: `{data['uncertainty']}`"
        )
        st.divider()

        col1, col2 = st.columns([1.3, 1])
        with col1:
            st.markdown("**DNA Score Radar**")
            dims = list(scores.keys())
            vals = list(scores.values())
            vals += [vals[0]]
            dims += [dims[0]]
            fig = go.Figure(go.Scatterpolar(
                r=vals, theta=dims, fill="toself",
                fillcolor="rgba(45,134,83,0.15)",
                line=dict(color="#1a3a2a", width=2),
                marker=dict(size=6, color="#2d8653")
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0,1]),
                           bgcolor="rgba(0,0,0,0)"),
                showlegend=False,
                margin=dict(l=40,r=40,t=20,b=20),
                height=360,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Score Breakdown**")
            dims_list = ["fraud","severity","complexity","urgency","litigation"]
            for dim in dims_list:
                score = scores[dim]
                pct   = int(score * 100)
                st.markdown(f"**{dim.capitalize()}** — {pct}%")
                st.progress(score)

        st.divider()

        st.markdown("**Why These Scores?**")
        st.caption("Interpretable AI — every decision is fully auditable by adjusters and regulators")
        cols = st.columns(5)
        for i, (dim, factors) in enumerate(explanations.items()):
            with cols[i]:
                st.markdown(f"**{dim.capitalize()}**")
                st.markdown(f"`{int(scores[dim]*100)}%`")
                if factors:
                    for f in factors:
                        st.markdown(
                            f"<div class='why-card'>{f['factor']}<br>"
                            f"<small>+{int(f['contribution']*100)}% weight</small></div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown("_No strong signals_")

        st.divider()

        st.markdown("**Most Similar Historical Claims**")
        st.caption("Cosine similarity search across 8,000 historical claims")
        df_sim = pd.DataFrame(similar)
        df_sim.columns = [c.replace("_"," ").title() for c in df_sim.columns]
        df_sim["Similarity"] = df_sim["Similarity"].apply(lambda x: f"{x:.1%}")
        st.dataframe(df_sim, use_container_width=True, hide_index=True)

        st.divider()

        st.markdown("**Submit Adjuster Feedback**")
        st.caption("Outcomes feed back into the model retraining pipeline")
        fc1, fc2, fc3 = st.columns([1,1,1])
        with fc1:
            adj_decision = st.selectbox("Adjuster decision",
                ["auto_settle","route","escalate"])
        with fc2:
            actual_outcome = st.selectbox("Actual outcome",
                ["settled","fraud_confirmed","litigated","pending"])
        with fc3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Submit Feedback"):
                fb = requests.post(f"{API_URL}/feedback", json={
                    "claim_id":          data["claim_id"],
                    "adjuster_decision": adj_decision,
                    "actual_outcome":    actual_outcome,
                }).json()
                st.success(f"Logged. Total records: {fb['records']}")

# ════════════════════════════════════════════════
# TAB 2 — Batch scoring
# ════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="pf-section-label">Batch Claim Scoring</div>', unsafe_allow_html=True)
    st.info("Upload a CSV file containing claim data. All 14 required fields must be present as column headers.")

    col1, col2 = st.columns([2,1])
    with col1:
        uploaded = st.file_uploader("Upload claims CSV", type="csv")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Required columns:**")
        st.caption("claim_amount, vehicle_age, driver_age, years_insured, prior_claims, region_risk, repair_cost, days_to_report, num_parties, injury_involved, description_len, loss_hour, weekend_loss, policy_type_num")

    if uploaded:
        if st.button("Score All Claims"):
            with st.spinner("Pathfinder is scoring all claims..."):
                res = requests.post(
                    f"{API_URL}/score/batch",
                    files={"file": ("claims.csv", uploaded, "text/csv")}
                )
            if res.status_code == 200:
                batch_data = res.json()
                df_batch   = pd.DataFrame(batch_data["results"])

                st.success(f"{batch_data['total']} claims scored successfully")

                df_display = df_batch.copy()
                df_display["decision"] = df_display["decision"].apply(
                    lambda x: x.replace("_"," ")
                )
                st.dataframe(df_display, use_container_width=True, hide_index=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Decision Breakdown**")
                    st.bar_chart(df_display["decision"].value_counts())
                with col2:
                    st.markdown("**Risk Score Averages**")
                    avg_scores = df_batch[["fraud","severity","complexity","urgency","litigation"]].mean()
                    st.bar_chart(avg_scores)

                csv_out = df_batch.to_csv(index=False, encoding="utf-8")
                st.download_button(
                    "Download Results CSV",
                    csv_out.encode("utf-8"),
                    "pathfinder_batch_results.csv",
                    "text/csv",
                    use_container_width=True
                )
            else:
                st.error(f"Batch error: {res.text}")

    st.divider()
    st.markdown("**Feedback Pipeline Summary**")
    try:
        summary = requests.get(f"{API_URL}/feedback/summary").json()
        m1, m2  = st.columns(2)
        with m1:
            st.metric("Total feedback records", summary["total"])
        with m2:
            st.metric("Decisions tracked", len(summary.get("decisions", {})))
        if summary.get("decisions"):
            st.bar_chart(summary["decisions"])
    except:
        st.caption("API not reachable")
# ════════════════════════════════════════════════
# TAB 3 — Audit Log
# ════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="pf-section-label">Regulatory Audit Log</div>',
                unsafe_allow_html=True)
    st.caption("Full decision history — GDPR Article 22 compliant · Every decision is logged, explainable and auditable")

    try:
        audit_res = requests.get(f"{API_URL}/audit")
        audit_data = audit_res.json()
        records = audit_data.get("records", [])

        if not records:
            st.info("No decisions logged yet. Score some claims to populate the audit log.")
        else:
            # ── Summary metrics ───────────────────────────
            total = audit_data["total"]
            decisions = [r["decision"] for r in records]
            high_conf = sum(1 for r in records if r["confidence"] == "HIGH")

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Total Decisions", total)
            with m2:
                st.metric("High Confidence", high_conf)
            with m3:
                st.metric("Escalations", decisions.count("SIU_ESCALATION"))
            with m4:
                st.metric("Auto Settled", decisions.count("AUTO_SETTLE"))

            st.divider()

            # ── Filter ────────────────────────────────────
            col1, col2 = st.columns(2)
            with col1:
                filter_decision = st.selectbox(
                    "Filter by decision",
                    ["All"] + list(set(decisions))
                )
            with col2:
                filter_confidence = st.selectbox(
                    "Filter by confidence",
                    ["All", "HIGH", "LOW"]
                )

            # Apply filters
            filtered = records
            if filter_decision != "All":
                filtered = [r for r in filtered if r["decision"] == filter_decision]
            if filter_confidence != "All":
                filtered = [r for r in filtered if r["confidence"] == filter_confidence]

            st.caption(f"Showing {len(filtered)} of {total} records")

            # ── Table ─────────────────────────────────────
            df_audit = pd.DataFrame([{
                "Timestamp":   r["timestamp"][:19].replace("T", " "),
                "Claim ID":    r["claim_id"],
                "Decision":    r["decision"].replace("_", " "),
                "Confidence":  r["confidence"],
                "Fraud":       f"{int(r['dna_scores'].get('fraud',0)*100)}%",
                "Severity":    f"{int(r['dna_scores'].get('severity',0)*100)}%",
                "Litigation":  f"{int(r['dna_scores'].get('litigation',0)*100)}%",
                "Reason":      r["reason"],
            } for r in filtered])

            st.dataframe(df_audit, use_container_width=True, hide_index=True)

            st.divider()

            # ── Decision distribution chart ───────────────
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Decision Distribution**")
                decision_counts = pd.Series(decisions).value_counts()
                decision_counts.index = decision_counts.index.str.replace("_", " ")
                st.bar_chart(decision_counts)

            with col2:
                st.markdown("**Average DNA Scores Across All Claims**")
                avg = {
                    dim: round(sum(r["dna_scores"].get(dim,0) for r in records)/len(records), 3)
                    for dim in ["fraud","severity","complexity","urgency","litigation"]
                }
                st.bar_chart(pd.Series(avg))

            st.divider()

            # ── Download full audit log ───────────────────
            st.markdown("**Download Full Audit Log**")
            st.caption("Provide this to compliance officers or regulators on request")
            audit_csv = df_audit.to_csv(index=False, encoding="utf-8")
            st.download_button(
                "Download Audit Log CSV",
                audit_csv.encode("utf-8"),
                "pathfinder_audit_log.csv",
                "text/csv",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Could not load audit log: {e}")
