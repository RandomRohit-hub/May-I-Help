import os
import streamlit as st
from pinecone import Pinecone
from groq import Groq
from langchain_core.prompts import ChatPromptTemplate

# Configuration
INDEX_NAME = "mayihelp"
NAMESPACE = "rufus-data"
TOP_K = 5
MAX_CONTEXT_CHARS = 8000
GROQ_MODEL = "llama-3.1-8b-instant"

# Initialize clients
@st.cache_resource
def init_clients():
    # Try to get API keys from Streamlit secrets first, then environment variables
    pinecone_key = st.secrets.get("PINECONE_API_KEY") if hasattr(st, 'secrets') else os.getenv("PINECONE_API_KEY")
    groq_key = st.secrets.get("GROQ_API_KEY") if hasattr(st, 'secrets') else os.getenv("GROQ_API_KEY")
    
    if not pinecone_key:
        raise ValueError("PINECONE_API_KEY not found")
    if not groq_key:
        raise ValueError("GROQ_API_KEY not found")
    
    pc = Pinecone(api_key=pinecone_key)
    index = pc.Index(INDEX_NAME)
    groq_client = Groq(api_key=groq_key)
    return pc, index, groq_client

# RAG Prompt Template
rag_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a website assistant. "
        "Answer ONLY using the provided context retrieved from the vector database. "
        "If the answer is not found in the context, say exactly: "
        "'Not related to project or not asked properly.'"
    ),
    (
        "human",
        "Context:\n{context}\n\nQuestion:\n{question}"
    )
])

def retrieve_context(pc, index, query, top_k=TOP_K):
    """Retrieve relevant context from Pinecone"""
    query_embedding = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=[query],
        parameters={"input_type": "query"}
    )[0]["values"]

    res = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        namespace=NAMESPACE
    )

    return [m["metadata"]["text"] for m in res["matches"]]

def ask_groq(groq_client, context, question):
    """Query Groq LLM with context"""
    messages = rag_prompt.format_messages(
        context=context[:MAX_CONTEXT_CHARS],
        question=question
    )

    groq_messages = []
    for m in messages:
        role = "user" if m.type == "human" else "system"
        groq_messages.append({
            "role": role,
            "content": m.content
        })

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=groq_messages,
        temperature=0
    )

    return response.choices[0].message.content

def ask_website(pc, index, groq_client, question):
    """Main RAG pipeline"""
    retrieved_chunks = retrieve_context(pc, index, question)
    context = "\n\n".join(retrieved_chunks)
    return ask_groq(groq_client, context, question)

# Streamlit UI
def main():
    st.set_page_config(
        page_title="MMTT Website Assistant",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 MMTT Website Assistant")
    st.markdown("Ask questions about the Multi-Mode Tactical Tracker project!")

    # Initialize clients
    try:
        pc, index, groq_client = init_clients()
        
        # Display connection status
        with st.sidebar:
            st.success("✅ Connected to Pinecone")
            st.success("✅ Connected to Groq")
            
            st.markdown("---")
            st.markdown("### About")
            st.info(
                "This assistant uses RAG (Retrieval Augmented Generation) "
                "to answer questions about the MMTT project based on "
                "website content and documentation."
            )
            
            st.markdown("---")
            st.markdown("### Index Stats")
            try:
                stats = index.describe_index_stats()
                st.json({
                    "Total Vectors": stats.get('total_vector_count', 0),
                    "Namespace Vectors": stats.get('namespaces', {}).get(NAMESPACE, {}).get('vector_count', 0)
                })
            except Exception as e:
                st.error(f"Could not fetch stats: {str(e)}")

    except Exception as e:
        st.error(f"❌ Error initializing clients: {str(e)}")
        st.info("Please ensure PINECONE_API_KEY and GROQ_API_KEY are set in your environment variables.")
        return

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about MMTT..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = ask_website(pc, index, groq_client, prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # Clear chat button
    if st.sidebar.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()