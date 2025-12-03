"""Outline Agent for creating article structure"""
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config import config
from src.models.schemas import OutlineOutput, OutlineSection


# Outline Agent Prompt
OUTLINE_PROMPT = """You are an outline creator for Kerala Ayurveda articles. Your job is to structure article content logically and comprehensively.

**Article Brief:** {brief}

**Target Length:** {target_length} (short=3-4 sections, medium=4-6 sections, long=6-8 sections)

**Requested Sections (if any):** {include_sections}

**Your Task:**
Create a clear, logical outline for this article that:
1. Has an engaging introduction
2. Covers key aspects of the topic
3. Includes practical information (benefits, usage, precautions if relevant)
4. Ends with a takeaway or gentle call-to-action

**Guidelines:**
- Each section should have 2-4 key points to cover
- Use clear, descriptive headings
- Ensure logical flow between sections
- Include safety/precautions section if discussing herbs or treatments

**Output Format:**
SECTION: [Section Heading]
- [Key point 1]
- [Key point 2]
- [Key point 3]

SECTION: [Next Section Heading]
- [Key point 1]
- [etc.]

KEY_TOPICS: [topic1], [topic2], [topic3]

Create the outline now:"""


class OutlineAgent:
    """Agent for creating article outlines"""
    
    def __init__(self):
        """Initialize outline agent"""
        self.llm = ChatGroq(
            temperature=0.4,
            model_name=config.GROQ_MODEL,
            groq_api_key=config.GROQ_API_KEY,
            max_tokens=800
        )
        
        self.prompt = ChatPromptTemplate.from_template(OUTLINE_PROMPT)
        
        self.chain = (
            self.prompt
            | self.llm
            | StrOutputParser()
        )
    
    def create_outline(self, brief: str, target_length: str = "medium", include_sections: list = None) -> OutlineOutput:
        """Create article outline
        
        Args:
            brief: Article brief/topic
            target_length: short, medium, or long
            include_sections: Specific sections to include
            
        Returns:
            OutlineOutput with structured outline
        """
        # Format include_sections
        sections_str = ", ".join(include_sections) if include_sections else "None specified"
        
        # Generate outline
        response = self.chain.invoke({
            "brief": brief,
            "target_length": target_length,
            "include_sections": sections_str
        })
        
        # Parse outline
        outline_sections, key_topics = self._parse_outline(response)
        
        return OutlineOutput(
            outline=outline_sections,
            key_topics=key_topics
        )
    
    def _parse_outline(self, response: str) -> tuple[list[OutlineSection], list[str]]:
        """Parse LLM outline response
        
        Returns:
            (outline_sections, key_topics)
        """
        sections = []
        key_topics = []
        
        current_section = None
        current_points = []
        
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Check for section header
            if line.startswith("SECTION:"):
                # Save previous section
                if current_section:
                    sections.append(OutlineSection(
                        heading=current_section,
                        key_points=current_points
                    ))
                
                # Start new section
                current_section = line.replace("SECTION:", "").strip()
                current_points = []
            
            # Check for key topics
            elif line.startswith("KEY_TOPICS:"):
                topics_str = line.replace("KEY_TOPICS:", "").strip()
                key_topics = [t.strip() for t in topics_str.split(',')]
            
            # Check for key points
            elif line.startswith('-') or line.startswith('•'):
                point = line.lstrip('-•').strip()
                if point:
                    current_points.append(point)
        
        # Add last section
        if current_section:
            sections.append(OutlineSection(
                heading=current_section,
                key_points=current_points
            ))
        
        return sections, key_topics
