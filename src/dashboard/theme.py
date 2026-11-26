"""Design system CSS for Life Time Library – The Daily Edge (Navy, Ivory & Muted Gold)."""

from __future__ import annotations

import streamlit as st


def inject_theme_css() -> None:
    """Inject custom editorial magazine CSS across the Streamlit application."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

        :root {
            --ltl-navy: #0B162C;
            --ltl-navy-soft: #132240;
            --ltl-ivory: #FAF8F3;
            --ltl-card: #FFFFFF;
            --ltl-border: #E8E2D5;
            --ltl-gold: #C59B38;
            --ltl-gold-soft: #FBF6E8;
            --ltl-text: #0F172A;
            --ltl-muted: #526075;
            --ltl-health: #1F7A5C;
            --ltl-health-bg: #F2FAF6;
            --ltl-wealth: #1D4ED8;
            --ltl-wealth-bg: #F3F7FE;
            --ltl-wisdom: #6D28D9;
            --ltl-wisdom-bg: #F7F4FE;
            --ltl-linkedin: #0A66C2;
        }

        /* Main Canvas */
        .stApp {
            background-color: var(--ltl-ivory);
            color: var(--ltl-text);
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        .main .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 1.5rem;
        }

        /* Hide default Streamlit chrome clutter while keeping sidebar toggle */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stAppDeployButton"], [data-testid="stToolbarActions"], .stAppDeployButton, .stDeployButton {display: none !important;}
        header[data-testid="stHeader"] {
            background: rgba(250, 248, 243, 0.85);
            backdrop-filter: blur(6px);
        }

        /* Deep Navy Sidebar */
        section[data-testid="stSidebar"] {
            background-color: var(--ltl-navy);
            border-right: 1px solid #1E2E4D;
        }
        section[data-testid="stSidebar"] * {
            color: #E2E8F0;
        }
        section[data-testid="stSidebar"] .stRadio > div {
            gap: 0.25rem;
        }
        section[data-testid="stSidebar"] .stRadio label {
            border-radius: 10px;
            padding: 0.42rem 0.7rem;
            transition: background-color 0.15s ease;
        }
        section[data-testid="stSidebar"] .stRadio label:hover {
            background-color: var(--ltl-navy-soft);
        }

        /* Typography */
        .ltl-serif {
            font-family: 'Playfair Display', Georgia, serif;
            letter-spacing: -0.01em;
        }

        /* Hero Banner */
        .ltl-hero {
            background: linear-gradient(135deg, #0B162C 0%, #142647 100%);
            color: #FAF8F3;
            border-radius: 16px;
            padding: 28px 32px;
            border-bottom: 3px solid var(--ltl-gold);
            box-shadow: 0 10px 28px rgba(11, 22, 44, 0.10);
            margin-bottom: 1.5rem;
        }
        .ltl-hero-eyebrow {
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            color: var(--ltl-gold);
            font-weight: 700;
            margin-bottom: 6px;
        }
        .ltl-hero-title {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2rem;
            font-weight: 700;
            color: #FFFFFF;
            margin: 0 0 6px 0;
            line-height: 1.2;
        }
        .ltl-hero-sub {
            font-size: 0.98rem;
            color: #CBD5E1;
            margin: 0;
            line-height: 1.5;
        }
        .ltl-date-pill {
            display: inline-block;
            margin-top: 14px;
            background: rgba(197, 155, 56, 0.14);
            border: 1px solid rgba(197, 155, 56, 0.45);
            color: #F4DE9D;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 999px;
        }

        /* Editorial Cards */
        .ltl-card {
            background: var(--ltl-card);
            border: 1px solid var(--ltl-border);
            border-radius: 14px;
            padding: 20px 22px;
            box-shadow: 0 4px 16px rgba(11, 22, 44, 0.04);
            height: 100%;
        }
        .ltl-pillar-card {
            height: 270px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin-bottom: 10px;
            overflow: hidden;
        }
        .ltl-recent-card {
            height: 270px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin-bottom: 10px;
            overflow: hidden;
        }
        .ltl-pillar-health { border-top: 4px solid var(--ltl-health); }
        .ltl-pillar-wealth { border-top: 4px solid var(--ltl-wealth); }
        .ltl-pillar-wisdom { border-top: 4px solid var(--ltl-wisdom); }

        .ltl-badge {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 3px 10px;
            border-radius: 999px;
            margin-bottom: 10px;
        }
        .ltl-badge-health { background: var(--ltl-health-bg); color: var(--ltl-health); }
        .ltl-badge-wealth { background: var(--ltl-wealth-bg); color: var(--ltl-wealth); }
        .ltl-badge-wisdom { background: var(--ltl-wisdom-bg); color: var(--ltl-wisdom); }
        .ltl-badge-gold { background: var(--ltl-gold-soft); color: #8A6510; }

        .ltl-card-title {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--ltl-navy);
            margin: 0 0 8px 0;
            line-height: 1.35;
        }
        .ltl-card-text {
            font-size: 0.92rem;
            color: var(--ltl-muted);
            line-height: 1.55;
            margin: 0 0 12px 0;
        }
        .ltl-meta {
            font-size: 0.78rem;
            color: #64748B;
            font-weight: 500;
        }

        /* Featured Spotlight */
        .ltl-spotlight {
            background: linear-gradient(120deg, #FFFFFF 0%, #FBF8EF 100%);
            border: 1px solid #E8DFC5;
            border-left: 5px solid var(--ltl-gold);
            border-radius: 14px;
            padding: 22px 26px;
            box-shadow: 0 6px 20px rgba(11, 22, 44, 0.05);
            margin: 1rem 0 1.4rem 0;
        }

        /* Progress Metric Tiles */
        .ltl-stat {
            background: #FFFFFF;
            border: 1px solid var(--ltl-border);
            border-radius: 12px;
            padding: 16px 18px;
            box-shadow: 0 2px 10px rgba(11, 22, 44, 0.03);
        }
        .ltl-stat-label {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: var(--ltl-muted);
            font-weight: 600;
        }
        .ltl-stat-val {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.7rem;
            font-weight: 700;
            color: var(--ltl-navy);
            margin-top: 4px;
        }

        /* Lesson Reader Blocks */
        .ltl-lesson-shell {
            background: #FFFFFF;
            border: 1px solid var(--ltl-border);
            border-radius: 16px;
            padding: 26px 30px;
            box-shadow: 0 6px 22px rgba(11, 22, 44, 0.04);
            margin-bottom: 1.25rem;
        }
        .ltl-section-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            color: var(--ltl-navy);
            font-weight: 700;
            margin-top: 14px;
            margin-bottom: 4px;
        }
        .ltl-section-body {
            font-size: 0.98rem;
            line-height: 1.72;
            color: #1E293B;
            margin-bottom: 8px;
        }
        .ltl-takeaway-box {
            background: var(--ltl-gold-soft);
            border-left: 4px solid var(--ltl-gold);
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 14px;
            font-weight: 500;
            color: var(--ltl-navy);
        }

        /* Clean Buttons */
        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.86rem;
            border: 1px solid var(--ltl-border);
            transition: all 0.15s ease;
        }
        .stButton > button[kind="primary"] {
            background-color: var(--ltl-navy);
            color: #FFFFFF;
            border-color: var(--ltl-navy);
        }
        .stButton > button[kind="primary"]:hover {
            background-color: var(--ltl-navy-soft);
            border-color: var(--ltl-gold);
        }

        /* Premium Signature Footer */
        .ltl-footer {
            margin-top: 3rem;
            background: linear-gradient(180deg, #0B162C 0%, #071021 100%);
            color: #CBD5E1;
            border-radius: 16px;
            padding: 28px 32px;
            border-top: 2px solid var(--ltl-gold);
            box-shadow: 0 10px 26px rgba(11, 22, 44, 0.12);
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .ltl-footer-brand {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.2rem;
            font-weight: 700;
            color: #FFFFFF;
            letter-spacing: 0.02em;
        }
        .ltl-footer-sub {
            font-size: 0.88rem;
            color: var(--ltl-gold);
            font-weight: 600;
            margin-top: 2px;
        }
        .ltl-footer-creator {
            font-size: 0.9rem;
            color: #E2E8F0;
            margin-top: 8px;
        }
        .ltl-footer-rule {
            width: 84px;
            height: 1px;
            background: rgba(197, 155, 56, 0.45);
            margin: 16px auto;
            border: none;
        }
        .ltl-linkedin-cta {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(10, 102, 194, 0.16);
            border: 1px solid rgba(96, 165, 250, 0.45);
            color: #93C5FD !important;
            text-decoration: none !important;
            padding: 8px 18px;
            border-radius: 999px;
            font-size: 0.88rem;
            font-weight: 600;
            transition: all 0.18s ease;
        }
        .ltl-linkedin-cta:hover {
            background: var(--ltl-linkedin);
            border-color: var(--ltl-linkedin);
            color: #FFFFFF !important;
            transform: translateY(-1px);
        }
        .ltl-footer-copy {
            font-size: 0.78rem;
            color: #94A3B8;
            margin-top: 16px;
        }
        .ltl-footer-closing {
            font-size: 0.8rem;
            color: #CBD5E1;
            font-style: italic;
            margin-top: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
