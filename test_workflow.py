"""
Test script for Kerala Ayurveda Agentic Workflow
Run this to test article generation with example brief
"""
import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.schemas import ArticleBrief
from src.agents.workflow import get_workflow


def test_article_generation(brief: str, target_length: str = "medium", include_sections: list = None):
    """Test article generation workflow"""
    print(f"\n{'='*80}")
    print(f"TESTING ARTICLE GENERATION")
    print(f"{'='*80}\n")
    
    print(f"Brief: {brief}")
    print(f"Target Length: {target_length}")
    if include_sections:
        print(f"Requested Sections: {', '.join(include_sections)}")
    
    try:
        # Create brief
        article_brief = ArticleBrief(
            brief=brief,
            target_length=target_length,
            include_sections=include_sections
        )
        
        # Run workflow
        workflow = get_workflow()
        result = workflow.generate_article(article_brief)
        
        # Print results
        print("\n" + "="*80)
        print("FINAL DRAFT")
        print("="*80 + "\n")
        print(result.final_draft)
        
        print("\n" + "="*80)
        print("CITATIONS")
        print("="*80 + "\n")
        for i, citation in enumerate(result.citations, 1):
            print(f"{i}. {citation.doc_id} → {citation.section_id}")
        
        print("\n" + "="*80)
        print("WORKFLOW METADATA")
        print("="*80 + "\n")
        
        # Fact-checking results
        fc = result.workflow_metadata['fact_checking']
        print(f"Fact-Checking:")
        print(f"  Total claims: {fc['total_claims']}")
        print(f"  Supported claims: {fc['supported_claims']}")
        print(f"  Flagged claims: {len(fc['flagged_claims'])}")
        
        if fc['flagged_claims']:
            print(f"  ⚠ Flagged:")
            for claim in fc['flagged_claims']:
                print(f"    - {claim[:100]}...")
        
        # Guardrail check
        gc = fc['guardrail_check']
        print(f"\nGuardrail Check: {'✓ PASSED' if gc['passed'] else '✗ FAILED'}")
        if gc['issues']:
            for issue in gc['issues']:
                print(f"  - {issue}")
        
        # Tone editing
        te = result.workflow_metadata['tone_editing']
        print(f"\nTone Editing:")
        print(f"  Safety disclaimer added: {te['safety_disclaimer_added']}")
        if te['suggestions']:
            print(f"  Suggestions ({len(te['suggestions'])}):")
            for suggestion in te['suggestions']:
                print(f"    - {suggestion}")
        
        return result
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run example article generation tests"""
    print("\n" + "#"*80)
    print("# Kerala Ayurveda Agentic Workflow - Test Examples")
    print("#"*80)
    
    # Test 1: Ashwagandha for stress
    test_article_generation(
        brief="Write about stress management with Ashwagandha",
        target_length="medium",
        include_sections=["benefits", "usage", "precautions"]
    )
    
    print("\n" + "#"*80)
    print("# Test Complete!")
    print("#"*80 + "\n")


if __name__ == "__main__":
    # Check if Groq API key is set
    from src.config import config
    
    if not config.GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set in environment")
        print("Please create a .env file with your Groq API key")
        print("See .env.example for template")
        sys.exit(1)
    
    main()
