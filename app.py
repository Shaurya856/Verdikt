"""Streamlit frontend for the Document Verification System."""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Document Verification System",
    page_icon="🔍",
    layout="wide",
)

# ── Styles ────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    .metric-card {
        background: #f0f2f6;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .label-supported  { color: #1a7f37; font-weight: 600; }
    .label-contradicted { color: #cf222e; font-weight: 600; }
    .label-not_found  { color: #6e7781; font-weight: 600; }
    .label-satisfied  { color: #1a7f37; font-weight: 600; }
    .label-violated   { color: #cf222e; font-weight: 600; }
    .label-missing    { color: #9a6700; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────

st.title("🔍 Document Verification System")
st.caption("Evidence-grounded, claim-level verification — no black-box confidence scores.")

# ── API key check ─────────────────────────────────────────────────────────────

api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", "")
if not api_key:
    st.error(
        "**GOOGLE_API_KEY not set.**  \n"
        "Add it to `.env` locally, or to **Secrets** in the Streamlit Cloud dashboard."
    )
    st.stop()

os.environ["GOOGLE_API_KEY"] = api_key

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Settings")
    mode = st.radio("Mode", ["Fact Verification", "Guideline Compliance"], index=0)

    st.divider()

    if mode == "Fact Verification":
        st.subheader("Evidence Sources")
        use_wikipedia = st.toggle("Wikipedia", value=True)
        use_arxiv = st.toggle("arXiv", value=True)
        st.caption("Evidence is retrieved from the selected sources and used only for NLI — not injected as truth.")
    else:
        st.caption("Guideline mode checks the document against your rules without external evidence.")

    st.divider()
    st.markdown(
        "**How it works**  \n"
        "1. Claims / constraints are extracted  \n"
        "2. Evidence is retrieved (fact mode)  \n"
        "3. NLI alignment per chunk  \n"
        "4. Deterministic aggregation  \n"
        "5. Numeric metrics"
    )

# ── Inputs ────────────────────────────────────────────────────────────────────

if mode == "Fact Verification":
    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader("Document to verify")
        document = st.text_area(
            "Paste the text you want to fact-check",
            height=260,
            placeholder="e.g. Transformers outperform RNNs in many NLP tasks. They do not use recurrence...",
            label_visibility="collapsed",
        )
        uploaded = st.file_uploader("Or upload a .txt file", type=["txt"])
        if uploaded:
            document = uploaded.read().decode("utf-8")
            st.info(f"Loaded {len(document):,} characters from {uploaded.name}")

    with col2:
        st.subheader("Reference document (optional)")
        reference = st.text_area(
            "Additional evidence source",
            height=260,
            placeholder="Paste a reference document whose content should be used as evidence (optional).",
            label_visibility="collapsed",
        )
        ref_uploaded = st.file_uploader("Or upload reference .txt", type=["txt"], key="ref")
        if ref_uploaded:
            reference = ref_uploaded.read().decode("utf-8")
            st.info(f"Loaded reference: {ref_uploaded.name}")

    run_label = "Verify Facts"

else:  # Guideline Compliance
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Document to check")
        document = st.text_area(
            "Paste the document",
            height=300,
            placeholder="Paste the document you want to check against guidelines...",
            label_visibility="collapsed",
        )
        uploaded = st.file_uploader("Or upload a .txt file", type=["txt"])
        if uploaded:
            document = uploaded.read().decode("utf-8")
            st.info(f"Loaded {len(document):,} characters from {uploaded.name}")

    with col2:
        st.subheader("Guidelines / Rules")
        guidelines = st.text_area(
            "Paste your guidelines",
            height=300,
            placeholder=(
                "e.g.\n"
                "Ensure the document:\n"
                "1. Defines transformers\n"
                "2. Does not mention recurrence\n"
                "3. Includes a performance comparison"
            ),
            label_visibility="collapsed",
        )

    run_label = "Check Compliance"
    reference = None

# ── Run ───────────────────────────────────────────────────────────────────────

run = st.button(run_label, type="primary", use_container_width=True)

if run:
    if not document or not document.strip():
        st.warning("Please enter a document first.")
        st.stop()

    if mode == "Guideline Compliance" and (not guidelines or not guidelines.strip()):
        st.warning("Please enter guidelines first.")
        st.stop()

    st.divider()

    # ── Fact Verification ──────────────────────────────────────────────────────
    if mode == "Fact Verification":
        from fact_checker.pipelines.fact_verification import run_fact_verification

        claim_count_hint = len(document.strip().split("."))
        if claim_count_hint > 10:
            st.info(
                "Large document detected. The free Gemini tier allows ~15 requests/minute — "
                "verification may take a few minutes and will auto-retry on rate limits."
            )

        try:
            with st.spinner("Extracting claims and retrieving evidence…"):
                result = run_fact_verification(
                    document=document.strip(),
                    reference_document=reference.strip() if reference and reference.strip() else None,
                    use_wikipedia=use_wikipedia,
                    use_arxiv=use_arxiv,
                    verbose=False,
                )
        except RuntimeError as e:
            st.error(str(e))
            st.stop()

        if result.warning:
            st.warning(result.warning)
            st.stop()

        m = result.metrics
        st.subheader("Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accuracy", f"{m['accuracy']:.1f}%", help="Supported / Total × 100")
        c2.metric("Coverage", f"{m['coverage']:.1f}%", help="(Supported + Contradicted) / Total × 100")
        c3.metric("Contradiction Rate", f"{m['contradiction_rate']:.1f}%", help="Contradicted / Total × 100")
        c4.metric("Risk Score", f"{m['risk']:.3f}", help="(0.3 × Not Found + 0.7 × Contradicted) / Total")

        st.caption(
            f"**{m['total_claims']}** claims · "
            f"**{m['supported']}** supported · "
            f"**{m['contradicted']}** contradicted · "
            f"**{m['not_found']}** not found"
        )

        st.subheader("Claims")
        for r in result.claim_results:
            label_class = f"label-{r.label.lower().replace('_', '_')}"
            icon = {"SUPPORTED": "✅", "CONTRADICTED": "❌", "NOT_FOUND": "❓"}.get(r.label, "❓")

            with st.expander(f"{icon} {r.claim}"):
                st.markdown(
                    f'<span class="{label_class}">{r.label}</span>',
                    unsafe_allow_html=True,
                )
                if r.reason:
                    st.markdown(f"**Reason:** {r.reason}")
                if r.evidence_used:
                    st.markdown("**Evidence used:**")
                    for ev in r.evidence_used:
                        src = ev.get("source", "")
                        url = ev.get("url")
                        text = ev.get("text", "")
                        header = f"`{src}`" + (f" · [{url}]({url})" if url else "")
                        st.markdown(header)
                        st.caption(text)

    # ── Guideline Compliance ───────────────────────────────────────────────────
    else:
        from fact_checker.pipelines.guideline_compliance import run_guideline_compliance

        try:
            with st.spinner("Parsing guidelines and checking compliance…"):
                result = run_guideline_compliance(
                    document=document.strip(),
                    guidelines=guidelines.strip(),
                    verbose=False,
                )
        except RuntimeError as e:
            st.error(str(e))
            st.stop()

        if result.warning:
            st.warning(result.warning)
            st.stop()

        m = result.metrics
        st.subheader("Metrics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Compliance", f"{m['compliance']:.1f}%", help="Satisfied / Total × 100")
        c2.metric("Violation Rate", f"{m['violation_rate']:.1f}%", help="Violated / Total × 100")
        c3.metric("Missing Rate", f"{m['missing_rate']:.1f}%", help="Missing / Total × 100")

        st.caption(
            f"**{m['total_constraints']}** constraints · "
            f"**{m['satisfied']}** satisfied · "
            f"**{m['violated']}** violated · "
            f"**{m['missing']}** missing"
        )

        st.subheader("Constraints")
        for r in result.constraint_results:
            icon = {"SATISFIED": "✅", "VIOLATED": "❌", "MISSING": "⚠️"}.get(r.label, "❓")
            badge = f"[{r.constraint.type[:3]}]"

            with st.expander(f"{icon} {badge} {r.constraint.text}"):
                label_class = f"label-{r.label.lower()}"
                st.markdown(
                    f'<span class="{label_class}">{r.label}</span>',
                    unsafe_allow_html=True,
                )
                if r.reason:
                    st.markdown(f"**Reason:** {r.reason}")
                if r.matched_chunk:
                    st.markdown("**Matched chunk:**")
                    st.caption(r.matched_chunk)
