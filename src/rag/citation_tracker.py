"""Citation extraction and tracking"""
from typing import List, Tuple
from langchain_core.documents import Document
from src.models.schemas import Citation


class CitationTracker:
    """Track and extract citations from retrieved documents"""
    
    @staticmethod
    def prepare_context_with_markers(documents: List[Document]) -> Tuple[str, List[Citation]]:
        """Prepare context string with source markers for LLM
        
        Args:
            documents: Retrieved documents
            
        Returns:
            Tuple of (context_string, citation_list)
        """
        context_parts = []
        citations = []
        
        for i, doc in enumerate(documents):
            source_id = f"[SOURCE_{i+1}]"
            
            # Create citation object
            citation = Citation(
                doc_id=doc.metadata.get('doc_id', 'unknown'),
                section_id=doc.metadata.get('section_id', 'unknown'),
                excerpt=doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
            )
            citations.append(citation)
            
            # Add to context with marker
            context_parts.append(f"{source_id}\n{doc.page_content}\n")
        
        context_string = "\n---\n".join(context_parts)
        return context_string, citations
    
    @staticmethod
    def extract_citations_from_answer(answer: str, available_citations: List[Citation]) -> List[Citation]:
        """Extract which citations were actually used in the answer
        
        Args:
            answer: Generated answer text
            available_citations: All available citations from retrieval
            
        Returns:
            List of citations that were referenced
        """
        used_citations = []
        
        # Check for source markers in answer
        for i, citation in enumerate(available_citations):
            source_marker = f"[SOURCE_{i+1}]"
            if source_marker in answer or f"Source {i+1}" in answer:
                used_citations.append(citation)
        
        # If no explicit markers found, return all citations (conservative approach)
        if not used_citations:
            return available_citations
        
        return used_citations
    
    @staticmethod
    def format_citations_for_display(citations: List[Citation]) -> str:
        """Format citations for user display
        
        Args:
            citations: List of citations
            
        Returns:
            Formatted citation string
        """
        if not citations:
            return ""
        
        citation_text = "\n\n**Sources:**\n"
        for i, cit in enumerate(citations):
            citation_text += f"{i+1}. {cit.doc_id} - {cit.section_id}\n"
        
        return citation_text
