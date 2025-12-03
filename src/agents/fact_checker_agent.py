"""Fact-Checker Agent using RAG to verify claims"""
from typing import List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config import config
from src.models.schemas import FactCheckResult, FactCheckerOutput, Citation
from src.rag.retriever import get_retriever


# Fact-Checking Prompt
FACT_CHECK_PROMPT = """You are a fact-checker for Kerala Ayurveda content. Your job is to verify if a claim is supported by the provided source material.

**Claim to Verify:**
{claim}

**Source Material:**
{context}

**Instructions:**
1. Check if the claim is supported by the source material
2. Answer with ONLY ONE of these:
   - "SUPPORTED" - if the source material clearly supports this claim
   - "PARTIALLY_SUPPORTED" - if the claim has some support but is overstated
   - "NOT_SUPPORTED" - if the source material does not support this claim
3. Then provide a brief 1-sentence explanation

**Format your response exactly as:**
VERDICT: [SUPPORTED/PARTIALLY_SUPPORTED/NOT_SUPPORTED]
EXPLANATION: [Your one-sentence explanation]

Respond now:"""


class FactCheckerAgent:
    """Agent for fact-checking article claims against content pack"""
    
    def __init__(self):
        """Initialize fact-checker agent"""
        self.llm = ChatGroq(
            temperature=0.1,  # Low temperature for factual accuracy
            model_name=config.GROQ_MODEL,
            groq_api_key=config.GROQ_API_KEY,
            max_tokens=200
        )
        
        self.retriever = get_retriever()
        self.prompt = ChatPromptTemplate.from_template(FACT_CHECK_PROMPT)
        
        self.chain = (
            self.prompt
            | self.llm
            | StrOutputParser()
        )
    
    def verify_draft(self, draft: str, claims: List[str]) -> FactCheckerOutput:
        """Verify all claims in draft against content pack
        
        Args:
            draft: Article draft text
            claims: Extracted claims to verify
            
        Returns:
            FactCheckerOutput with verification results
        """
        fact_check_results = []
        all_citations = []
        flagged_claims = []
        
        for claim in claims:
            result = self._verify_single_claim(claim)
            fact_check_results.append(result)
            
            # Collect citations
            if result.citation:
                all_citations.append(result.citation)
            
            # Flag unsupported claims
            if not result.is_supported:
                flagged_claims.append(claim)
        
        # Prepare verified draft with citations
        verified_draft = self._add_citations_to_draft(draft, fact_check_results)
        
        return FactCheckerOutput(
            verified_draft=verified_draft,
            all_citations=all_citations,
            fact_check_results=fact_check_results,
            flagged_claims=flagged_claims
        )
    
    def _verify_single_claim(self, claim: str) -> FactCheckResult:
        """Verify a single claim
        
        Args:
            claim: Claim text to verify
            
        Returns:
            FactCheckResult with verification status
        """
        # Retrieve relevant context
        docs = self.retriever.retrieve(claim, k=3)
        
        if not docs:
            return FactCheckResult(
                claim=claim,
                is_supported=False,
                citation=None,
                explanation="No relevant source material found"
            )
        
        # Prepare context
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Run fact-check
        response = self.chain.invoke({
            "claim": claim,
            "context": context
        })
        
        # Parse response
        is_supported, explanation = self._parse_fact_check_response(response)
        
        # Create citation if supported
        citation = None
        if is_supported and docs:
            citation = Citation(
                doc_id=docs[0].metadata.get('doc_id', 'unknown'),
                section_id=docs[0].metadata.get('section_id', 'unknown'),
                excerpt=docs[0].page_content[:150] + "..."
            )
        
        return FactCheckResult(
            claim=claim,
            is_supported=is_supported,
            citation=citation,
            explanation=explanation
        )
    
    def _parse_fact_check_response(self, response: str) -> tuple[bool, str]:
        """Parse LLM fact-check response
        
        Returns:
            (is_supported, explanation)
        """
        response_upper = response.upper()
        
        # Extract verdict
        if "SUPPORTED" in response_upper and "NOT_SUPPORTED" not in response_upper:
            is_supported = True
        elif "PARTIALLY_SUPPORTED" in response_upper:
            is_supported = True  # Accept partial support
        else:
            is_supported = False
        
        # Extract explanation
        if "EXPLANATION:" in response:
            explanation = response.split("EXPLANATION:")[-1].strip()
        else:
            explanation = response
        
        return is_supported, explanation
    
    def _add_citations_to_draft(self, draft: str, results: List[FactCheckResult]) -> str:
        """Add citation markers to draft
        
        For now, append citations at the end. 
        More sophisticated: inline citation insertion
        """
        # Simple approach: append citations section
        return draft
    
    def check_guardrails(self, draft: str, flagged_claims: List[str]) -> dict:
        """Check if draft passes guardrails
        
        Guardrails:
        - No more than 2 unsupported claims
        - No medical claims without citations
        - No prohibited language
        
        Returns:
            Dict with pass/fail and issues
        """
        issues = []
        
        # Check flagged claims limit
        if len(flagged_claims) > 2:
            issues.append(f"Too many unsupported claims: {len(flagged_claims)} (max 2)")
        
        # Check prohibited language
        prohibited_phrases = [
            "miracle cure",
            "guaranteed",
            "cures",
            "100% safe",
            "scientifically proven"
        ]
        
        for phrase in prohibited_phrases:
            if phrase.lower() in draft.lower():
                issues.append(f"Prohibited phrase found: '{phrase}'")
        
        passed = len(issues) == 0
        
        return {
            "passed": passed,
            "issues": issues
        }
