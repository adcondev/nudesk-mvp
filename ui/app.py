import streamlit as st
import httpx
import os
import time

st.set_page_config(page_title="FinDocIQ Demo", page_icon="📄", layout="wide")

API_URL = os.getenv("API_URL", "http://gateway:8080")
API_KEY = os.getenv("API_KEY", "changeme")

HEADERS = {"Authorization": f"Bearer {API_KEY}"}

st.title("FinDocIQ RAG Demo")

# Upload Section
st.header("1. Upload Document")
uploaded_file = st.file_uploader("Upload a financial document (PDF)", type=["pdf"])

if uploaded_file is not None:
    if st.button("Upload & Process"):
        with st.spinner("Uploading and processing..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = httpx.post(f"{API_URL}/documents", files=files, headers=HEADERS, timeout=60.0)
            except (httpx.ConnectError, httpx.TimeoutException):
                st.error("Cannot reach the API. Is the stack running? (`docker-compose up`)")
                st.stop()
            except httpx.HTTPError as e:
                st.error(f"Unexpected network error: {e}")
                st.stop()

            if response.status_code == 200:
                data = response.json().get("data", {})
                doc_id = data.get("document_id")
                st.success(f"Uploaded! Document ID: {doc_id}")
                st.session_state["doc_id"] = doc_id

                # Poll for completion
                status_placeholder = st.empty()
                max_retries = 30
                for _ in range(max_retries):
                    try:
                        res = httpx.get(f"{API_URL}/documents/{doc_id}", headers=HEADERS, timeout=10.0)
                    except (httpx.ConnectError, httpx.TimeoutException):
                        st.error("Lost connection to the API while polling. Please refresh.")
                        break
                    if res.status_code == 200:
                        doc_data = res.json().get("data", {})
                        status = doc_data.get("status")
                        status_placeholder.info(f"Status: {status}")
                        if status == "completed":
                            st.success("Extraction and Indexing complete!")

                            # Extraction Display
                            st.subheader("Extraction Results")
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                extracted_data = doc_data.get("extracted_data", {})
                                if extracted_data:
                                    # Create a table of fields, excluding derived_fields
                                    display_fields = {k: v for k, v in extracted_data.items() if k != "derived_fields" and v is not None}
                                    st.table(display_fields)
                                else:
                                    st.info("No structured data extracted.")

                            with col2:
                                derived = extracted_data.get("derived_fields", {})
                                if derived:
                                    st.markdown("### Key Metrics")

                                    # Specific metrics based on available doc types
                                    if "dti" in derived and derived["dti"] is not None:
                                        dti = derived["dti"]
                                        dti_color = "normal"
                                        if dti > 0.43:
                                            dti_color = "inverse" # Red
                                        st.metric(label="Debt-to-Income (DTI)", value=f"{dti*100:.1f}%", delta="High Risk" if dti > 0.43 else "Normal", delta_color=dti_color)

                                    if "ltv" in derived and derived["ltv"] is not None:
                                        ltv = derived["ltv"]
                                        ltv_color = "inverse" if ltv > 0.80 else "normal"
                                        st.metric(label="Loan-to-Value (LTV)", value=f"{ltv*100:.1f}%", delta="High Risk" if ltv > 0.80 else "Normal", delta_color=ltv_color)

                                    if "effective_tax_rate_pct" in derived and derived["effective_tax_rate_pct"] is not None:
                                        st.metric(label="Effective Tax Rate", value=f"{derived['effective_tax_rate_pct']}%")

                                    if "monthly_income_proxy" in derived and derived["monthly_income_proxy"] is not None:
                                        st.metric(label="Est. Monthly Income", value=f"${derived['monthly_income_proxy']:,.2f}")

                                    if "total_deposits_snapshot" in derived and derived["total_deposits_snapshot"] is not None:
                                        st.metric(label="Total Deposits", value=f"${derived['total_deposits_snapshot']:,.2f}")

                                # Red flags panel
                                st.markdown("### Risk Flags")
                                flags = []
                                doc_type = doc_data.get("document_type")
                                if doc_type == "loan_application":
                                    dti = derived.get("dti")
                                    if dti and dti > 0.43:
                                        flags.append("🚨 DTI exceeds 43% standard threshold")
                                    ltv = derived.get("ltv")
                                    if ltv and ltv > 0.80:
                                        flags.append("⚠️ LTV exceeds 80% — PMI likely required")
                                elif doc_type == "pay_stub":
                                    tax_rate = derived.get("effective_tax_rate_pct")
                                    if tax_rate and (tax_rate < 5 or tax_rate > 50):
                                        flags.append("⚠️ Unusual effective tax rate")
                                elif doc_type == "bank_statement":
                                    withdrawals = extracted_data.get("total_withdrawals", 0)
                                    deposits = extracted_data.get("total_deposits", 0)
                                    if withdrawals and deposits and withdrawals > deposits:
                                        flags.append("⚠️ Negative cash flow in period")

                                if flags:
                                    for flag in flags:
                                        st.error(flag)
                                else:
                                    st.success("No immediate red flags detected.")

                            break
                        elif status == "failed":
                            st.error(
                                "Processing failed. The file may be unsupported, corrupted, or contain "
                                "unreadable text. Try uploading a cleaner PDF."
                            )
                            break
                    time.sleep(2)
                else:
                    st.warning(
                        "Processing timed out after 60 seconds. The document may still be processing — "
                        "refresh the page to check its status."
                    )
            else:
                st.error(f"Failed to upload document (HTTP {response.status_code}).")

st.divider()

# RAG Query Section
st.header("2. Ask Questions")

# Shortcut buttons
st.markdown("**Quick Queries:**")
col1, col2, col3 = st.columns(3)

def set_query(q):
    st.session_state["query_input"] = q

with col1:
    st.button("What is the applicant's name and SSN?", on_click=set_query, args=("What is the applicant's name and SSN?",))
with col2:
    st.button("Summarize the income and debt.", on_click=set_query, args=("Summarize the income and debt.",))
with col3:
    st.button("List all the deposits and withdrawals.", on_click=set_query, args=("List all the deposits and withdrawals.",))

query_val = st.session_state.get("query_input", "")
query = st.text_input("Ask a question about the uploaded documents:", value=query_val)

if st.button("Ask"):
    if not query.strip():
        st.info("Enter a question above before clicking Ask.")
    else:
        st.session_state["query_input"] = query
        with st.spinner("Searching and synthesizing answer..."):
            try:
                response = httpx.post(f"{API_URL}/query", json={"query": query}, headers=HEADERS, timeout=60.0)
            except (httpx.ConnectError, httpx.TimeoutException):
                st.error("Cannot reach the API. Is the stack running? (`docker-compose up`)")
                st.stop()
            except httpx.HTTPError as e:
                st.error(f"Unexpected network error: {e}")
                st.stop()

            if response.status_code == 200:
                data = response.json().get("data", {})
                st.markdown("### Answer")
                st.markdown(data.get("answer"))

                with st.expander("View Sources"):
                    for i, source in enumerate(data.get("sources", [])):
                        st.markdown(f"**Source {i+1}** (Chunk {source.get('chunk_index')} from Document {source.get('document_id')})")
                        st.caption(f"Distance: {source.get('distance'):.4f}")
                        st.text(source.get('content'))
                        st.divider()
            else:
                error_body = response.json().get("error", {})
                message = error_body.get("message", "Unknown error") if isinstance(error_body, dict) else str(error_body)
                st.error(f"Query failed: {message}")
