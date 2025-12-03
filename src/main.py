"""FastAPI application for Kerala Ayurveda RAG and Agentic System"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.models.schemas import QueryRequest, QueryResponse, ArticleBrief, ArticleResponse
from src.rag.qa_chain import get_qa_chain
from src.agents.workflow import get_workflow
from src.config import config

# Initialize FastAPI app
app = FastAPI(
    title="Kerala Ayurveda RAG & Agentic System",
    description="Q&A system and article generation workflow for Kerala Ayurveda content",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint with system information"""
    return {
        "message": "Kerala Ayurveda RAG & Agentic System",
        "version": "1.0.0",
        "endpoints": {
            "qa": "/api/query (POST)",
            "article_generation": "/api/generate-article (POST)",
            "health": "/health (GET)"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "groq_api_configured": bool(config.GROQ_API_KEY),
        "content_pack_path": config.CONTENT_PACK_PATH
    }


@app.post("/api/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    """Q&A endpoint using RAG
    
    Args:
        request: QueryRequest with user question
        
    Returns:
        QueryResponse with answer and citations
    """
    try:
        # Get QA chain
        qa_chain = get_qa_chain()
        
        # Generate answer
        response = qa_chain.answer_query(request.question)
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/api/generate-article", response_model=ArticleResponse)
def generate_article_endpoint(brief: ArticleBrief):
    """Article generation endpoint using agentic workflow
    
    Args:
        brief: ArticleBrief with topic and requirements
        
    Returns:
        ArticleResponse with final draft, citations, and workflow metadata
    """
    try:
        # Get workflow
        workflow = get_workflow()
        
        # Generate article
        response = workflow.generate_article(brief)
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating article: {str(e)}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    print("\n" + "="*60)
    print("Kerala Ayurveda RAG & Agentic System")
    print("="*60)
    
    # Check configuration
    if not config.GROQ_API_KEY:
        print("⚠ WARNING: GROQ_API_KEY not set in environment")
        print("  Please set your Groq API key in .env file")
    else:
        print("✓ Groq API key configured")
    
    print(f"✓ Content pack path: {config.CONTENT_PACK_PATH}")
    print(f"✓ Model: {config.GROQ_MODEL}")
    print(f"✓ Embeddings: {config.EMBEDDING_MODEL}")
    
    # Initialize systems
    try:
        print("\nInitializing RAG system...")
        qa_chain = get_qa_chain()
        print("✓ RAG system ready")
        
        print("\nInitializing agentic workflow...")
        workflow = get_workflow()
        print("✓ Agentic workflow ready")
        
    except Exception as e:
        print(f"⚠ Error during initialization: {e}")
    
    print("\n" + "="*60)
    print("System Ready!")
    print("="*60 + "\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
