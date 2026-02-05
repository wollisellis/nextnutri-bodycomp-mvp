from __future__ import annotations

import io
import os

import requests
import streamlit as st

st.set_page_config(page_title="NextNutri BodyComp MVP", layout="centered")

st.title("NextNutri BodyComp MVP")
st.caption("Photo-based body fat % *prototype* for nutrition professionals (high uncertainty).")

st.warning(
    "This tool provides a probabilistic estimate with significant uncertainty. "
    "It is not a medical device and must not be used for diagnosis or treatment decisions."
)

api_url = st.text_input("Backend API URL", value=os.getenv("BODYCOMP_API_URL", "http://localhost:8000"))

image_file = st.file_uploader("Upload a full-body photo (front-facing)", type=["png", "jpg", "jpeg", "webp"])

col1, col2 = st.columns(2)
with col1:
    sex = st.selectbox("Sex", options=["unknown", "female", "male"], index=0)
    age_years = st.number_input("Age (years)", min_value=0, max_value=120, value=30)
with col2:
    height_cm = st.number_input("Height (cm)", min_value=50, max_value=250, value=170)
    weight_kg = st.number_input("Weight (kg)", min_value=10, max_value=300, value=70)

submit = st.button("Estimate")

if submit:
    if not image_file:
        st.error("Please upload an image.")
        st.stop()

    files = {"image": (image_file.name, image_file.getvalue(), image_file.type or "image/jpeg")}
    data = {
        "sex": sex,
        "age_years": age_years,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
    }

    with st.spinner("Estimating (prototype)…"):
        try:
            r = requests.post(f"{api_url.rstrip('/')}/estimate", files=files, data=data, timeout=60)
        except Exception as e:
            st.error(f"Failed to contact backend: {e}")
            st.stop()

    if r.status_code != 200:
        st.error(f"Backend error ({r.status_code}): {r.text}")
        st.stop()

    out = r.json()

    st.subheader("Result")
    st.metric("Estimated body fat %", f"{out['body_fat_percent']:.1f}%")
    st.write(f"Range: **{out['range']['low']:.1f}% – {out['range']['high']:.1f}%**")
    st.write(f"Confidence: **{out['confidence']:.2f}**")

    st.subheader("Notes")
    for n in out.get("notes", []):
        st.write(f"- {n}")

    with st.expander("Features (debug)"):
        st.json(out.get("features", {}))
