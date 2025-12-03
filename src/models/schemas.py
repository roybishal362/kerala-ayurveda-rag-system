"""Pydantic models for request/response schemas"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# RAG Q&A Schemas
class Citation(BaseModel):
    """Citation information for retrieved content"""
    doc_id: str = Field(description="Document identifier")
    section_id: str = Field(description="Section within document")
    excerpt: str = Field(description="Relevant excerpt from source")


class QueryRequest(BaseModel):
    """Request model for Q&A queries"""
    question: str = Field(description="User's question")


class QueryResponse(BaseModel):
    """Response model for Q&A queries"""
    answer: str = Field(description="Generated answer")
    citations: List[Citation] = Field(description="Source citations")
    retrieved_chunks: int = Field(description="Number of chunks retrieved")


# Agentic Workflow Schemas
class ArticleBrief(BaseModel):
    """Input brief for article generation"""
    brief: str = Field(description="Brief description of article topic")
    target_length: str = Field(default="medium", description="short, medium, or long")
    include_sections: Optional[List[str]] = Field(default=None, description="Sections to include")


class OutlineSection(BaseModel):
    """Section in article outline"""
    heading: str
    key_points: List[str]


class OutlineOutput(BaseModel):
    """Output from outline agent"""
    outline: List[OutlineSection]
    key_topics: List[str]


class WriterOutput(BaseModel):
    """Output from writer agent"""
    draft: str
    claims: List[str]


class FactCheckResult(BaseModel):
    """Result of fact-checking a claim"""
    claim: str
    is_supported: bool
    citation: Optional[Citation]
    explanation: str


class FactCheckerOutput(BaseModel):
    """Output from fact-checker agent"""
    verified_draft: str
    all_citations: List[Citation]
    fact_check_results: List[FactCheckResult]
    flagged_claims: List[str]


class ToneEditorOutput(BaseModel):
    """Output from tone editor agent"""
    final_draft: str
    tone_suggestions: List[str]
    safety_disclaimer_added: bool


class ArticleResponse(BaseModel):
    """Final response for article generation"""
    final_draft: str
    citations: List[Citation]
    workflow_metadata: Dict[str, Any]


# Agent State
class AgentState(BaseModel):
    """State passed between agents in workflow"""
    brief: str
    target_length: str
    include_sections: Optional[List[str]] = None
    outline: Optional[OutlineOutput] = None
    writer_output: Optional[WriterOutput] = None
    fact_checker_output: Optional[FactCheckerOutput] = None
    tone_editor_output: Optional[ToneEditorOutput] = None
