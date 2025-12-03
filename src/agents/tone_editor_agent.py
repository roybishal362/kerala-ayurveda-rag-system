"""Tone Editor Agent for brand voice validation"""
from typing import List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config import config
from src.models.schemas import ToneEditorOutput


# Tone Editing Prompt
TONE_EDITOR_PROMPT = """You are a tone and style editor for Kerala Ayurveda. Your job is to ensure content matches the brand voice and includes required safety elements.

**Kerala Ayurveda Brand Voice:**
- Warm & reassuring (like a calm practitioner)
- Grounded & precise (no vague mystical claims)
- Respectful of tradition AND modern science
- Invitational, not prescriptive

**Preferred Language:**
- "traditionally used to support"
- "may help maintain"
- "gently supports"
- "find space to"

**Prohibited Language:**
- "miracle cure"
- "guaranteed results"
- "100% safe for everyone"
- "cures [disease]"

**Required Elements:**
- Safety disclaimer for medical content
- Encouragement to consult healthcare providers
- Person-first language

**Article to Review:**
{draft}

**Your Tasks:**
1. Review the tone and style
2. Check for prohibited language
3. Suggest 2-3 specific improvements (if needed)
4. Verify safety disclaimer is present (or note it's missing)
5. Make minor edits to improve brand alignment

**Output Format:**
EDITED_DRAFT:
[Your edited version of the article]

TONE_SUGGESTIONS:
- [Suggestion 1]
- [Suggestion 2]
- [etc.]

SAFETY_DISCLAIMER_STATUS: [PRESENT/MISSING/NEEDS_IMPROVEMENT]

Respond now:"""


class ToneEditorAgent:
    """Agent for validating and improving brand voice"""
    
    def __init__(self):
        """Initialize tone editor agent"""
        self.llm = ChatGroq(
            temperature=0.3,  # Moderate creativity for editing
            model_name=config.GROQ_MODEL,
            groq_api_key=config.GROQ_API_KEY,
            max_tokens=2000
        )
        
        self.prompt = ChatPromptTemplate.from_template(TONE_EDITOR_PROMPT)
        
        self.chain = (
            self.prompt
            | self.llm
            | StrOutputParser()
        )
    
    def edit_for_tone(self, draft: str) -> ToneEditorOutput:
        """Edit draft for brand voice and safety compliance
        
        Args:
            draft: Article draft to review
            
        Returns:
            ToneEditorOutput with edited draft and suggestions
        """
        # Run tone check
        response = self.chain.invoke({"draft": draft})
        
        # Parse response
        final_draft, suggestions, disclaimer_status = self._parse_editor_response(response, draft)
        
        # Ensure safety disclaimer if missing
        if "MISSING" in disclaimer_status:
            final_draft = self._add_safety_disclaimer(final_draft)
            disclaimer_added = True
        else:
            disclaimer_added = "PRESENT" in disclaimer_status
        
        return ToneEditorOutput(
            final_draft=final_draft,
            tone_suggestions=suggestions,
            safety_disclaimer_added=disclaimer_added
        )
    
    def _parse_editor_response(self, response: str, original_draft: str) -> tuple[str, List[str], str]:
        """Parse editor response
        
        Returns:
            (edited_draft, suggestions, disclaimer_status)
        """
        # Extract edited draft
        if "EDITED_DRAFT:" in response:
            draft_section = response.split("EDITED_DRAFT:")[1]
            if "TONE_SUGGESTIONS:" in draft_section:
                edited_draft = draft_section.split("TONE_SUGGESTIONS:")[0].strip()
            else:
                edited_draft = draft_section.strip()
        else:
            edited_draft = original_draft
        
        # Extract suggestions
        suggestions = []
        if "TONE_SUGGESTIONS:" in response:
            suggestions_section = response.split("TONE_SUGGESTIONS:")[1]
            if "SAFETY_DISCLAIMER_STATUS:" in suggestions_section:
                suggestions_section = suggestions_section.split("SAFETY_DISCLAIMER_STATUS:")[0]
            
            # Parse bullet points
            lines = suggestions_section.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    suggestions.append(line.lstrip('-•').strip())
        
        # Extract disclaimer status
        disclaimer_status = "UNKNOWN"
        if "SAFETY_DISCLAIMER_STATUS:" in response:
            status_line = response.split("SAFETY_DISCLAIMER_STATUS:")[1].split('\n')[0].strip()
            disclaimer_status = status_line
        
        return edited_draft, suggestions, disclaimer_status
    
    def _add_safety_disclaimer(self, draft: str) -> str:
        """Add standard safety disclaimer to draft"""
        disclaimer = """

---

**Important Note:**
This article is for informational purposes and is not a substitute for medical advice, diagnosis, or treatment. Ayurvedic herbs and therapies may not be suitable for everyone. Individuals with existing medical conditions, those who are pregnant or nursing, or anyone taking prescription medications should consult their healthcare provider before starting any new supplement or therapy. Kerala Ayurveda encourages you to work with qualified practitioners for personalized guidance."""
        
        return draft + disclaimer
