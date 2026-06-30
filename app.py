import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import io

st.set_page_config(page_title="ATV-QAQC Visual Assessment", layout="centered")

st.title("ATV-QAQC Visual Assessment Tool")
st.write("Upload a core photo to estimate visual geological metrics for Framework 1.")

api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

uploaded_file = st.file_uploader("Upload core photo", type=["jpg", "jpeg", "png"])

prompt = """
You are a geotechnical visual assessment assistant.

Assess ONLY the visible core photograph.

Return ONLY valid JSON with numbers from 0 to 100.

{
  "structural_responses_visible": 0,
  "responses_continuous": 0,
  "veining_coverage": 0,
  "simple_rock_fabric": 0,
  "discontinuities_visible": 0,
  "short_comment": ""
}
"""

def score_positive(p):
    if p >= 90: return 4
    if p >= 70: return 3
    if p >= 50: return 2
    if p >= 30: return 1
    return 0

def score_negative(p):
    if p <= 10: return 4
    if p <= 25: return 3
    if p <= 50: return 2
    if p <= 75: return 1
    return 0

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded core photo", use_container_width=True)

    if st.button("Run Visual Assessment"):
        model = genai.GenerativeModel("gemini-2.0-flash")

        try:
            response = model.generate_content(
                [prompt, image],
                generation_config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json"
                }
            )

            text = response.text.strip()
            data = json.loads(text)

            st.subheader("AI Visual Metrics")
            st.json(data)

            scores = {
                "Structural responses visible": score_positive(data["structural_responses_visible"]),
                "Responses continuous": score_positive(data["responses_continuous"]),
                "Veining coverage": score_negative(data["veining_coverage"]),
                "Simple rock fabric": score_positive(data["simple_rock_fabric"]),
                "Discontinuities visible": score_positive(data["discontinuities_visible"]),
            }

            final_score = sum(scores.values()) / len(scores)

            st.subheader("Framework 1 Scores")
            st.write(scores)
            st.metric("Framework 1 Score", round(final_score, 2))

            if final_score >= 3.25:
                confidence = "High expected confidence"
            elif final_score >= 2.25:
                confidence = "Moderate expected confidence"
            elif final_score >= 1.25:
                confidence = "Low expected confidence"
            else:
                confidence = "Very low expected confidence"

            st.success(confidence)
            st.write("Comment:", data.get("short_comment", ""))

        except Exception as e:
            st.error("Something went wrong.")
            st.write(e)
