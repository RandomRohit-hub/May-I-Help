import os
import streamlit as st
from pinecone import Pinecone
from groq import Groq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

INDEX_NAME = "mayihelp"
NAMESPACE = "rufus-data"
TOP_K = 5
MAX_CONTEXT_CHARS = 8000
GROQ_MODEL = "llama-3.1-8b-instant"


@st.cache_resource
def init_clients():
    """Initialize Pinecone and Groq clients"""
    try:
        # Initialize Pinecone with timeout
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Check if index exists
        available_indexes = pc.list_indexes().names()
        if INDEX_NAME not in available_indexes:
            raise ValueError(f"Index '{INDEX_NAME}' not found. Available indexes: {available_indexes}")
        
        index = pc.Index(INDEX_NAME)
        
        # Initialize Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        
        return pc, index, groq_client
    except Exception as e:
        raise Exception(f"Initialization failed: {str(e)}")


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
    try:
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
    except Exception as e:
        raise Exception(f"Retrieval error: {str(e)}")


def ask_groq(groq_client, context, question):
    """Query Groq LLM with context"""
    try:
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
            temperature=0,
            timeout=30
        )

        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Groq API error: {str(e)}")


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

    # Check if API keys are set
    if not PINECONE_API_KEY or not GROQ_API_KEY:
        st.error("⚠️ API keys not found! Please configure your .env file.")
        st.info("""
        **To fix this:**
        1. Create a `.env` file in the same directory as this script
        2. Add the following lines to the `.env` file:
        ```
        PINECONE_API_KEY=your_actual_pinecone_api_key
        GROQ_API_KEY=your_actual_groq_api_key
        ```
        3. Replace the values with your actual API keys
        4. Save the file and refresh this page
        
        **Note:** Never commit the .env file to version control!
        """)
        return

    # Initialize clients
    try:
        pc, index, groq_client = init_clients()
        
        # Display connection status
        with st.sidebar:
            st.success("✅ Connected to Pinecone")
            st.success("✅ Connected to Groq")
            
            st.markdown("---")
            st.markdown("### Configuration")
            st.code(f"""
Index: {INDEX_NAME}
Namespace: {NAMESPACE}
Model: {GROQ_MODEL}
Top K: {TOP_K}
            """)
            
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
                namespace_stats = stats.get('namespaces', {}).get(NAMESPACE, {})
                st.json({
                    "Total Vectors": stats.get('total_vector_count', 0),
                    "Namespace Vectors": namespace_stats.get('vector_count', 0),
                    "Dimension": stats.get('dimension', 0)
                })
            except Exception as e:
                st.error(f"Could not fetch stats: {str(e)}")

    except Exception as e:
        st.error(f"❌ Error initializing clients: {str(e)}")
        
        with st.expander("Troubleshooting Tips"):
            st.markdown("""
            **Common issues:**
            
            1. **Invalid API Keys**
               - Check that your Pinecone API key starts with `pcsk_` or `pc-`
               - Check that your Groq API key starts with `gsk_`
            
            2. **Network Issues**
               - Check your internet connection
               - Try disabling VPN if using one
               - Check if firewalls are blocking connections
            
            3. **Index Issues**
               - Verify the index name is correct: `mayihelp`
               - Check that the index exists in your Pinecone dashboard
               - Ensure the namespace `rufus-data` has data
            
            4. **Rate Limits**
               - You may have exceeded API rate limits
               - Wait a few minutes and try again
            
            **Need help?**
            - Pinecone Dashboard: https://app.pinecone.io
            - Groq Console: https://console.groq.com
            """)
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
                    error_msg = f"⚠️ Error: {str(e)}"
                    st.error(error_msg)
                    
                    # Show detailed error info
                    with st.expander("Error Details"):
                        st.code(str(e))
                        st.markdown("""
                        **Possible solutions:**
                        - Check your internet connection
                        - Verify API keys are valid
                        - Try asking a simpler question
                        - Wait a moment and try again
                        """)
                    
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # Clear chat button
    if st.sidebar.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()


if __name__ == "__main__":
    main()
