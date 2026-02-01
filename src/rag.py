import pinecone
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config import Config


class RAGEngine:
    def __init__(self):
        # --- Validate Config ---
        if not Config.PINECONE_API_KEY:
            raise ValueError("Missing PINECONE_API_KEY")

        # --- Init Pinecone (VECTOR DB ONLY) ---
        pinecone.init(
            api_key=Config.PINECONE_API_KEY,
            environment=Config.PINECONE_ENV
        )

        # --- Ollama LLM ---
        self.llm = ChatOllama(
            model=Config.OLLAMA_MODEL,
            temperature=0.4
        )

        # --- Ollama Embeddings ---
        self.embeddings = OllamaEmbeddings(
            model=Config.OLLAMA_MODEL
        )

        # --- Connect Existing Index ---
        self.vectorstore = LangchainPinecone.from_existing_index(
            index_name=Config.PINECONE_INDEX_NAME,
            embedding=self.embeddings
        )

        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": Config.TOP_K}
        )

        # --- Prompt ---
        self.prompt = ChatPromptTemplate.from_template("""
You are a technical assistant.
Answer ONLY using the context below.
If the answer is not present, say "I don't know".

Context:
{context}

Question:
{question}
""")

        self.parser = StrOutputParser()

    # -----------------------------
    # Main RAG Method
    # -----------------------------
    def generate_response(self, query: str) -> dict:
        try:
            docs = self.retriever.get_relevant_documents(query)

            context = "\n\n".join(d.page_content for d in docs)

            chain = self.prompt | self.llm | self.parser
            response = chain.invoke({
                "context": context,
                "question": query
            })

            sources = []
            for d in docs:
                meta = d.metadata or {}
                if "source" in meta:
                    sources.append({
                        "title": meta.get("title", "Source"),
                        "url": meta.get("source")
                    })

            return {
                "response": response,
                "sources": sources
            }

        except Exception as e:
            return {
                "response": f"Retrieval Error: {e}",
                "sources": []
            }
