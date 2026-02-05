from __future__ import annotations

import io
import os

import requests
import streamlit as st

st.set_page_config(page_title="NextNutri BodyComp MVP", layout="wide")

# --- Minimal modern styling (Streamlit)
st.markdown(
    """
<style>
.block-container {padding-top: 2rem; padding-bottom: 2rem; max-width: 1100px;}
.small-muted {color: rgba(229,231,235,0.75); font-size: 0.95rem;}
.card {background: rgba(17,26,46,0.85); border: 1px solid rgba(255,255,255,0.06); padding: 1rem 1.1rem; border-radius: 14px;}
.badge {display:inline-block; padding: 0.25rem 0.6rem; border-radius: 999px; font-size: 0.85rem; border: 1px solid rgba(255,255,255,0.12);}
.badge-ok {background: rgba(34,197,94,0.12); border-color: rgba(34,197,94,0.35);}
.badge-bad {background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.35);}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("# NextNutri BodyComp MVP")
st.markdown(
    "<div class='small-muted'>Estimativa por foto para nutris. Protótipo com alta incerteza — use como triagem e feedback de qualidade de foto.</div>",
    unsafe_allow_html=True,
)

with st.expander("⚠️ Aviso / Disclaimer", expanded=False):
    st.warning(
        "Este sistema fornece uma estimativa probabilística com incerteza significativa. "
        "Não é dispositivo médico e não deve ser usado para diagnóstico ou decisões de tratamento."
    )

# Sidebar config
with st.sidebar:
    st.markdown("## Config")
    api_url = st.text_input("Backend API URL", value=os.getenv("BODYCOMP_API_URL", "http://localhost:8000"))
    st.markdown("---")
    st.markdown("## Inputs")
    sex = st.selectbox("Sex", options=["unknown", "female", "male"], index=0)
    age_years = st.number_input("Age (years)", min_value=0, max_value=120, value=30)
    height_cm = st.number_input("Height (cm)", min_value=50, max_value=250, value=170)
    weight_kg = st.number_input("Weight (kg)", min_value=10, max_value=300, value=70)

# Main layout
left, right = st.columns([1.1, 0.9], gap="large")

with left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 1) Foto")
    image_file = st.file_uploader(
        "Envie uma foto de corpo inteiro (frontal)", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed"
    )
    if image_file is not None:
        st.image(image_file.getvalue(), caption=image_file.name, use_container_width=True)
    st.markdown(
        "<div class='small-muted'>Dica: cabeça aos pés, boa luz, celular apoiado/temporizador, fundo simples.</div>",
        unsafe_allow_html=True,
    )
    submit = st.button("Estimar", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 2) Resultado")
    result_slot = st.empty()
    details_slot = st.empty()
    st.markdown("</div>", unsafe_allow_html=True)

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
        # Support structured 422.detail payloads (dict) from the API
        try:
            payload = r.json()
        except Exception:
            payload = {"detail": r.text}

        detail = payload.get("detail")
        if isinstance(detail, dict):
            ok = bool(detail.get("quality_ok", False))
            reason = detail.get("quality_reason", "unknown")
            msg = detail.get("quality_message_ptbr") or str(detail)
            badge = "<span class='badge badge-bad'>REJEITADO</span>" if not ok else "<span class='badge badge-ok'>OK</span>"
            result_slot.markdown(badge + f"  \n**Motivo:** `{reason}`", unsafe_allow_html=True)
            details_slot.error(msg)
        else:
            result_slot.markdown("<span class='badge badge-bad'>ERRO</span>", unsafe_allow_html=True)
            details_slot.error(f"Backend error ({r.status_code}): {detail}")
        st.stop()

    out = r.json()

    # Success
    result_slot.markdown("<span class='badge badge-ok'>OK</span>", unsafe_allow_html=True)
    details_slot.metric("Body fat % (estimado)", f"{out['body_fat_percent']:.1f}%")
    details_slot.write(f"Faixa: **{out['range']['low']:.1f}% – {out['range']['high']:.1f}%**")
    details_slot.write(f"Confiança: **{out['confidence']:.2f}**")

    if out.get("notes"):
        details_slot.markdown("#### Notas")
        for n in out.get("notes", []):
            details_slot.write(f"- {n}")

    with st.expander("Debug (features)"):
        st.json(out.get("features", {}))
