import streamlit as st
from src.rag import RAGEngine
from src.config import Config

st.set_page_config(
    page_title="MMTT Website Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .stMarkdown {
        font-family: 'Inter', sans-serif;
    }
    h1 {
        color: #0E1117;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_engine():
    try:
        return RAGEngine()
    except Exception as e:
        st.error(f"Failed to initialize RAG Engine: {e}")
        return None

def main():
    st.title("🤖 MMTT Website Assistant")
    st.markdown("Ask questions about the **Multi-Mode Tactical Tracker** project based on the website documentation.")

    # Sidebar configuration
    with st.sidebar:
        st.header("Status")
        if Config.PINECONE_API_KEY:
            st.success("API Keys detected")
        else:
            st.error("Missing API Keys in .env")
            st.info("Plese ensure .env file exists with PINECONE_API_KEY")

        st.markdown("---")
        st.markdown("### About")
        st.info(
            "This assistant extracts knowledge from the PlayMetrics website "
            "and uses a Vector Database (Pinecone) + Local LLM (Ollama/Gemma2:2b) to answer your questions."
        )
        if st.button("Clear History"):
            st.session_state.messages = []
            st.rerun()

    # Initialize RAG Engine
    engine = get_engine()
    if not engine:
        st.stop()

    # Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("View Sources"):
                    for src in message["sources"]:
                        st.markdown(f"- [{src['title']}]({src['url']})")

    # Chat Input
    if prompt := st.chat_input("What is MMTT?"):
        # User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing knowledge base..."):
                result = engine.generate_response(prompt)
                response = result["response"]
                sources = result["sources"]

                st.markdown(response)
                
                if sources:
                    with st.expander("View Sources"):
                        for src in sources:
                            st.markdown(f"- [{src['title']}]({src['url']})")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "sources": sources
                })

if __name__ == "__main__":
    main()