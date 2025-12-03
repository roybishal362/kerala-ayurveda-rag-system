"""RAG Q&A Chain using LangChain LCEL"""
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from src.config import config
from src.models.schemas import QueryResponse, Citation
from src.rag.retriever import get_retriever
from src.rag.citation_tracker import CitationTracker


# Kerala Ayurveda Q&A Prompt Template
QA_PROMPT_TEMPLATE = """You are a knowledgeable assistant for Kerala Ayurveda, helping answer questions about Ayurveda, products, and treatments.

**Brand Voice Guidelines:**
- Be warm, reassuring, and grounded (like a calm practitioner)
- Use precise, clear language - avoid vague mystical claims
- Honor Ayurvedic tradition while respecting modern safety
- Use phrases like "traditionally used to support", "may help maintain"
- NEVER claim to cure, treat, or diagnose diseases
- Always encourage consulting healthcare providers for medical conditions

**Safety Boundaries:**
- No specific dosing instructions
- No suggesting stopping/changing prescribed medications
- Always add safety notes for herbs and therapies

**Your Task:**
Answer the user's question using ONLY the provided context below. Do not add information from outside sources.

**Context:**
{context}

**Question:** {question}

**Instructions:**
1. Answer based ONLY on the provided context
2. If the context doesn't contain enough information, say so honestly
3. Reference sources using [SOURCE_X] markers when making claims
4. Maintain Kerala Ayurveda's warm, grounded tone
5. Include appropriate safety disclaimers when relevant
6. Keep answers concise but complete (2-4 paragraphs)

**Answer:**"""


class QAChain:
    """Question-Answering chain using RAG"""
    
    def __init__(self):
        """Initialize QA chain with LangChain LCEL"""
        # Initialize LLM
        self.llm = ChatGroq(
            temperature=config.TEMPERATURE,
            model_name=config.GROQ_MODEL,
            groq_api_key=config.GROQ_API_KEY,
            max_tokens=config.MAX_TOKENS
        )
        
        # Initialize retriever
        self.retriever = get_retriever()
        
        # Citation tracker
        self.citation_tracker = CitationTracker()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_template(QA_PROMPT_TEMPLATE)
        
        # Build LCEL chain
        self.chain = (
            {"context": lambda x: x["context"], "question": lambda x: x["question"]}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        print("✓ QA Chain initialized with LCEL")
    
    def answer_query(self, question: str) -> QueryResponse:
        """Answer a user query with citations
        
        Args:
            question: User's question
            
        Returns:
            QueryResponse with answer and citations
        """
        # Step 1: Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(question)
        
        # Step 2: Prepare context with citation markers
        context, available_citations = self.citation_tracker.prepare_context_with_markers(retrieved_docs)
        
        # Step 3: Generate answer using chain
        answer = self.chain.invoke({
            "context": context,
            "question": question
        })
        
        # Step 4: Extract used citations
        used_citations = self.citation_tracker.extract_citations_from_answer(answer, available_citations)
        
        # Step 5: Build response
        response = QueryResponse(
            answer=answer,
            citations=used_citations,
            retrieved_chunks=len(retrieved_docs)
        )
        
        return response


# Global chain instance
_qa_chain_instance = None

def get_qa_chain() -> QAChain:
    """Get or create global QA chain instance
    
    Returns:
        Initialized QAChain
    """
    global _qa_chain_instance
    
    if _qa_chain_instance is None:
        print("Initializing QA Chain...")
        _qa_chain_instance = QAChain()
    
    return _qa_chain_instance


# Convenience function matching assignment requirements
def answer_user_query(query: str) -> Dict[str, Any]:
    """Answer user query (matches assignment function signature)
    
    Args:
        query: User's question string
        
    Returns:
        Dictionary with answer and citations
    """
    chain = get_qa_chain()
    response = chain.answer_query(query)
    
    return {
        "answer": response.answer,
        "citations": [
            {
                "doc_id": cit.doc_id,
                "section_id": cit.section_id,
                "excerpt": cit.excerpt
            }
            for cit in response.citations
        ]
    }
