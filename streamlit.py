import streamlit as st
import os
from dotenv import load_dotenv
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Pinecone as LangchainPinecone

from pinecone import Pinecone
import ollama


# ==================================================
# ENV
# ==================================================
load_dotenv()


# ==================================================
# INTERNAL CONFIG (HIDDEN FROM UI)
# ==================================================
DATA_PATH = "data/playmetrics_full_dataset.txt"   # <-- change only here if needed
DEFAULT_NAMESPACE = "mmtt-docs"


# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="MMTT RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# MODERN CSS (CLEAN + READABLE)
# ==================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

#MainMenu, footer, header { visibility: hidden; }

/* Main background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
}

/* Content card */
.block-container {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border-radius: 20px;
    padding: 2.5rem 3rem;
    max-width: 1200px;
    margin: 2rem auto;
    box-shadow: 0 25px 60px rgba(0,0,0,0.4);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #667eea, #764ba2);
}
[data-testid="stSidebar"] * {
    color: white !important;
}

/* Title */
.main-title {
    font-size: 3rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.subtitle {
    text-align: center;
    color: #b8b9c9;
    margin-bottom: 2rem;
}

/* Chat bubbles */
.chat {
    padding: 1.4rem;
    border-radius: 16px;
    margin-bottom: 1.2rem;
    animation: fadeIn 0.25s ease-in;
}
.user {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    margin-left: 20%;
}
.assistant {
    background: #2d2d44;
    color: #e2e8f0;
    margin-right: 20%;
    border-left: 4px solid #667eea;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 14px;
    border: none;
    color: white;
    font-weight: 600;
    padding: 0.8rem 2rem;
}
.stButton > button:hover {
    transform: translateY(-2px);
}

/* Chat input */
.stChatInput > div {
    background: #2d2d44;
    border-radius: 14px;
    border: 2px solid #3a3a52;
}
.stChatInput textarea {
    color: #e2e8f0;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# SESSION STATE
# ==================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "initialized" not in st.session_state:
    st.session_state.initialized = False


# ==================================================
# PINECONE
# ==================================================
@st.cache_resource
def get_pinecone():
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

pc = get_pinecone()
indexes = [i["name"] for i in pc.list_indexes()]


# ==================================================
# SIDEBAR (CLEAN – NO DATA PATH)
# ==================================================
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")

    if not indexes:
        st.error("No Pinecone indexes found")
        st.stop()

    index_name = st.selectbox("🗄️ Pinecone Index", indexes)

    namespace = st.text_input("📦 Namespace", value=DEFAULT_NAMESPACE)

    model_name = st.selectbox(
        "🤖 Model",
        ["gemma2:2b", "llama2", "mistral"]
    )

    st.markdown("---")

    if st.button("🔄 Reset Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ==================================================
# EMBEDDINGS
# ==================================================
@st.cache_resource
def load_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


# ==================================================
# SAFE FILE LOADER (NO LANGCHAIN LOADERS)
# ==================================================
def load_documents():
    path = Path(DATA_PATH)

    if not path.exists():
        st.error(f"Data file not found: {DATA_PATH}")
        return []

    text = path.read_text(encoding="utf-8", errors="ignore")
    docs = [Document(page_content=text)]

    splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    return splitter.split_documents(docs)


# ==================================================
# VECTOR STORE
# ==================================================
def setup_vectorstore(docs, embeddings):
    return LangchainPinecone.from_documents(
        documents=docs,
        embedding=embeddings,
        index_name=index_name,
        namespace=namespace
    )


# ==================================================
# OLLAMA
# ==================================================
def ask_llm(context, question):
    res = ollama.chat(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI assistant for the MMTT project. "
                    "Answer ONLY from the provided context. "
                    "If the answer is missing, say you don't know."
                )
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{question}"
            }
        ]
    )
    return res["message"]["content"]


# ==================================================
# MAIN UI
# ==================================================
st.markdown("<h1 class='main-title'>🤖 MMTT RAG Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Ask intelligent questions about your documentation</p>", unsafe_allow_html=True)


# ==================================================
# INITIALIZE
# ==================================================
if not st.session_state.initialized:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Initialize System", use_container_width=True):
            with st.spinner("Preparing knowledge base..."):
                embeddings = load_embeddings()
                docs = load_documents()

                vectorstore = setup_vectorstore(docs, embeddings)
                st.session_state.retriever = vectorstore.as_retriever(k=3)

                st.session_state.initialized = True
                st.success("System ready!")
                st.rerun()


# ==================================================
# CHAT
# ==================================================
if st.session_state.initialized:
    for msg in st.session_state.messages:
        st.markdown(
            f"<div class='chat {msg['role']}'>"
            f"<strong>{'You' if msg['role']=='user' else 'AI'}:</strong><br>"
            f"{msg['content']}</div>",
            unsafe_allow_html=True
        )

    if prompt := st.chat_input("Ask something about MMTT…"):
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        docs = st.session_state.retriever.invoke(prompt)
        context = "\n\n".join(d.page_content for d in docs)

        answer = ask_llm(context, prompt)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )

        st.rerun()
