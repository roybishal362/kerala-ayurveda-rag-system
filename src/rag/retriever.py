"""Vector store and retrieval system using ChromaDB"""
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from src.config import config
from src.rag.document_loader import load_documents


class KeralaAyurvedaRetriever:
    """Retriever for Kerala Ayurveda content using semantic search"""
    
    def __init__(self, persist_directory: str = None):
        """Initialize retriever with embeddings and vector store
        
        Args:
            persist_directory: Directory to persist ChromaDB
        """
        self.persist_directory = persist_directory or config.CHROMA_PERSIST_DIR
        self.embeddings = None
        self.vectorstore = None
        self.retriever = None
        
        self._setup_embeddings()
    
    def _setup_embeddings(self):
        """Setup HuggingFace embeddings model"""
        print(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},  # Use CPU for compatibility
            encode_kwargs={'normalize_embeddings': True}  # Better similarity
        )
        
        print("✓ Embeddings model loaded")
    
    def initialize_vectorstore(self, documents: List[Document] = None):
        """Initialize or load vector store
        
        Args:
            documents: Documents to index. If None, loads from content pack
        """
        # Load documents if not provided
        if documents is None:
            print("Loading documents from content pack...")
            documents = load_documents()
        
        # Check if vectorstore already exists
        try:
            print(f"Attempting to load existing vector store from {self.persist_directory}")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print("✓ Loaded existing vector store")
        except Exception as e:
            print(f"Creating new vector store (no existing store found)")
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"✓ Created and persisted vector store with {len(documents)} documents")
        
        # Setup retriever
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": config.TOP_K_CHUNKS}
        )
        
        print(f"✓ Retriever configured (top-k={config.TOP_K_CHUNKS})")
    
    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]:
        """Retrieve relevant documents for a query
        
        Args:
            query: User's question
            k: Number of documents to retrieve (overrides config)
            
        Returns:
            List of relevant Document objects with metadata
        """
        if self.retriever is None:
            raise ValueError("Retriever not initialized. Call initialize_vectorstore() first.")
        
        # Override k if provided
        if k is not None:
            search_kwargs = {"k": k}
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs
            )
            return retriever.invoke(query)
        
        return self.retriever.invoke(query)
    
    def retrieve_with_filter(self, query: str, doc_type: str = None, k: Optional[int] = None) -> List[Document]:
        """Retrieve documents with metadata filtering
        
        Args:
            query: User's question
            doc_type: Filter by document type (product, faq, guide, etc.)
            k: Number of documents to retrieve
            
        Returns:
            List of filtered relevant documents
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized.")
        
        # Build filter
        filter_dict = {}
        if doc_type:
            filter_dict["doc_type"] = doc_type
        
        # Retrieve with filter
        k = k or config.TOP_K_CHUNKS
        
        if filter_dict:
            docs = self.vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            docs = self.vectorstore.similarity_search(query, k=k)
        
        return docs


# Global retriever instance
_retriever_instance = None

def get_retriever() -> KeralaAyurvedaRetriever:
    """Get or create global retriever instance
    
    Returns:
        Initialized KeralaAyurvedaRetriever
    """
    global _retriever_instance
    
    if _retriever_instance is None:
        print("Initializing Kerala Ayurveda Retriever...")
        _retriever_instance = KeralaAyurvedaRetriever()
        _retriever_instance.initialize_vectorstore()
    
    return _retriever_instance
