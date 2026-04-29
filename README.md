# 🎯 TalentScout Hiring Assistant

An AI-powered screening interview chatbot built with **Streamlit** and **Groq/Llama**. Candidates interact with "Scout", a professional hiring assistant that collects their information, asks tailored technical questions, and saves structured data, all through a polished chat interface.

---

## 📖 Project Overview

**TalentScout** is a fictional tech recruitment agency. This application serves as the agency's first-round screening tool. Instead of scheduling a live call with a recruiter, candidates chat with **Scout**, an AI assistant that:

1. Greets the candidate and explains the process
2. Collects personal & professional details one field at a time
3. Generates 3-5 tailored technical questions **per technology** in the candidate's stack
4. Saves all collected data as a structured JSON file
5. Handles exit keywords, off-topic messages, and edge cases gracefully

The entire interview takes approximately 10–15 minutes and requires no human recruiter involvement.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Stage-based interview flow** | 4 distinct stages: Greeting → Info Collection → Tech Questions → Closing |
| **One-at-a-time data collection** | Never overwhelms the candidate; asks for one field per message |
| **Tailored tech questions** | 3–5 questions per technology, testing real-world practical knowledge |
| **Context retention** | conversation history maintains full conversation history automatically |
| **Exit handling** | Typing "exit", "quit", "bye", "done", etc. triggers a graceful close |
| **Off-topic guardrails** | Scout politely redirects any non-recruitment conversation |
| **Candidate data export** | JSON files saved automatically; TXT summary downloadable via sidebar button |
| **Sentiment indicator** | Keyword-based analysis shows if the candidate seems Confident / Neutral / Nervous |
| **Progress tracker** | Visual progress bar and field-by-field checklist in the sidebar |
| **Professional UI** | Custom-styled dark sidebar, gradient branding, Google Fonts (Inter), chat bubbles |
| **Privacy-conscious** | Scout never echoes back full phone numbers or emails |

---

## 🛠️ Tech Stack Used

| Component | Technology | Purpose |
|---|---|---|
| Frontend / UI | **Streamlit** | Web interface, chat components, session state |
| AI Model | **Llama 3.3 70B (via Groq)** | Conversational AI backbone (free tier) |
| API Client | **groq** Python SDK | Communication with Groq API |
| Environment | **python-dotenv** | Secure API key management via `.env` file |
| Standard Libraries | `json`, `os`, `re`, `datetime`, `pathlib` | Data handling, validation, file I/O |

**No** LangChain, OpenAI, vector databases, or external NLP libraries are used.

---

## 🚀 Installation Instructions

### Prerequisites

- **Python 3.10 or higher** installed
- A **Groq/Llama API key** ([get one free here](https://console.groq.com/keys)) [no credit card required :)]

### Step-by-step Setup

```bash
# 1. Clone or navigate to the project directory
cd TalentScout

# 2. Create a virtual environment (recommended)
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your API key
#    Copy the example env file and add your real key:
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux

#    Then open .env in a text editor and replace the placeholder:
#    GROQ_API_KEY=your_actual_api_key_here
```

> ⚠️ **IMPORTANT**: You must place your **Google API key** in the `.env` file.  
> The line should look like: `GROQ_API_KEY=gsk_...`  
> Get your FREE key at: **https://console.groq.com/keys** (no credit card needed)

### Running the Application

```bash
python -m streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 📘 Usage Guide

1. **Start**: The app loads and Scout greets you automatically
2. **Answer questions**: Scout asks for your info one field at a time:
   - Full Name → Email → Phone → Years of Experience → Desired Position(s) → Location → Tech Stack
3. **Technical questions**: After you list your tech stack, Scout generates 3-5 questions per technology
4. **Answer or skip**: Respond to the technical questions in any order
5. **End the interview**: Scout will close automatically after tech questions, or type `exit`/`done`/`bye` anytime
6. **Export**: Click the "📥 Export Summary" button in the sidebar to download your data
7. **New interview**: Click "🔄 Start New Interview" to reset everything

---

## 🏗️ Architecture & File Structure

```
TalentScout/
├── app.py                  # Streamlit UI: layout, session state, chat loop
├── chatbot.py              # TalentScoutChatbot class: Groq API wrapper
├── prompts.py              # SYSTEM_PROMPT + generate_tech_questions_prompt()
├── data_handler.py         # CandidateDataHandler: extract, save, retrieve
├── utils.py                # Pure helpers: validation, exit detection, sentiment
├── candidates/             # Auto-created; stores candidate JSON files
│   └── .gitkeep
├── docs/                   # Detailed explanation files for every component
├── requirements.txt        # Python dependencies
├── .env.example            # API key template (copy to .env)
├── .gitignore              # Protects .env and candidate data from git
└── README.md               # This file
```

### Data Flow

```
User Input → app.py → chatbot.py → Groq/Llama API → chatbot.py → app.py → Display
                                         ↑
                                   prompts.py (system instruction)
                                   
On Conversation End:
  chatbot history → data_handler.py → candidates/*.json
                                    → summary .txt (via download button)
```

### Module Responsibilities

| Module | Single Responsibility |
|---|---|
| `prompts.py` | Prompt engineering — all instructions to the model live here |
| `chatbot.py` | API communication — manages chat session and history |
| `utils.py` | Pure functions — validation, parsing, sentiment (no side effects) |
| `data_handler.py` | Data I/O — extraction from conversation, JSON persistence |
| `app.py` | UI orchestration — ties everything together in Streamlit |

---

## 🧠 Prompt Design Explanation

### System Prompt Strategy

The system prompt in `prompts.py` uses a **multi-layered instruction architecture**:

1. **Role Definition**: The model is given a specific persona ("Scout") with clear behavioural traits like warm, professional, encouraging. This creates consistency across all responses.

2. **Stage-based Flow Control**: The prompt defines 4 numbered stages (Greeting, Info Collection, Tech Questions, Closing). The model is explicitly told to follow them in order and **never skip ahead**. This replaces traditional state-machine logic with LLM-native instruction following.

3. **One-at-a-time Enforcement**: The prompt repeatedly emphasises asking for ONE field per message. This prevents the model from batching questions (a common failure mode) and ensures clean data extraction on the backend.

4. **Format Specification**: Technical questions use a prescribed format (`--- [Technology Name] ---` / `Q1:` / `Q2:` etc.) so the output is visually consistent and potentially parseable by downstream systems.

5. **Guardrails**: Three layers of protection:
   - Off-topic redirect (with an exact response template)
   - Inappropriate content handling
   - Data privacy (never echo PII)

6. **Sentinel Token**: The `[CONVERSATION_ENDED]` token is an invisible signal. The model appends it to its final message; the app detects it programmatically and triggers data extraction/saving. The user never sees this token.

### Stage-based Conversation Flow

```
STAGE 1: Greeting
    └── Scout introduces itself, explains the process
    └── Asks for Full Name (transitions into Stage 2)

STAGE 2: Information Collection (7 fields, one at a time)
    └── Full Name → Email → Phone → Years of Experience
    └── Desired Position(s) → Current Location → Tech Stack

STAGE 3: Technical Questions
    └── Parses tech stack → generates 3-5 Qs per technology
    └── Presents all questions at once
    └── Receives and acknowledges answers

STAGE 4: Closing
    └── Thanks candidate, mentions 5 business day follow-up
    └── Appends [CONVERSATION_ENDED]
```

### Technical Question Generation

When the candidate provides their tech stack (e.g., "Python, Django, PostgreSQL"):
- The model generates a **separate block** for each technology
- Each block contains 3–5 questions
- Questions progress from easier to harder
- Focus is on practical/real-world knowledge, not trivia
- The `generate_tech_questions_prompt()` function in `prompts.py` is available as a standalone utility but is NOT needed during normal flow — the system instruction already handles this at Stage 3.

---

## 🔍 What's Pre-built vs What Was Custom Built

### Pre-built (from libraries/SDKs)

| Component | Source |
|---|---|
| Chat UI components | Streamlit: `st.chat_message()`, `st.chat_input()` |
| Groq API communication | groq SDK: `model.start_chat()`, `chat.send_message()` |
| Environment variable loading | python-dotenv: `load_dotenv()` |
| Progress bar widget | Streamlit: `st.progress()` |
| Download button | Streamlit: `st.download_button()` |
| Session state management | Streamlit: `st.session_state` |

### Custom Built (designed specifically for this project)

| Component | Description |
|---|---|
| System prompt | 150+ line instruction set governing Scout's behaviour |
| Stage-based conversation flow | 4-stage interview pipeline encoded in the prompt |
| Candidate data extraction | Dual-strategy parser (index-based + regex fallback) |
| Sentiment analysis | Keyword-based polarity classifier (no API call) |
| Custom CSS theme | Dark sidebar, gradient branding, styled chat bubbles |
| Exit detection | Whole-word matching against exit keywords |
| Progress computation | Maps user message count to interview completion % |
| JSON persistence layer | Timestamped file naming, PII-safe storage |

---

## 🔒 Data Privacy & Security Notes

1. **API Key Protection**: The Google API key is stored in a `.env` file which is excluded from version control via `.gitignore`. Never commit your `.env` file.

2. **Candidate PII**: Candidate JSON files in `candidates/` contain personal information (name, email, phone). These files are also gitignored. In a production deployment, this data should be stored in an encrypted database with access controls.

3. **In-chat Privacy**: The system prompt instructs the model to **never echo back** full phone numbers or email addresses. This reduces the risk of PII exposure in chat logs or screen recordings.

4. **Data Minimisation**: Only the information necessary for the screening process is collected. No passwords, SSNs, or financial data are requested.

5. **Local Storage Only**: All data stays on the local machine. No candidate data is sent to external services beyond the Groq API (which processes messages but does not use them for training per Google's API data policy).

6. **Session Isolation**: Each Streamlit session operates independently. One candidate's data is never visible to another.

---

## 🧩 Challenges & Solutions

### Challenge 1: Ensuring the Model Asks One Question at a Time
**Problem**: LLMs naturally tend to batch related questions together.  
**Solution**: The system prompt uses triple reinforcement — stating the rule in the stage description, in a dedicated "RULES" section, and as a general personality guideline. The phrase "Ask for ONE piece of information at a time" appears with emphasis.

### Challenge 2: Reliable Data Extraction from Free-text Conversation
**Problem**: Candidates might provide info out of order, or the model might deviate slightly from the expected flow.  
**Solution**: A dual extraction strategy — primary index-based mapping (user message N = field N) with regex fallback scanning for email and phone patterns across all messages.

### Challenge 3: Detecting Conversation End Programmatically
**Problem**: How does the app know when the model has finished the interview vs just responding to a message?  
**Solution**: A sentinel token `[CONVERSATION_ENDED]` is defined in the system prompt. The model appends it to closing messages. The app detects this token, strips it from display, and triggers data extraction. The user never sees the token.

### Challenge 4: Maintaining Context Over Long Conversations
**Problem**: The interview may span 20+ messages, and the model needs to reference earlier answers.  
**Solution**: the conversation history automatically maintains the full conversation history internally. Each `send_message()` call has access to everything said before. No manual history management needed.

### Challenge 5: Preventing Off-topic Derailment
**Problem**: Candidates might ask unrelated questions, attempt prompt injection, or try to repurpose the assistant.  
**Solution**: Hard guardrails in the system prompt with exact response templates for off-topic input. The model is told its "sole purpose" is screening — leaving no room for creative interpretation.

---

## 🚀 Future Enhancements

1. **Database Backend**: Replace JSON file storage with PostgreSQL or MongoDB for production-scale candidate management.

2. **Authentication**: Add recruiter login to view/search/filter submitted candidates.

3. **Multi-language Support**: Detect the candidate's language and conduct the interview in their preferred language.

4. **Resume Upload**: Allow candidates to upload a PDF resume and have the model extract/cross-reference information.

5. **Scoring System**: Have the model rate technical answers on a 1-5 scale with justification notes for the human recruiter.

6. **Email Notifications**: Automatically send a confirmation email to the candidate after the interview completes.

7. **Analytics Dashboard**: Show interview completion rates, average duration, most common tech stacks, and sentiment trends.

8. **Voice Interface**: Integrate speech-to-text and text-to-speech for a voice-based interview experience.

9. **Customisable Question Banks**: Let recruiters define custom questions or question categories per role.

10. **Rate Limiting**: Add per-session rate limiting to prevent API abuse in a public deployment.

---

## ▶️ HOW TO RUN

Run these exact commands in your terminal to get the app running from scratch:

```bash
# 1. Navigate to the project folder
cd TalentScout

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Set up your API key
copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux

# 5. Open .env and replace the placeholder with your real Google API key:
#    GROQ_API_KEY=gsk_...your-key-here
#    Get a FREE key at: https://console.groq.com/keys

# 6. Launch the application
python -m streamlit run app.py
```

The app opens at **http://localhost:8501** — Scout will greet you automatically and start the screening interview.

---

## 📄 License

This project is for educational and demonstration purposes. Built as a portfolio project to showcase conversational AI application development.

---

*Built with ❤️ using Streamlit and Groq/Llama*
