"""Configuration management for Kerala Ayurveda RAG System"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Embeddings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Vector Store
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    
    # Content Pack Path
    CONTENT_PACK_PATH = os.getenv("CONTENT_PACK_PATH", "./kerala_ayurveda_content_pack_v1")
    
    # Chunking
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    # Retrieval
    TOP_K_CHUNKS = int(os.getenv("TOP_K_CHUNKS", "4"))
    
    # LLM Parameters
    TEMPERATURE = 0.3
    MAX_TOKENS = 800

config = Config()
