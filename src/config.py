import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

    # Pinecone
    INDEX_NAME = "mayihelp"
    NAMESPACE = "rufus-data"
    
    # LLM
    OLLAMA_MODEL = "gemma2:2b"
    EMBEDDING_MODEL = "llama-text-embed-v2"
    
    # Text Processing
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 100
    MAX_CONTEXT_CHARS = 8000
    TOP_K = 5
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    
    @classmethod
    def validate(cls):
        if not cls.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY not found in environment variables.")
