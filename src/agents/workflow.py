"""Workflow orchestration for article generation"""
from src.models.schemas import (
    ArticleBrief, ArticleResponse, AgentState
)
from src.agents.outline_agent import OutlineAgent
from src.agents.writer_agent import WriterAgent
from src.agents.fact_checker_agent import FactCheckerAgent
from src.agents.tone_editor_agent import ToneEditorAgent


class ArticleGenerationWorkflow:
    """Orchestrates multi-agent article generation workflow
    
    Workflow Steps:
    1. Outline Agent - Creates structured outline
    2. Writer Agent - Generates draft content
    3. Fact-Checker Agent - Verifies claims via RAG
    4. Tone Editor Agent - Validates brand voice and safety
    """
    
    def __init__(self):
        """Initialize all agents"""
        print("Initializing Article Generation Workflow...")
        
        self.outline_agent = OutlineAgent()
        self.writer_agent = WriterAgent()
        self.fact_checker_agent = FactCheckerAgent()
        self.tone_editor_agent = ToneEditorAgent()
        
        print("✓ All agents initialized")
    
    def generate_article(self, brief: ArticleBrief) -> ArticleResponse:
        """Run complete article generation workflow
        
        Args:
            brief: ArticleBrief with topic and requirements
            
        Returns:
            ArticleResponse with final draft and metadata
        """
        print(f"\n{'='*60}")
        print(f"Starting Article Generation Workflow")
        print(f"Brief: {brief.brief}")
        print(f"Target Length: {brief.target_length}")
        print(f"{'='*60}\n")
        
        # Initialize state
        state = AgentState(
            brief=brief.brief,
            target_length=brief.target_length,
            include_sections=brief.include_sections
        )
        
        # Step 1: Create Outline
        print("Step 1: Creating outline...")
        state.outline = self.outline_agent.create_outline(
            brief=state.brief,
            target_length=state.target_length,
            include_sections=state.include_sections
        )
        print(f"✓ Outline created with {len(state.outline.outline)} sections")
        print(f"  Key topics: {', '.join(state.outline.key_topics)}")
        
        # Step 2: Write Draft
        print("\nStep 2: Writing article draft...")
        state.writer_output = self.writer_agent.generate_draft(
            brief=state.brief,
            outline=state.outline,
            target_length=state.target_length
        )
        print(f"✓ Draft generated ({len(state.writer_output.draft)} characters)")
        print(f"  Extracted {len(state.writer_output.claims)} claims for verification")
        
        # Step 3: Fact-Check
        print("\nStep 3: Fact-checking claims...")
        state.fact_checker_output = self.fact_checker_agent.verify_draft(
            draft=state.writer_output.draft,
            claims=state.writer_output.claims
        )
        print(f"✓ Fact-check complete")
        print(f"  Supported claims: {len([r for r in state.fact_checker_output.fact_check_results if r.is_supported])}/{len(state.fact_checker_output.fact_check_results)}")
        print(f"  Citations added: {len(state.fact_checker_output.all_citations)}")
        
        if state.fact_checker_output.flagged_claims:
            print(f"  ⚠ Flagged claims: {len(state.fact_checker_output.flagged_claims)}")
        
        # Check guardrails
        guardrail_check = self.fact_checker_agent.check_guardrails(
            state.writer_output.draft,
            state.fact_checker_output.flagged_claims
        )
        
        if not guardrail_check["passed"]:
            print(f"  ⚠ Guardrail issues:")
            for issue in guardrail_check["issues"]:
                print(f"    - {issue}")
        
        # Step 4: Tone Editing
        print("\nStep 4: Editing for brand voice...")
        state.tone_editor_output = self.tone_editor_agent.edit_for_tone(
            state.fact_checker_output.verified_draft
        )
        print(f"✓ Tone editing complete")
        print(f"  Safety disclaimer: {'Added' if state.tone_editor_output.safety_disclaimer_added else 'Already present'}")
        
        if state.tone_editor_output.tone_suggestions:
            print(f"  Tone suggestions: {len(state.tone_editor_output.tone_suggestions)}")
        
        # Build final response
        print(f"\n{'='*60}")
        print("Workflow Complete!")
        print(f"{'='*60}\n")
        
        workflow_metadata = {
            "outline": {
                "sections": [
                    {"heading": s.heading, "points": s.key_points}
                    for s in state.outline.outline
                ],
                "key_topics": state.outline.key_topics
            },
            "fact_checking": {
                "total_claims": len(state.writer_output.claims),
                "supported_claims": len([r for r in state.fact_checker_output.fact_check_results if r.is_supported]),
                "flagged_claims": state.fact_checker_output.flagged_claims,
                "guardrail_check": guardrail_check
            },
            "tone_editing": {
                "suggestions": state.tone_editor_output.tone_suggestions,
                "safety_disclaimer_added": state.tone_editor_output.safety_disclaimer_added
            }
        }
        
        return ArticleResponse(
            final_draft=state.tone_editor_output.final_draft,
            citations=state.fact_checker_output.all_citations,
            workflow_metadata=workflow_metadata
        )


# Global workflow instance
_workflow_instance = None

def get_workflow() -> ArticleGenerationWorkflow:
    """Get or create global workflow instance
    
    Returns:
        Initialized ArticleGenerationWorkflow
    """
    global _workflow_instance
    
    if _workflow_instance is None:
        _workflow_instance = ArticleGenerationWorkflow()
    
    return _workflow_instance
