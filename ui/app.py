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
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            response = httpx.post(f"{API_URL}/ingest", files=files, headers=HEADERS, timeout=60.0)

            if response.status_code == 200:
                data = response.json().get("data", {})
                doc_id = data.get("document_id")
                st.success(f"Uploaded! Document ID: {doc_id}")
                st.session_state["doc_id"] = doc_id

                # Poll for completion
                status_placeholder = st.empty()
                max_retries = 30
                for _ in range(max_retries):
                    res = httpx.get(f"{API_URL}/documents/{doc_id}", headers=HEADERS, timeout=60.0)
                    if res.status_code == 200:
                        doc_data = res.json().get("data", {})
                        status = doc_data.get("status")
                        status_placeholder.info(f"Status: {status}")
                        if status == "completed":
                            st.success("Extraction and Indexing complete!")
                            st.json(doc_data)
                            break
                        elif status == "failed":
                            st.error("Processing failed.")
                            break
                    time.sleep(2)
            else:
                st.error("Failed to upload document")

st.divider()

# RAG Query Section
st.header("2. Ask Questions")
query = st.text_input("Ask a question about the uploaded documents:")
if st.button("Ask"):
    if query:
        with st.spinner("Searching and synthesizing answer..."):
            response = httpx.post(f"{API_URL}/query", json={"query": query}, headers=HEADERS, timeout=60.0)
            if response.status_code == 200:
                data = response.json().get("data", {})
                st.markdown("### Answer")
                st.write(data.get("answer"))

                with st.expander("View Sources"):
                    for i, source in enumerate(data.get("sources", [])):
                        st.markdown(f"**Source {i+1}** (Chunk {source.get('chunk_index')} from Document {source.get('document_id')})")
                        st.text(source.get('content'))
                        st.write(f"Distance: {source.get('distance'):.4f}")
            else:
                st.error(f"Failed to query. Status code: {response.status_code}")
