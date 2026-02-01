import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Pinecone
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENV = os.getenv("PINECONE_ENV", "gcp-starter")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "mmtt-rag")

    # Ollama
    OLLAMA_MODEL = "gemma2:2b"

    # Retrieval
    TOP_K = 3
