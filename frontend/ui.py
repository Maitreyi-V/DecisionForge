from html import escape
from typing import Any

import streamlit as st


CUSTOM_CSS = """
<style>
    .stApp {
        background:
            radial-gradient(circle at 18% -10%, rgba(124, 58, 237, 0.23), transparent 34%),
            radial-gradient(circle at 88% 12%, rgba(14, 165, 233, 0.13), transparent 28%),
            #070A12;
    }

    [data-testid="stHeader"] {
        background: rgba(7, 10, 18, 0.78);
        backdrop-filter: blur(16px);
    }

    [data-testid="stAppViewContainer"] > .main .block-container {
        max-width: 1180px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }

    [data-testid="stSidebar"] {
        background: rgba(10, 15, 27, 0.96);
        border-right: 1px solid rgba(148, 163, 184, 0.12);
    }

    .df-hero {
        padding: 1.2rem 0 2rem;
    }

    .df-eyebrow {
        color: #A78BFA;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }

    .df-hero h1 {
        margin: 0;
        font-size: clamp(2.5rem, 6vw, 4.6rem);
        line-height: 0.98;
        letter-spacing: -0.055em;
        background: linear-gradient(105deg, #FFFFFF 5%, #C4B5FD 45%, #7DD3FC 95%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .df-hero p {
        max-width: 720px;
        color: #94A3B8;
        font-size: 1.05rem;
        line-height: 1.7;
        margin: 0.9rem 0 0;
    }

    .df-section-label {
        color: #A78BFA;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 0.7rem;
    }

    .df-situation-card,
    .df-feedback-card,
    .df-timeline-card,
    div[data-testid="stForm"] {
        background: linear-gradient(145deg, rgba(17, 24, 39, 0.92), rgba(10, 15, 27, 0.92));
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 20px;
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.24);
    }

    div[data-testid="stForm"] {
        padding: 1.4rem 1.5rem 1.1rem;
    }

    .df-situation-card {
        padding: 1.55rem 1.65rem;
        color: #E2E8F0;
        font-size: 1.08rem;
        line-height: 1.75;
        margin-bottom: 1.35rem;
    }

    .df-feedback-card {
        padding: 1.2rem 1.35rem;
        border-color: rgba(56, 189, 248, 0.28);
        background: linear-gradient(145deg, rgba(14, 116, 144, 0.16), rgba(17, 24, 39, 0.92));
        margin-bottom: 1.25rem;
    }

    .df-feedback-choice {
        color: #7DD3FC;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }

    .df-feedback-copy {
        color: #CBD5E1;
        line-height: 1.65;
    }

    .df-timeline-card {
        padding: 1.25rem 1.2rem;
        position: sticky;
        top: 5.5rem;
    }

    .df-timeline-title {
        color: #F8FAFC;
        font-size: 1rem;
        font-weight: 750;
        margin-bottom: 1.2rem;
    }

    .df-timeline-item {
        display: grid;
        grid-template-columns: 20px 1fr;
        gap: 0.75rem;
        min-height: 68px;
    }

    .df-timeline-rail {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .df-timeline-dot {
        width: 12px;
        height: 12px;
        border-radius: 999px;
        background: #64748B;
        border: 2px solid #1E293B;
        z-index: 1;
    }

    .df-timeline-line {
        width: 2px;
        flex: 1;
        background: rgba(100, 116, 139, 0.35);
    }

    .df-timeline-item.current .df-timeline-dot {
        background: #A78BFA;
        box-shadow: 0 0 0 5px rgba(139, 92, 246, 0.17), 0 0 22px rgba(139, 92, 246, 0.75);
    }

    .df-timeline-step {
        color: #A78BFA;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.09em;
        text-transform: uppercase;
    }

    .df-timeline-copy {
        color: #CBD5E1;
        font-size: 0.88rem;
        line-height: 1.45;
        margin-top: 0.18rem;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        width: 100%;
        min-height: 3.2rem;
        padding: 0.75rem 1rem;
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.96), rgba(17, 24, 39, 0.96));
        color: #F8FAFC;
        text-align: left;
        transition: transform 150ms ease, border-color 150ms ease, box-shadow 150ms ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        transform: translateY(-2px);
        border-color: rgba(167, 139, 250, 0.75);
        box-shadow: 0 10px 30px rgba(76, 29, 149, 0.22);
        color: #FFFFFF;
    }

    .stFormSubmitButton > button[kind="primary"] {
        justify-content: center;
        text-align: center;
        background: linear-gradient(115deg, #7C3AED, #2563EB);
        border-color: transparent;
        font-weight: 750;
    }

    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.72);
        border: 1px solid rgba(148, 163, 184, 0.13);
        border-radius: 16px;
        padding: 1rem 1.1rem;
    }

    div[data-testid="stExpander"] {
        background: rgba(17, 24, 39, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 14px;
        overflow: hidden;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #7C3AED, #38BDF8);
    }

    @media (max-width: 760px) {
        [data-testid="stAppViewContainer"] > .main .block-container {
            padding-top: 1rem;
        }

        .df-hero {
            padding-top: 0.5rem;
        }

        .df-timeline-card {
            position: static;
            margin-top: 1rem;
        }
    }
</style>
"""


def apply_custom_styles() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_brand() -> None:
    st.markdown(
        """
        <div class="df-hero">
            <div class="df-eyebrow">AI decision lab</div>
            <h1>DecisionForge</h1>
            <p>
                Rehearse difficult professional choices, explore their trade-offs,
                and reflect on the path you created.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_label(label: str) -> None:
    st.markdown(
        f'<div class="df-section-label">{escape(label)}</div>',
        unsafe_allow_html=True,
    )


def render_situation_card(content: str) -> None:
    safe_content = escape(content).replace("\n", "<br>")
    st.markdown(
        f'<div class="df-situation-card">{safe_content}</div>',
        unsafe_allow_html=True,
    )


def render_feedback_card(feedback: dict[str, Any]) -> None:
    option_text = escape(str(feedback["option_text"]))
    feedback_text = escape(str(feedback["feedback"])).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="df-feedback-card">
            <div class="df-feedback-choice">You chose: {option_text}</div>
            <div class="df-feedback-copy">{feedback_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_path(
    journey: list[dict[str, Any]],
    current_content: str,
) -> None:
    items = [("Start", "Simulation begins")]
    items.extend(
        (
            f"Decision {index}",
            str(decision["option_text"]),
        )
        for index, decision in enumerate(journey, start=1)
    )
    items.append(("Current", current_content))

    rendered_items: list[str] = []
    last_index = len(items) - 1

    for index, (label, copy) in enumerate(items):
        is_current = index == last_index
        state_class = "current" if is_current else "complete"
        trimmed_copy = copy if len(copy) <= 105 else f"{copy[:102]}..."
        line = "" if is_current else '<div class="df-timeline-line"></div>'

        rendered_items.append(
            f"""
            <div class="df-timeline-item {state_class}">
                <div class="df-timeline-rail">
                    <div class="df-timeline-dot"></div>
                    {line}
                </div>
                <div>
                    <div class="df-timeline-step">{escape(label)}</div>
                    <div class="df-timeline-copy">{escape(trimmed_copy)}</div>
                </div>
            </div>
            """
        )

    st.html(
        '<div class="df-timeline-card">'
        '<div class="df-timeline-title">Your decision path</div>'
        f"{''.join(rendered_items)}"
        "</div>"
    )
