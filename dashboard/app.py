import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Pathfinder", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    /* ── Global ── */
    .block-container { padding: 2rem 3rem; }
    
    /* ── Header ── */
    .pf-header {
        background: #1a3a2a;
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .pf-title { font-size: 28px; font-weight: 700; margin: 0; }
    .pf-subtitle { font-size: 14px; opacity: 0.7; margin: 0; }

    /* ── Cards ── */
    .pf-card {
        background: white;
        border: 1px solid #e8ede9;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .pf-card-title {
        font-size: 13px;
        font-weight: 600;
        color: #6b7b6e;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 1rem;
    }

    /* ── Decision banner ── */
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

    /* ── Form ── */
    .pf-form-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
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

    /* ── Why card ── */
    .why-card {
        background: #f8faf9;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 6px;
        border-left: 3px solid #2d8653;
        font-size: 13px;
        color: #2c3e30;
    }

    /* ── Score pill ── */
    .score-pill {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    /* ── Tab styling ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #e8ede9;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 600;
        color: #6b7b6e;
    }
    .stTabs [aria-selected="true"] {
        background: #1a3a2a !important;
        color: white !important;
    }

    /* ── Button ── */
    .stButton > button {
        background: #1a3a2a;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 15px;
        width: 100%;
    }
    .stButton > button:hover {
        background: #2d8653;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="pf-header">
    <div>
        <div class="pf-title">Pathfinder</div>
        <div class="pf-subtitle">Intelligent Claim Triage & Decision Support · Powered by Guidewire ClaimCenter</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2 = st.tabs([" Score a Claim", "Batch Scoring"])

# ════════════════════════════════════════════════════════════
# TAB 1 — Single claim
# ════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="pf-section-label">Claim Details</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        claim_amount = st.number_input("Claim Amount ($)", 500.0, 100000.0, 7500.0, step=500.0)
    with c2:
        repair_cost = st.number_input("Repair Cost ($)", 0.0, 50000.0, 4200.0, step=200.0)
    with c3:
        policy_type_num = st.selectbox("Policy Type", [0.3, 0.6, 1.0], index=2,
            format_func=lambda x: {0.3:"Comprehensive", 0.6:"Fire & Theft", 1.0:"Third Party"}[x])
    with c4:
        days_to_report = st.slider("Days to Report", 0, 60, 12)

    st.markdown('<div class="pf-section-label">Vehicle & Driver</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        vehicle_age = st.slider("Vehicle Age (years)", 0, 20, 5)
    with c2:
        driver_age = st.slider("Driver Age", 18, 80, 34)
    with c3:
        years_insured = st.slider("Years Insured", 0, 30, 3)
    with c4:
        prior_claims = st.slider("Prior Claims", 0, 10, 1)

    st.markdown('<div class="pf-section-label">Incident Details</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        num_parties = st.slider("Number of Parties", 1, 5, 2)
    with c2:
        injury_involved = st.selectbox("Injury Involved", [0,1], index=1,
            format_func=lambda x: "Yes" if x else "No")
    with c3:
        loss_hour = st.slider("Hour of Loss (0-23)", 0, 23, 2)
    with c4:
        weekend_loss = st.selectbox("Weekend Loss", [0,1], index=0,
            format_func=lambda x: "Yes" if x else "No")
    with c5:
        region_risk = st.slider("Region Risk", 0.5, 2.0, 1.4, step=0.1)

    description_len = st.slider("Claim Description Length (chars)", 10, 500, 320)

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
            "AUTO_SETTLE":"✅","SENIOR_ADJUSTER":"⚠️",
            "STANDARD_ADJUSTER":"📋","SIU_ESCALATION":"🚨","HUMAN_REVIEW":"🔍"
        }

        st.divider()

        # Decision banner
        st.markdown(f"""
        <div class="decision-box {css_map.get(decision,'standard')}">
            {emoji_map.get(decision,'📋')} {decision.replace('_',' ')}
            <div style="font-size:14px;font-weight:400;margin-top:4px">{routing['reason']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.caption(
            f"Claim ID: `{data['claim_id']}` · "
            f"Confidence: `{data['confidence']}` · "
            f"Uncertainty: `{data['uncertainty']}`"
        )

        st.divider()

        # Radar + breakdown
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
                polar=dict(
                    radialaxis=dict(visible=True, range=[0,1]),
                    bgcolor="rgba(0,0,0,0)"
                ),
                showlegend=False,
                margin=dict(l=40,r=40,t=20,b=20),
                height=360,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Score Breakdown**")
            icons  = {"fraud":"","severity":"","complexity":"","urgency":"","litigation":""}
            colors = {"fraud":"#dc3545","severity":"#fd7e14","complexity":"#d4ac0d","urgency":"#0d6efd","litigation":"#6f42c1"}
            for dim, score in scores.items():
                pct = int(score * 100)
                st.markdown(f"{icons[dim]} **{dim.capitalize()}** — {pct}%")
                st.progress(score)

        st.divider()

        # Why these scores
        st.markdown("**Why These Scores?**")
        st.caption("Interpretable AI — every decision is fully auditable")
        dim_emoji = {"fraud":"","severity":"","complexity":"","urgency":"","litigation":""}
        cols = st.columns(5)
        for i, (dim, factors) in enumerate(explanations.items()):
            with cols[i]:
                st.markdown(f"**{dim_emoji[dim]} {dim.capitalize()}**")
                st.markdown(f"`{int(scores[dim]*100)}%`")
                if factors:
                    for f in factors:
                        st.markdown(
                            f"<div class='why-card'>↑ {f['factor']}<br>"
                            f"<small>+{int(f['contribution']*100)}% weight</small></div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown("_No strong signals_")

        st.divider()

        # Similar claims
        st.markdown("**Most Similar Historical Claims**")
        st.caption("Semantic similarity search across 8,000 historical claims")
        df_sim = pd.DataFrame(similar)
        df_sim.columns = [c.replace("_"," ").title() for c in df_sim.columns]
        df_sim["Similarity"] = df_sim["Similarity"].apply(lambda x: f"{x:.1%}")
        st.dataframe(df_sim, use_container_width=True, hide_index=True)

        st.divider()

        # Feedback
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
                st.success(f"✓ Logged. Total records: {fb['records']}")

# ════════════════════════════════════════════════════════════
# TAB 2 — Batch scoring
# ════════════════════════════════════════════════════════════
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

                st.success(f"✓ {batch_data['total']} claims scored successfully")

                decision_icons = {
                    "AUTO_SETTLE":       "AUTO SETTLE",
                    "STANDARD_ADJUSTER": "STANDARD ADJUSTER",
                    "SENIOR_ADJUSTER":   "SENIOR ADJUSTER",
                    "HUMAN_REVIEW":      "HUMAN REVIEW",
                    "SIU_ESCALATION":    "SIU ESCALATION",
                }
                df_display = df_batch.copy()
                df_display["decision"] = df_display["decision"].map(
                    lambda x: decision_icons.get(x, x)
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

                # Clean CSV download — no emojis
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

    # Feedback summary at bottom
    st.divider()
    st.markdown("** Feedback Pipeline Summary**")
    try:
        summary = requests.get(f"{API_URL}/feedback/summary").json()
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Total feedback records", summary["total"])
        with m2:
            st.metric("Decisions tracked", len(summary.get("decisions", {})))
        if summary.get("decisions"):
            st.bar_chart(summary["decisions"])
    except:
        st.caption("API not reachable")
