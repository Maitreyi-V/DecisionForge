import os
import time

import streamlit as st

from api_client import DecisionForgeAPI, DecisionForgeAPIError
from ui import (
    apply_custom_styles,
    render_brand,
    render_decision_path,
    render_feedback_card,
    render_section_label,
    render_situation_card,
)


API_URL = os.getenv(
    "DECISIONFORGE_API_URL",
    "http://localhost:8001/api",
)
GENERATION_API_KEY = os.getenv(
    "DECISIONFORGE_GENERATION_API_KEY",
    "local-development-key",
)


st.set_page_config(
    page_title="DecisionForge",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styles()


def initialize_state() -> None:
    defaults = {
        "screen": "setup",
        "job_id": None,
        "simulation_id": None,
        "attempt": None,
        "latest_feedback": None,
        "result": None,
        "journey": [],
        "generation_started_at": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "api" not in st.session_state:
        st.session_state.api = DecisionForgeAPI(
            API_URL,
            GENERATION_API_KEY,
        )


def reset_simulation() -> None:
    st.session_state.screen = "setup"
    st.session_state.job_id = None
    st.session_state.simulation_id = None
    st.session_state.attempt = None
    st.session_state.latest_feedback = None
    st.session_state.result = None
    st.session_state.journey = []
    st.session_state.generation_started_at = None


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## DecisionForge")
        st.caption("A private workspace for practising consequential choices.")

        if st.session_state.screen == "playing":
            st.divider()
            st.metric(
                "Decisions made",
                len(st.session_state.journey),
            )

        if st.session_state.screen != "setup":
            st.divider()
            st.caption("SESSION CONTROLS")

            if st.button(
                "↻ Start a new simulation",
                key="sidebar-reset",
            ):
                reset_simulation()
                st.rerun()


def render_setup_screen() -> None:
    _, form_column, _ = st.columns([0.45, 1.6, 0.45])

    with form_column:
        render_section_label("Create your simulation")
        st.markdown(
            "### What decision do you want to rehearse?"
        )
        st.caption(
            "Use a real situation. DecisionForge will create balanced "
            "trade-offs rather than a simple right-or-wrong quiz."
        )

        with st.form("simulation_setup"):
            scenario = st.text_area(
                "Scenario",
                placeholder=(
                    "Example: A production API starts failing during a major "
                    "launch, but rolling back would affect committed customers."
                ),
                height=150,
            )

            role = st.text_input(
                "Your role",
                placeholder="Example: Backend engineer",
            )

            difficulty = st.selectbox(
                "Difficulty",
                options=[
                    "beginner",
                    "intermediate",
                    "advanced",
                ],
                index=1,
                format_func=str.title,
            )

            submitted = st.form_submit_button(
                "Forge simulation",
                type="primary",
            )

        if not submitted:
            return

        try:
            job = st.session_state.api.generate_simulation(
                scenario=scenario,
                role=role,
                difficulty=difficulty,
            )
        except DecisionForgeAPIError as exc:
            st.error(str(exc))
            return

        st.session_state.job_id = job["job_id"]
        st.session_state.generation_started_at = time.time()
        st.session_state.screen = "generating"
        st.rerun()


def render_generation_screen() -> None:
    _, content_column, _ = st.columns([0.55, 1.4, 0.55])

    with content_column:
        render_section_label("Generation in progress")
        st.markdown("## Forging a balanced decision path")
        st.write(
            "We are creating realistic situations, defensible choices, "
            "consequences, and multiple outcomes."
        )

        try:
            job = st.session_state.api.get_job(
                st.session_state.job_id
            )
        except DecisionForgeAPIError as exc:
            st.error(str(exc))
            return

        if job["status"] in {"pending", "in_progress"}:
            progress = 0.18 if job["status"] == "pending" else 0.68
            status_label = job["status"].replace("_", " ").title()
            st.progress(progress, text=status_label)

            started_at = st.session_state.generation_started_at
            if started_at is not None:
                elapsed = int(time.time() - started_at)
                st.caption(f"Elapsed time: {elapsed} seconds")

            time.sleep(1.5)
            st.rerun()

        if job["status"] == "failed":
            st.error(
                job["error_message"]
                or "Simulation generation failed."
            )
            if st.button(
                "Return to setup",
                type="primary",
                key="generation-failed-reset",
            ):
                reset_simulation()
                st.rerun()
            return

        simulation_id = job["simulation_id"]

        if simulation_id is None:
            st.error(
                "The job completed without creating a simulation."
            )
            return

        try:
            attempt = st.session_state.api.start_attempt(
                simulation_id
            )
        except DecisionForgeAPIError as exc:
            st.error(str(exc))
            return

        st.session_state.simulation_id = simulation_id
        st.session_state.attempt = attempt
        st.session_state.latest_feedback = None
        st.session_state.journey = []
        st.session_state.screen = "playing"
        st.rerun()


def render_playing_screen() -> None:
    attempt = st.session_state.attempt

    if attempt is None:
        st.error("No active attempt was found.")
        return

    node = attempt["current_node"]
    main_column, path_column = st.columns(
        [1.65, 0.85],
        gap="large",
    )

    with main_column:
        step_number = len(st.session_state.journey) + 1
        render_section_label(f"Decision {step_number}")

        feedback = st.session_state.latest_feedback
        if feedback is not None:
            render_feedback_card(feedback)

        st.markdown("## Current situation")
        render_situation_card(node["content"])

        if node["is_ending"]:
            st.success(
                "You have reached an outcome. Your decision profile and "
                "complete path analysis are ready."
            )

            if st.button(
                "View final analysis",
                type="primary",
                key="view-result",
            ):
                try:
                    result = st.session_state.api.get_result(
                        attempt["attempt_id"]
                    )
                except DecisionForgeAPIError as exc:
                    st.error(str(exc))
                    return

                st.session_state.result = result
                st.session_state.screen = "result"
                st.rerun()

            return

        st.markdown("### Choose your response")
        st.caption(
            "There may not be a perfect answer. Consider what each option "
            "protects—and what it puts at risk."
        )

        for option in node["options"]:
            selected = st.button(
                option["text"],
                key=f"option-{node['id']}-{option['id']}",
            )

            if not selected:
                continue

            try:
                decision = st.session_state.api.submit_decision(
                    attempt_id=attempt["attempt_id"],
                    option_id=option["id"],
                )
            except DecisionForgeAPIError as exc:
                st.error(str(exc))
                return

            feedback = decision["decision_feedback"]
            st.session_state.latest_feedback = feedback
            st.session_state.journey = [
                *st.session_state.journey,
                feedback,
            ]
            st.session_state.attempt = decision["attempt"]
            st.rerun()

    with path_column:
        render_decision_path(
            journey=st.session_state.journey,
            current_content=node["content"],
        )


def render_result_screen() -> None:
    result = st.session_state.result

    if result is None:
        st.error("No completed result was found.")
        return

    render_section_label("Final analysis")
    st.markdown("## Your decision journey is complete")

    decision_count = len(result["decisions"])
    profile = result["decision_profile"]

    style_column, decisions_column = st.columns(2)
    style_column.metric(
        "Decision style",
        profile["style"],
    )
    decisions_column.metric(
        "Decisions made",
        decision_count,
    )

    st.caption(profile["summary"])
    if profile["top_priorities"]:
        st.markdown(
            "**Priorities expressed:** "
            + " · ".join(profile["top_priorities"])
        )

    main_column, path_column = st.columns(
        [1.65, 0.85],
        gap="large",
    )

    with main_column:
        st.markdown("### Outcome")
        render_situation_card(result["outcome_summary"])

        st.markdown("### Decision analysis")
        for decision in result["decisions"]:
            title = (
                f"{decision['sequence_number']}. "
                f"{decision['option_text']}"
            )

            with st.expander(title):
                priorities = decision.get("priorities", [])
                if priorities:
                    st.caption(
                        "Emphasized: "
                        + " · ".join(
                            priority.replace("_", " ").title()
                            for priority in priorities
                        )
                    )
                st.write(decision["feedback"])

                alternatives = decision.get("alternatives", [])
                if alternatives:
                    st.markdown("#### Paths not taken")

                for alternative in alternatives:
                    with st.container(border=True):
                        st.markdown(f"**{alternative['option_text']}**")
                        alternate_priorities = alternative.get(
                            "priorities",
                            [],
                        )
                        if alternate_priorities:
                            st.caption(
                                "Would emphasize: "
                                + " · ".join(
                                    priority.replace("_", " ").title()
                                    for priority in alternate_priorities
                                )
                            )
                        st.caption("Immediate trade-off")
                        st.write(alternative["immediate_feedback"])
                        st.caption("Next situation")
                        st.write(alternative["next_situation"])

                        possible_outcomes = alternative.get(
                            "possible_outcomes",
                            [],
                        )
                        if possible_outcomes:
                            st.caption("Possible eventual outcomes")
                            for outcome in possible_outcomes:
                                st.markdown(f"- {outcome}")

    with path_column:
        render_decision_path(
            journey=st.session_state.journey,
            current_content="Outcome reached",
        )

    st.divider()
    replay_column, new_column = st.columns(2)

    with replay_column:
        replay = st.button(
            "Replay this simulation",
            key="replay-simulation",
        )

    with new_column:
        create_new = st.button(
            "Create a new simulation",
            key="create-new-simulation",
        )

    if replay:
        try:
            attempt = st.session_state.api.start_attempt(
                st.session_state.simulation_id
            )
        except DecisionForgeAPIError as exc:
            st.error(str(exc))
            return

        st.session_state.attempt = attempt
        st.session_state.latest_feedback = None
        st.session_state.result = None
        st.session_state.journey = []
        st.session_state.screen = "playing"
        st.rerun()

    if create_new:
        reset_simulation()
        st.rerun()


initialize_state()
render_sidebar()
render_brand()

if st.session_state.screen == "setup":
    render_setup_screen()
elif st.session_state.screen == "generating":
    render_generation_screen()
elif st.session_state.screen == "playing":
    render_playing_screen()
elif st.session_state.screen == "result":
    render_result_screen()
