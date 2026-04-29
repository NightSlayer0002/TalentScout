"""
app.py — Main Streamlit application for TalentScout Hiring Assistant.

Run with:  python -m streamlit run app.py

Handles UI rendering, session state, chat logic, sidebar widgets,
and automatic candidate data extraction on conversation end.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load .env before any module reads GROQ_API_KEY
load_dotenv()

from chatbot import TalentScoutChatbot
from data_handler import CandidateDataHandler, generate_candidate_summary_text
from utils import is_exit_keyword, analyze_sentiment


# ── Page config ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title="TalentScout Hiring Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Custom CSS ───────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1b2d 0%, #1a2940 100%);
    color: #e0e7ef;
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #60a5fa;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] .stMarkdown span {
    color: #cbd5e1;
}

/* Chat bubbles */
.stChatMessage[data-testid="stChatMessage"] {
    border-radius: 12px;
    margin-bottom: 8px;
    padding: 12px 16px;
}
.stChatInput textarea { border-radius: 12px !important; }

/* Branding header */
.brand-header {
    text-align: center;
    padding: 24px 12px 16px 12px;
    margin-bottom: 16px;
    border-bottom: 1px solid rgba(96, 165, 250, 0.2);
}
.brand-header h1 { font-size: 1.6rem; font-weight: 700; color: #60a5fa; margin: 0; letter-spacing: -0.5px; }
.brand-header p  { font-size: 0.85rem; color: #94a3b8; margin: 4px 0 0 0; }

/* Info card */
.info-card {
    background: rgba(96, 165, 250, 0.08);
    border: 1px solid rgba(96, 165, 250, 0.15);
    border-radius: 10px;
    padding: 14px;
    margin: 10px 0;
}

/* Stage tracker */
.stage-item { padding: 4px 0; font-size: 0.88rem; }
.stage-done    { color: #4ade80; }
.stage-pending { color: #64748b; }
.stage-current { color: #60a5fa; font-weight: 600; }

/* Sentiment badges */
.sentiment-badge {
    display: inline-block; padding: 6px 14px; border-radius: 20px;
    font-size: 0.9rem; font-weight: 500; margin-top: 4px;
}
.sentiment-positive { background: rgba(74, 222, 128, 0.15); color: #4ade80; }
.sentiment-neutral  { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }
.sentiment-negative { background: rgba(251, 113, 133, 0.15); color: #fb7185; }

/* Summary card */
.summary-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #0f1b2d 100%);
    border: 1px solid rgba(96, 165, 250, 0.25);
    border-radius: 14px; padding: 24px; margin: 16px 0; color: #e0e7ef;
}
.summary-card h3 { color: #60a5fa; margin-top: 0; }
.summary-card .field-label {
    color: #94a3b8; font-size: 0.82rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.summary-card .field-value { color: #e0e7ef; font-size: 1rem; margin-bottom: 12px; }

/* Main title */
.main-title { text-align: center; padding: 16px 0 4px 0; }
.main-title h1 {
    font-size: 2rem; font-weight: 700;
    background: linear-gradient(90deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;
}
.main-title p { color: #94a3b8; font-size: 1rem; margin: 4px 0 0 0; }
</style>
""", unsafe_allow_html=True)


# ── Session state initialisation ─────────────────────────────────────────

def init_session_state() -> None:
    """Set up all session state variables on first load or after reset."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "chatbot" not in st.session_state:
        try:
            st.session_state.chatbot = TalentScoutChatbot()
        except ValueError as e:
            st.error(str(e))
            st.stop()

    if "conversation_ended" not in st.session_state:
        st.session_state.conversation_ended = False

    if "candidate_data_saved" not in st.session_state:
        st.session_state.candidate_data_saved = False

    if "candidate_data" not in st.session_state:
        st.session_state.candidate_data = {}

    # Send an initial greeting trigger (only on first load)
    if "greeting_sent" not in st.session_state:
        st.session_state.greeting_sent = True
        initial_response = st.session_state.chatbot.chat(
            "Hello, I'd like to apply for a position at TalentScout."
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": initial_response,
        })


init_session_state()


# ── Progress tracking ────────────────────────────────────────────────────

INTERVIEW_FIELDS: list[tuple[str, str]] = [
    ("full_name",           "Full Name"),
    ("email",               "Email Address"),
    ("phone",               "Phone Number"),
    ("years_of_experience", "Years of Experience"),
    ("desired_positions",   "Desired Position(s)"),
    ("current_location",    "Current Location"),
    ("tech_stack",          "Tech Stack"),
]


def compute_progress() -> tuple[int, int]:
    """Map user message count to number of fields collected."""
    user_msg_count = sum(
        1 for msg in st.session_state.chatbot.get_history()
        if msg["role"] == "user"
    ) - 1  # Subtract the hidden greeting trigger

    fields_collected = max(0, min(user_msg_count, len(INTERVIEW_FIELDS)))
    return fields_collected, len(INTERVIEW_FIELDS)


# ── Sidebar ──────────────────────────────────────────────────────────────

with st.sidebar:
    # Branding
    st.markdown("""
    <div class="brand-header">
        <h1>🎯 TalentScout</h1>
        <p>AI Hiring Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    # Instructions
    st.markdown("""
    <div class="info-card">
        <strong>📋 How it works</strong><br>
        <span style="font-size: 0.84rem;">
        1. Scout will ask for your basic info<br>
        2. Then tailored technical questions<br>
        3. Your data is saved securely<br>
        4. Type <b>exit</b> or <b>done</b> anytime to end
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Progress bar
    st.markdown("### 📊 Interview Progress")
    fields_done, total_fields = compute_progress()

    if st.session_state.conversation_ended:
        progress_pct = 1.0
    elif fields_done >= total_fields:
        progress_pct = 0.85 + (0.15 if st.session_state.conversation_ended else 0.05)
    else:
        progress_pct = fields_done / total_fields * 0.85

    st.progress(min(progress_pct, 1.0))
    if st.session_state.conversation_ended:
        st.caption("✅ Interview complete!")
    else:
        st.caption(f"{fields_done}/{total_fields} fields collected")

    # Stage tracker
    st.markdown("### 📝 Information Collected")
    for idx, (field_key, field_label) in enumerate(INTERVIEW_FIELDS):
        if idx < fields_done:
            st.markdown(
                f'<div class="stage-item stage-done">✅ {field_label}</div>',
                unsafe_allow_html=True,
            )
        elif idx == fields_done and not st.session_state.conversation_ended:
            st.markdown(
                f'<div class="stage-item stage-current">➡️ {field_label}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="stage-item stage-pending">⬜ {field_label}</div>',
                unsafe_allow_html=True,
            )

    # Sentiment indicator
    st.markdown("### 🧠 Candidate Sentiment")

    recent_user_msgs = [
        msg["content"]
        for msg in st.session_state.messages
        if msg["role"] == "user"
    ][-3:]

    if recent_user_msgs:
        emoji, label = analyze_sentiment(recent_user_msgs)
        css_class = {
            "Confident": "sentiment-positive",
            "Neutral": "sentiment-neutral",
            "Nervous": "sentiment-negative",
        }.get(label, "sentiment-neutral")

        st.markdown(
            f'<div class="sentiment-badge {css_class}">{emoji} {label}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="sentiment-badge sentiment-neutral">⏳ Waiting for responses...</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Export button (visible after conversation ends)
    if st.session_state.conversation_ended and st.session_state.candidate_data:
        summary_text = generate_candidate_summary_text(
            st.session_state.candidate_data
        )
        st.download_button(
            label="📥 Export Summary (.txt)",
            data=summary_text,
            file_name=f"talentscout_summary_{st.session_state.candidate_data.get('full_name', 'candidate').replace(' ', '_').lower()}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # Reset button
    if st.button("🔄 Start New Interview", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ── Main chat area ───────────────────────────────────────────────────────

st.markdown("""
<div class="main-title">
    <h1>🎯 TalentScout Hiring Assistant</h1>
    <p>Your AI-powered screening interview — professional, fast, and friendly</p>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
        display_text = msg["content"].replace("[CONVERSATION_ENDED]", "").strip()
        st.markdown(display_text)

# Summary card after conversation ends
if st.session_state.conversation_ended and st.session_state.candidate_data:
    data = st.session_state.candidate_data
    st.markdown(f"""
    <div class="summary-card">
        <h3>📋 Candidate Summary</h3>
        <div class="field-label">Full Name</div>
        <div class="field-value">{data.get('full_name', 'N/A')}</div>
        <div class="field-label">Email</div>
        <div class="field-value">{data.get('email', 'N/A')}</div>
        <div class="field-label">Phone</div>
        <div class="field-value">{data.get('phone', 'N/A')}</div>
        <div class="field-label">Years of Experience</div>
        <div class="field-value">{data.get('years_of_experience', 'N/A')}</div>
        <div class="field-label">Desired Position(s)</div>
        <div class="field-value">{data.get('desired_positions', 'N/A')}</div>
        <div class="field-label">Current Location</div>
        <div class="field-value">{data.get('current_location', 'N/A')}</div>
        <div class="field-label">Tech Stack</div>
        <div class="field-value">{data.get('tech_stack', 'N/A')}</div>
    </div>
    """, unsafe_allow_html=True)

# Chat input
if not st.session_state.conversation_ended:
    user_input = st.chat_input("Type your message here...")

    if user_input:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # Get model response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Scout is thinking..."):
                try:
                    response = st.session_state.chatbot.chat(user_input)
                except Exception as e:
                    response = (
                        "I'm sorry, I encountered a technical issue. "
                        "Please try again in a moment. "
                        f"(Error: {type(e).__name__})"
                    )

            display_response = response.replace("[CONVERSATION_ENDED]", "").strip()
            st.markdown(display_response)

        st.session_state.messages.append({"role": "assistant", "content": response})

        # Check for conversation end
        conversation_should_end = (
            "[CONVERSATION_ENDED]" in response
            or is_exit_keyword(user_input)
        )

        if conversation_should_end and not st.session_state.conversation_ended:
            st.session_state.conversation_ended = True

            handler = CandidateDataHandler()
            candidate_data = handler.extract_candidate_info(
                st.session_state.chatbot.get_history()
            )
            st.session_state.candidate_data = candidate_data

            if not st.session_state.candidate_data_saved:
                handler.save_candidate(candidate_data)
                st.session_state.candidate_data_saved = True
                st.toast("✅ Candidate data saved!", icon="💾")

            st.rerun()

else:
    st.info(
        "✅ This interview session has ended. "
        "Click **🔄 Start New Interview** in the sidebar to begin a new screening."
    )
