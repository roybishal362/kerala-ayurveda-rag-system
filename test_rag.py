"""
Test script for Kerala Ayurveda RAG system
Run this to test the answer_user_query function with example queries
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rag.qa_chain import answer_user_query


def test_query(question: str):
    """Test a single query and print results"""
    print(f"\n{'='*80}")
    print(f"QUERY: {question}")
    print(f"{'='*80}\n")
    
    try:
        result = answer_user_query(question)
        
        print("ANSWER:")
        print(result['answer'])
        
        print("\n" + "-"*80)
        print("CITATIONS:")
        for i, citation in enumerate(result['citations'], 1):
            print(f"\n{i}. {citation['doc_id']} → {citation['section_id']}")
            print(f"   Excerpt: {citation['excerpt'][:100]}...")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run example test queries"""
    print("\n" + "#"*80)
    print("# Kerala Ayurveda RAG System - Test Examples")
    print("#"*80)
    
    # Test Query 1: Product contraindications
    test_query("What are the contraindications for Ashwagandha?")
    
    # Test Query 2: General Ayurveda question
    test_query("Can I combine Ayurveda with modern medicine?")
    
    # Test Query 3: Dosha information
    test_query("What is Pitta dosha and how does it affect me?")
    
    # Test Query 4: Product benefits
    test_query("What are the benefits of Triphala?")
    
    print("\n" + "#"*80)
    print("# Tests Complete!")
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
