import streamlit as st
import uuid
from flipkart.data_ingestion import DataIngestor
from flipkart.rag_agent import RAGAgentBuilder
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Flipkart Product Assistant",
    page_icon="🛒",
    layout="centered"
)

# ─────────────────────────────────────────────
# Flipkart Theme CSS (Yellow + Blue)
# ─────────────────────────────────────────────
st.markdown("""
    <style>
        /* Background */
        .stApp {
            background-color: #F9F9F9;
        }

        /* Header Banner */
        .flipkart-header {
            background-color: #2874F0;
            padding: 16px 24px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
        }
        .flipkart-header h1 {
            color: white;
            font-size: 26px;
            margin: 0;
            font-weight: 700;
        }
        .flipkart-header span {
            color: #FFD700;
            font-size: 14px;
            font-style: italic;
        }
        .flipkart-logo {
            font-size: 36px;
        }

        /* Chat messages */
        .stChatMessage {
            border-radius: 12px;
            padding: 8px;
        }

        /* User bubble */
        [data-testid="stChatMessageContent"] {
            background-color: #E8F0FE;
            border-left: 4px solid #2874F0;
            border-radius: 8px;
            padding: 10px;
        }

        /* Chat input */
        .stChatInput textarea {
            border: 2px solid #2874F0 !important;
            border-radius: 10px !important;
            background-color: #fff !important;
        }
        .stChatInput button {
            background-color: #FFD700 !important;
            color: #212121 !important;
            border-radius: 8px !important;
            font-weight: bold !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #2874F0 !important;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        [data-testid="stSidebar"] .stButton button {
            background-color: #FFD700 !important;
            color: #212121 !important;
            font-weight: bold !important;
            border-radius: 8px !important;
            width: 100%;
        }

        /* Divider */
        hr {
            border-color: #FFD700 !important;
        }

        /* Spinner */
        .stSpinner > div {
            border-top-color: #2874F0 !important;
        }

        /* Success box */
        .stSuccess {
            background-color: #E8F5E9 !important;
            border-left: 4px solid #FFD700 !important;
        }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Flipkart Header Banner
# ─────────────────────────────────────────────
st.markdown("""
    <div class="flipkart-header">
        <div class="flipkart-logo">🛒</div>
        <div>
            <h1>Flipkart Assistant</h1>
            <span>✦ Explore. Compare. Buy Smart.</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "rag_agent" not in st.session_state:
    with st.spinner("⏳ Loading Flipkart AI Assistant..."):
        vector_store = DataIngestor().ingest(load_existing=True)
        st.session_state.rag_agent = RAGAgentBuilder(vector_store).build_agent()
    st.success("✅ Assistant Ready! Ask me about any Flipkart product.")

# ─────────────────────────────────────────────
# Chat History Display
# ─────────────────────────────────────────────
for message in st.session_state.chat_history:
    avatar = "🧑" if message["role"] == "user" else "🛒"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# ─────────────────────────────────────────────
# Chat Input
# ─────────────────────────────────────────────
user_input = st.chat_input("🔍 Search for a product or ask a question...")

if user_input:
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("assistant", avatar="🛒"):
        with st.spinner("Finding best products for you..."):
            try:
                response = st.session_state.rag_agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": user_input
                            }
                        ]
                    },
                    config={
                        "configurable": {
                            "thread_id": st.session_state.thread_id
                        }
                    }
                )

                if not response.get("messages"):
                    answer = "⚠️ Sorry, I couldn't find relevant product information."
                else:
                    answer = response["messages"][-1].content

            except Exception as e:
                answer = f"❌ Error: {str(e)}"

        st.markdown(answer)

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer
    })

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛒 Flipkart Assistant")
    st.markdown("---")
    st.markdown("### 📋 Session Info")
    st.markdown(f"**🔑 Thread ID:**")
    st.code(st.session_state.thread_id, language=None)
    st.markdown(f"**💬 Messages:** `{len(st.session_state.chat_history)}`")
    st.markdown("---")

    if st.button("🔄 Reset Chat"):
        st.session_state.chat_history = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Try asking:")
    st.markdown("- Best mobile under ₹15,000?")
    st.markdown("- Top rated laptops on Flipkart?")
    st.markdown("- Compare Samsung vs OnePlus?")
    st.markdown("---")
    st.markdown("✅ **Status:** Healthy")
    st.markdown("🔵 Powered by **LangChain + LangGraph**")