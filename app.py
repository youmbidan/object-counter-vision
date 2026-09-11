import tempfile
import os
import cv2
import streamlit as st

from src.detector import process_video, get_preview_frame
from src.config import LINE_Y_RATIO

st.set_page_config(page_title="Vehicle Counter", layout="wide")

ACCENT = "#e8a33d"
BG = "#111213"
PANEL = "#1a1b1d"
BORDER = "#2c2d30"
TEXT = "#e8e8ea"
MUTED = "#8a8b8e"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');

    .stApp {{ background-color: {BG}; font-family: 'Inter', sans-serif; color: {TEXT}; }}

    .block-container {{ max-width: 1200px; padding-top: 1.5rem; }}

    header[data-testid="stHeader"] {{ background-color: {BG} !important; }}

    .header {{
        padding: 1.5rem 0 1.6rem 0; margin-bottom: 1.6rem;
        text-align: center;
        position: relative;
    }}
    .header::after {{
        content: "";
        display: block;
        position: absolute;
        bottom: 0; left: 50%;
        transform: translateX(-50%);
        width: 220px; height: 1px;
        background: linear-gradient(90deg, transparent, {BORDER} 20%, {BORDER} 80%, transparent);
    }}
    .header h1 {{
        font-family: 'Space Grotesk', sans-serif; font-size: 2.2rem; font-weight: 700;
        color: #ffffff; margin: 0; letter-spacing: -0.01em;
    }}
    .header p {{ color: {MUTED}; font-size: 0.94rem; margin-top: 0.5rem; }}

    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(12px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    .steps-row {{ display: flex; gap: 1px; background: {BORDER}; border: 1px solid {BORDER}; margin-bottom: 1.6rem; }}
    .step {{
        flex: 1; background: {PANEL}; padding: 1.1rem 1.3rem; position: relative;
        animation: fadeInUp 0.5s ease backwards;
        transition: background-color 0.25s ease, transform 0.25s ease;
    }}
    .step:nth-child(1) {{ animation-delay: 0.05s; }}
    .step:nth-child(2) {{ animation-delay: 0.18s; }}
    .step:nth-child(3) {{ animation-delay: 0.31s; }}
    .step:hover {{
        background-color: #221a12;
        transform: translateY(-3px);
    }}
    .step-num {{
        font-family: 'Space Grotesk', sans-serif; font-size: 0.78rem; font-weight: 700;
        color: {BG}; background-color: {ACCENT}; border-radius: 50%;
        width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;
        margin-bottom: 0.6rem;
    }}
    .step-title {{ font-weight: 700; font-size: 0.9rem; color: {ACCENT}; margin-bottom: 0.25rem; }}
    .step-desc {{ font-size: 0.8rem; color: {MUTED}; line-height: 1.4; }}

    .empty-preview {{
        border: 2px dashed {BORDER};
        border-radius: 8px;
        height: 260px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: {MUTED};
        font-size: 0.85rem;
        background: {PANEL};
        margin-top: 0.5rem;
    }}
    .empty-preview .icon {{ font-size: 1.8rem; margin-bottom: 0.5rem; opacity: 0.5; }}

    .section-label {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.07em; color: {ACCENT}; margin: 0 0 0.5rem 0;
    }}

    .hud-readout {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem; color: {MUTED};
        display: flex; gap: 1rem;
        margin-bottom: 0.4rem;
    }}
    .hud-readout span b {{ color: {ACCENT}; font-weight: 600; }}

    [data-testid="stVideo"], [data-testid="stImage"] {{
        border: 2px solid {BORDER};
        border-radius: 8px;
        padding: 5px;
        background: #000000;
        height: 280px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    [data-testid="stVideo"]:hover, [data-testid="stImage"]:hover {{
        border-color: {ACCENT};
        box-shadow: 0 0 0 3px rgba(232, 163, 61, 0.15);
    }}
    [data-testid="stVideo"] video, [data-testid="stImage"] img {{
        max-width: 100% !important;
        max-height: 100% !important;
        width: auto !important;
        height: auto !important;
        object-fit: contain !important;
        border-radius: 4px;
        margin: 0 auto;
    }}

    [data-testid="stFileUploaderDropzone"] {{
        background: {PANEL} !important;
        border: 1px dashed {BORDER} !important;
        border-radius: 8px !important;
        transition: border-color 0.2s ease, background-color 0.2s ease;
    }}
    [data-testid="stFileUploaderDropzone"]:hover {{
        border-color: {ACCENT} !important;
        background-color: #221a12 !important;
    }}
    [data-testid="stFileUploaderDropzone"] button {{
        background-color: {BG} !important;
        color: {ACCENT} !important;
        border: 1px solid {ACCENT} !important;
        border-radius: 6px !important;
        transition: background-color 0.2s ease, color 0.2s ease, transform 0.15s ease;
    }}
    [data-testid="stFileUploaderDropzone"] button:hover {{
        background-color: {ACCENT} !important;
        color: {BG} !important;
        transform: translateY(-1px);
    }}
    [data-testid="stFileUploaderFile"] {{
        background: #232427 !important;
        border: 1px solid {BORDER} !important;
        border-radius: 6px !important;
    }}
    [data-testid="stFileUploaderFileName"] {{ color: {TEXT} !important; }}

    div[data-testid="stWidgetLabel"] label {{
        color: {ACCENT} !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.72rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}

    .stat-grid {{ display: flex; gap: 1px; margin: 0.8rem 0 1rem 0; background: {BORDER}; border: 1px solid {BORDER}; }}
    .stat-box {{ flex: 1; background: {PANEL}; padding: 0.7rem 1rem; }}
    .stat-box .val {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; color: #ffffff; }}
    .stat-box .lbl {{ font-size: 0.65rem; color: {MUTED}; margin-top: 0.1rem; text-transform: uppercase; letter-spacing: 0.04em; }}

    .result-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 0.6rem; }}
    .result-table th {{
        text-align: left; padding: 0.4rem 0.3rem; border-bottom: 1px solid {BORDER};
        color: {ACCENT}; font-weight: 600; font-size: 0.68rem; text-transform: uppercase; font-family: 'JetBrains Mono', monospace;
    }}
    .result-table td {{ padding: 0.4rem 0.3rem; border-bottom: 1px solid #232427; color: {TEXT}; }}

    .stButton button {{
        background-color: {ACCENT} !important; color: {BG} !important; border: none !important;
        border-radius: 6px !important; font-weight: 700 !important; font-size: 0.85rem !important;
        padding: 0.5rem 1.3rem !important;
        transition: background-color 0.2s ease;
    }}
    .stButton button:hover {{ background-color: #f0b757 !important; }}

    [data-testid="stDownloadButton"] button {{
        background-color: {PANEL} !important; color: {TEXT} !important;
        border: 1px solid {BORDER} !important; border-radius: 6px !important;
        font-weight: 600 !important; font-size: 0.82rem !important;
        transition: border-color 0.2s ease;
    }}
    [data-testid="stDownloadButton"] button:hover {{ border-color: {ACCENT} !important; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <h1>Vehicle Counter</h1>
    <p>Détection et suivi de véhicules ,comptage par franchissement de ligne</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="steps-row">
    <div class="step">
        <div class="step-num">1</div>
        <div class="step-title">Charger une vidéo</div>
        <div class="step-desc">Une caméra de circulation, statique de préférence, filmée depuis un point fixe.</div>
    </div>
    <div class="step">
        <div class="step-num">2</div>
        <div class="step-title">Positionner la ligne</div>
        <div class="step-desc">Place la ligne de comptage à l'endroit où les véhicules doivent être comptés.</div>
    </div>
    <div class="step">
        <div class="step-num">3</div>
        <div class="step-title">Lancer l'analyse</div>
        <div class="step-desc">Le modèle détecte, suit, et compte chaque véhicule par catégorie et direction.</div>
    </div>
</div>
""", unsafe_allow_html=True)

if "video_path" not in st.session_state:
    st.session_state.video_path = None

uploaded_file = st.file_uploader("Charger une vidéo", type=["mp4", "avi", "mov"])

if not uploaded_file:
    st.markdown("""
    <div class="empty-preview">
        <div class="icon">▢</div>
        <div>Aucune vidéo chargée pour l'instant</div>
    </div>
    """, unsafe_allow_html=True)

if uploaded_file:
    if st.session_state.video_path is None or st.session_state.get("uploaded_name") != uploaded_file.name:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded_file.read())
            st.session_state.video_path = tmp.name
            st.session_state.uploaded_name = uploaded_file.name
        st.session_state.counts = None
        st.session_state.output_path = None

    cap = cv2.VideoCapture(st.session_state.video_path)
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="section-label">Flux source</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="hud-readout">
            <span>RES <b>{w}×{h}</b></span>
            <span>FPS <b>{fps:.0f}</b></span>
        </div>
        """, unsafe_allow_html=True)
        st.video(st.session_state.video_path)

    with col2:
        st.markdown('<div class="section-label">Ligne de comptage</div>', unsafe_allow_html=True)
        line_position = st.slider("Position", 0.1, 0.9, LINE_Y_RATIO, 0.05, label_visibility="collapsed")
        preview = get_preview_frame(st.session_state.video_path, line_position)
        if preview is not None:
            st.image(preview)

    launch = st.button("Lancer l'analyse")

    if launch:
        output_path = st.session_state.video_path.replace(".mp4", "_output.mp4")
        with st.spinner("Analyse en cours..."):
            counts, _ = process_video(st.session_state.video_path, output_path, line_y_ratio=line_position)
        st.session_state.counts = counts
        st.session_state.output_path = output_path

    if st.session_state.get("counts"):
        counts = st.session_state.counts
        output_path = st.session_state.output_path

        total_down = sum(counts["down"].values())
        total_up = sum(counts["up"].values())
        total = total_down + total_up
        n_categories = len(set(counts["down"]) | set(counts["up"]))

        st.markdown('<div class="section-label">Résultats</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stat-grid">
            <div class="stat-box"><div class="val">{total}</div><div class="lbl">Total</div></div>
            <div class="stat-box"><div class="val">{total_down}</div><div class="lbl">Descendant</div></div>
            <div class="stat-box"><div class="val">{total_up}</div><div class="lbl">Montant</div></div>
            <div class="stat-box"><div class="val">{n_categories}</div><div class="lbl">Catégories</div></div>
        </div>
        """, unsafe_allow_html=True)

        result_col1, result_col2 = st.columns([1, 1], gap="large")

        with result_col1:
            all_categories = sorted(set(counts["down"]) | set(counts["up"]))
            rows = "".join(
                f"<tr><td>{cat}</td><td>{counts['down'].get(cat, 0)}</td><td>{counts['up'].get(cat, 0)}</td></tr>"
                for cat in all_categories
            )
            st.markdown('<div class="section-label">Détail par catégorie</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <table class="result-table">
                <tr><th>Catégorie</th><th>Descendant</th><th>Montant</th></tr>
                {rows}
            </table>
            """, unsafe_allow_html=True)

        with result_col2:
            st.markdown('<div class="section-label">Vidéo annotée</div>', unsafe_allow_html=True)
            if output_path and os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    video_bytes = f.read()
                st.video(video_bytes)
                st.download_button(
                    "Télécharger la vidéo annotée",
                    data=video_bytes,
                    file_name="video_annotee.mp4",
                    mime="video/mp4",
                )
            else:
                st.warning("La vidéo annotée n'est plus disponible — relance l'analyse.")