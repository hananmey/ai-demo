import os

import httpx
import streamlit as st

API_SERVICE_URL = os.environ.get(
    "API_SERVICE_URL",
    "http://api-service.ai-demo.svc.cluster.local:8000",
)

st.set_page_config(page_title="NYC Taxi Q&A")
st.title("Ask about NYC taxi trips")

question = st.text_input("Question", placeholder="e.g. What was the average fare in January 2016?")

if st.button("Ask") and question:
    with st.spinner("Thinking..."):
        try:
            resp = httpx.post(f"{API_SERVICE_URL}/chat", json={"question": question}, timeout=60.0)
            resp.raise_for_status()
            answer = resp.json()["answer"]
        except httpx.HTTPError as exc:
            answer = f"Error calling api-service: {exc}"
    st.text_area("Answer", value=answer, height=200)
