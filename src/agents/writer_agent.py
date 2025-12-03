"""Writer Agent for generating article drafts"""
from typing import List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config import config
from src.models.schemas import OutlineOutput, WriterOutput


# Writer Agent Prompt
WRITER_PROMPT = """You are a skilled content writer for Kerala Ayurveda, creating articles that inform and guide readers.

**Brand Voice (CRITICAL - Follow Strictly):**
- Warm & reassuring - like a calm, knowledgeable practitioner
- Grounded & precise - no vague mystical claims
- Traditional yet science-friendly
- Use phrases: "traditionally used to support", "may help maintain", "gently supports"
- NEVER use: "miracle cure", "guaranteed results", "100% safe for everyone", "cures disease"

**Content Structure:**
- Clear H2/H3 headings
- Short paragraphs (2-4 sentences)
- Bulleted lists for practical points
- Invitational language: "You may find...", "Many people notice..."

**Medical & Legal Boundaries (NON-NEGOTIABLE):**
- NO specific dosing instructions
- NO disease-cure claims
- NO advising to stop/change medications
- ALWAYS encourage consulting healthcare providers
- Use person-first language

**Your Task:**
Write an article based on the following outline.

**Article Brief:** {brief}

**Outline:**
{outline}

**Target Length:** {target_length} (short=300-400 words, medium=500-700 words, long=800-1000 words)

**Instructions:**
1. Follow the outline structure closely
2. Maintain Kerala Ayurveda's warm, grounded tone throughout
3. Make specific claims that can be verified (fact-checker will review)
4. Write naturally - be informative yet accessible
5. Include transitional phrases between sections
6. End with a practical takeaway or gentle call-to-action

Write the article now:"""


class WriterAgent:
    """Agent for generating article content"""
    
    def __init__(self):
        """Initialize writer agent"""
        self.llm = ChatGroq(
            temperature=0.5,  # Slightly higher for creativity
            model_name=config.GROQ_MODEL,
            groq_api_key=config.GROQ_API_KEY,
            max_tokens=1500
        )
        
        self.prompt = ChatPromptTemplate.from_template(WRITER_PROMPT)
        
        # LCEL Chain
        self.chain = (
            self.prompt
            | self.llm
            | StrOutputParser()
        )
    
    def generate_draft(self, brief: str, outline: OutlineOutput, target_length: str = "medium") -> WriterOutput:
        """Generate article draft from outline
        
        Args:
            brief: Article brief/topic
            outline: Structured outline
            target_length: short, medium, or long
            
        Returns:
            WriterOutput with draft and extracted claims
        """
        # Format outline for prompt
        outline_text = ""
        for section in outline.outline:
            outline_text += f"\n## {section.heading}\n"
            for point in section.key_points:
                outline_text += f"- {point}\n"
        
        # Generate draft
        draft = self.chain.invoke({
            "brief": brief,
            "outline": outline_text,
            "target_length": target_length
        })
        
        # Extract claims (simple heuristic - sentences with specific assertions)
        claims = self._extract_claims(draft)
        
        return WriterOutput(
            draft=draft,
            claims=claims
        )
    
    def _extract_claims(self, draft: str) -> List[str]:
        """Extract factual claims from draft for verification
        
        Simple heuristic: Look for sentences containing key claim indicators
        """
        claim_indicators = [
            "traditionally used",
            "helps",
            "supports",
            "may",
            "contains",
            "known for",
            "benefits include",
            "used in Ayurveda for"
        ]
        
        claims = []
        sentences = draft.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if sentence contains claim indicators
            for indicator in claim_indicators:
                if indicator.lower() in sentence.lower():
                    claims.append(sentence + '.')
                    break
        
        return claims[:10]  # Limit to top 10 claims
