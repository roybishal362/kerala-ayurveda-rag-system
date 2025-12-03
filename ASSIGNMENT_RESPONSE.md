# Kerala Ayurveda RAG & Agentic System - Assignment Response

**Submitted by:** Bishal Roy 
**Date:** December 3, 2025  
**Role:** Agentic AI Internship - Kerala Ayurveda

---

## Part A: Small RAG Design

### 1. RAG Approach (High-Level Design)

#### Document Chunking Strategy

1. **Markdown Files (Articles, FAQs, Guides)**
   - **Primary strategy**: Split by headers (H2/H3) using `MarkdownHeaderTextSplitter`
   - **Chunk size**: 500-800 characters with 50-character overlap
   - **Special handling for FAQs**: Keep Q&A pairs together as single semantic units
   - **Rationale**: Header-based chunking preserves context and semantic coherence better than arbitrary length splits

2. **CSV File (Product Catalog)**
   - **Strategy**: Each product row = one complete chunk
   - **Rationale**: Product information (name, herbs, contraindications) must stay together for accuracy
   - **Format**: Structured text representation with all fields

3. **Metadata Extraction**
   - Each chunk tagged with: `doc_id`, `section_id`, `doc_type` (product/faq/guide), `source_file`
   - Enables filtered retrieval (e.g., "search only products" or "only FAQs")

#### Retrieval Method

- **Primary**: **Semantic search using embeddings** (HuggingFace `sentence-transformers/all-MiniLM-L6-v2`)
- **Why embeddings over BM25**: 
  - User questions are natural language ("Can I take Ashwagandha with my thyroid medication?")
  - Embeddings capture semantic meaning, not just keyword matches
  - Better for paraphrased queries and synonym handling
- **Vector store**: ChromaDB (lightweight, persisted locally, no separate server)
- **Future enhancement**: Hybrid approach (BM25 + semantic) if keyword precision becomes important

#### Number of Chunks Retrieved

- **Default**: Top **4-5 chunks** per query
- **Reasoning**: 
  - Balance between context richness and token limits
  - Our content pack is focused (9 files), so 4-5 chunks cover most questions comprehensively
  - Groq models handle ~8k tokens; 4-5 chunks + prompt leaves room for answer generation

#### Citation Mechanism

1. **During retrieval**: Mark each chunk with `[SOURCE_1]`, `[SOURCE_2]`, etc. in prompt
2. **In prompt**: Explicitly instruct LLM to reference sources using markers
3. **After generation**: Parse answer for source markers, map back to original metadata
4. **Return format**: 
   ```json
   {
     "doc_id": "product_ashwagandha_tablets_internal",
     "section_id": "Safety & Precautions",
     "excerpt": "People with thyroid disorders... should consult..."
   }
   ```
5. **Fallback**: If no markers found, return all retrieved chunks (conservative approach)

---

### 2. Function Design (Pseudo-Code & Implementation)

```python
def answer_user_query(query: str) -> dict:
    """
    Answer user query using RAG with Kerala Ayurveda content
    
    Args:
        query: User's question (string)
        
    Returns:
        {
            "answer": str,
            "citations": [
                {"doc_id": str, "section_id": str, "excerpt": str}
            ]
        }
    """
    # Step 1: Retrieve relevant documents
    retriever = get_retriever()  # ChromaDB + HuggingFace embeddings
    retrieved_docs = retriever.retrieve(query, k=4)
    
    # Step 2: Prepare context with citation markers
    context_parts = []
    available_citations = []
    
    for i, doc in enumerate(retrieved_docs):
        source_marker = f"[SOURCE_{i+1}]"
        
        # Build citation object
        citation = {
            "doc_id": doc.metadata["doc_id"],
            "section_id": doc.metadata["section_id"],
            "excerpt": doc.page_content[:150] + "..."
        }
        available_citations.append(citation)
        
        # Add to context with marker
        context_parts.append(f"{source_marker}\\n{doc.page_content}")
    
    context_string = "\\n---\\n".join(context_parts)
    
    # Step 3: Build prompt with Kerala Ayurveda brand voice
    prompt = f"""You are a Kerala Ayurveda assistant. Guidelines:
- Warm, grounded tone (no mystical vagueness)
- Use phrases: "traditionally used to support", "may help maintain"
- NEVER claim to cure diseases
- Reference sources using [SOURCE_X] markers
- Include safety disclaimers for medical topics

Context:
{context_string}

Question: {query}

Answer based ONLY on the context above:"""
    
    # Step 4: Call LLM (Groq API with Llama/Mixtral)
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    
    answer = llm.invoke(prompt)
    
    # Step 5: Extract used citations
    used_citations = []
    for i, citation in enumerate(available_citations):
        if f"[SOURCE_{i+1}]" in answer:
            used_citations.append(citation)
    
    # If no markers found, return all (conservative)
    if not used_citations:
        used_citations = available_citations
    
    # Step 6: Return structured response
    return {
        "answer": answer,
        "citations": used_citations
    }
```

**LangChain Implementation Note**: 
The actual code uses LangChain LCEL (Expression Language) for chain composition:
```python
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt_template
    | llm
    | StrOutputParser()
)
```

---

### 3. Example Queries & Outputs

#### **Query 1: "What are the contraindications for Ashwagandha?"**

**Expected Retrieved Documents:**
1. `product_ashwagandha_tablets_internal.md` - Section: "Safety & Precautions"
2. `ayurveda_foundations.md` - Section: "Content Boundaries"

**Answer:**
```
I'm happy to help you with your question about Ashwagandha. However, I must admit that the provided context does not contain enough information to accurately answer your question about the contraindications for Ashwagandha.

As a responsible and grounded assistant, I would like to emphasize the importance of consulting a healthcare provider before using any herbal supplements, including Ashwagandha. They can help you understand potential interactions or contraindications based on your individual health needs and medical history.

Traditionally, Ashwagandha is used to support overall well-being and may help maintain stress resilience. However, it's essential to approach its use with caution and respect for individual health differences. If you're considering using Ashwagandha, please consult with a qualified healthcare provider to discuss potential benefits and risks.

Please note that I'm not providing specific contraindications or dosing instructions, as this information requires a more detailed understanding of your health context. I encourage you to consult with a healthcare provider for personalized guidance on using Ashwagandha or any other herbal supplements. They can help you make informed decisions about your health and well-being.

```

**Citations:**
- `product_ashwagandha_tablets_internal`, "Safety & Precautions", "Not recommended for: Pregnant individuals..."
- `ayurveda_foundations`, "Content Boundaries", "Always add a gentle safety note..."

**Potential Failure Mode:**
- **Incomplete precautions**: If the query is very specific (e.g., "Can I take Ashwagandha with levothyroxine?"), 
  the content pack may not have drug-specific interactions. Risk of hallucinating specific drug interactions.
- **Mitigation**: Prompt instructs LLM to say "consult healthcare provider" when info is insufficient.

---

#### **Query 2: "Can I combine Ayurveda with modern medicine?"**

**Expected Retrieved Documents:**
1. `faq_general_ayurveda_patients.md` - Q1: "Is Ayurveda safe to combine with modern medicine?"
2. `ayurveda_foundations.md` - "How we position Ayurveda"

**Answer:**
```
Combining Ayurveda with modern medicine is a topic of interest for many individuals seeking a holistic approach to wellness. While Ayurveda has been traditionally used to support overall health and well-being, it's essential to approach this combination with caution and respect for both traditions.

Unfortunately, the provided context does not contain enough information to provide a detailed answer to your question. However, I can offer some general guidance. Traditionally, Ayurveda has been used to support health and wellness, and some people may find it helpful to incorporate Ayurvedic practices and principles into their lifestyle. If you're considering combining Ayurveda with modern medicine, it's crucial to consult with a qualified healthcare provider to discuss the potential benefits and risks.

As we always advise, it's essential to prioritize your safety and well-being. When exploring Ayurvedic therapies or herbs, please be aware of potential interactions with modern medications or underlying health conditions. We recommend consulting with a healthcare provider before starting any new therapies or supplements.

In conclusion, while the context doesn't provide a definitive answer, we encourage you to approach this topic with an open mind and a critical perspective. Remember to consult with a qualified healthcare provider to ensure your safety and well-being. They can help you make informed decisions about combining Ayurveda with modern medicine, if appropriate for your individual needs.
```

**Citations:**
- `faq_general_ayurveda_patients`, "Q1", "Ayurveda is often used alongside modern medicine..."
- `ayurveda_foundations`, "Content Boundaries", "No suggesting stopping or changing prescribed medication"

**Potential Failure Mode:**
- **Over-reassurance**: LLM might be too positive about safety if not grounded. Risk: "Yes, it's completely 
  safe!" without caveats.
- **Mitigation**: Strong prompt instructions emphasize Kerala Ayurveda's cautious, grounded tone.

---

#### **Query 3: "What is Pitta dosha and how does it affect me?"**

**Expected Retrieved Documents:**
1. `dosha_guide_vata_pitta_kapha.md` - Section: "Pitta"
2. `ayurveda_foundations.md` - "The Tridosha Model"

**Answer:**
```
I'm happy to help you understand the concept of Pitta dosha. However, I must admit that the provided context doesn't contain enough information about Pitta dosha.

In Ayurveda, the three doshas - Vata, Pitta, and Kapha - are traditionally used to support understanding individual characteristics and health. Unfortunately, without more context, I'm unable to provide specific details about Pitta dosha and its effects.

If you're interested in learning more about Pitta dosha, I recommend consulting with a qualified Ayurvedic practitioner who can provide personalized guidance and support. It's essential to remember that Ayurveda is a traditional system of medicine, and while it may help maintain overall well-being, it's crucial to consult with a healthcare provider for any medical conditions.

Please note that any Ayurvedic therapies or herbs should be used under the guidance of a qualified practitioner, and it's essential to follow safety guidelines to avoid any potential interactions or side effects. If you have any further questions or concerns, feel free to ask, and I'll do my best to provide a helpful response within the limits of the provided context.

**Common Pitta Tendencies (when balanced):**
- Drive, ambition, and natural leadership qualities
- Strong digestion and healthy appetite
- Clarity and decisiveness in thinking

**When Pitta is Imbalanced:**
You may notice:
- Irritability or impatience
- Feeling overheated or skin sensitivity
- Tendency to "overdo" things and experience burnout [SOURCE_1]

**How to Support Balanced Pitta:**
Ayurveda suggests emphasizing:
- **Cooling practices**: Both in food choices and lifestyle
- **Moderation**: Taking time to pause and reflect
- **Connection with nature**: Spending time outdoors can be grounding [SOURCE_1]

**Important Note:**
These patterns are tendencies, not rigid labels [SOURCE_2]. Many people benefit from foundational 
wellness practices—better sleep, mindful eating, gentle movement—even before deep dosha analysis. 
Kerala Ayurveda's content keeps Ayurveda accessible, not gatekept behind complex concepts [SOURCE_1].
```

**Citations:**
- `dosha_guide_vata_pitta_kapha`, "Pitta", "hot, sharp, intense, focused..."
- `ayurveda_foundations`, "Tridosha Model", "Emphasise tendencies and patterns..."

**Potential Failure Mode:**
- **Over-prescription**: Risk of LLM giving specific dietary advice ("Avoid all spicy foods") beyond 
  what's in the content.
- **Missing individual context**: Generic dosha info may not address user's specific situation.
- **Mitigation**: Prompt emphasizes educational tone, not personalized prescriptions. Encourages working 
  with practitioners for tailored guidance.

---

## Part B: Agentic Workflow & Evaluation

### 1. Agent / Step Graph (Article Generation Workflow)

#### **Workflow Overview**
```
Brief Input → [1] Outline Agent → [2] Writer Agent → [3] Fact-Checker Agent → [4] Tone Editor → Final Draft
```

---

#### **Step 1: Outline Agent**

**Role:** Creates structured article outline from brief

**Input Schema:**
```json
{
  "brief": "Write about stress management with Ashwagandha",
  "target_length": "medium",  // short | medium | long
  "include_sections": ["benefits", "usage", "precautions"]  // optional
}
```

**Output Schema:**
```json
{
  "outline": [
    {
      "heading": "Introduction to Ashwagandha for Stress",
      "key_points": [
        "Define stress in modern context",
        "Introduce Ashwagandha as adaptogen",
        "Set expectations (support, not cure)"
      ]
    },
    {
      "heading": "How Ashwagandha Supports Stress Resilience",
      "key_points": ["..."]
    }
  ],
  "key_topics": ["stress", "adaptogen", "resilience", "sleep"]
}
```

**Likely Failure Mode:**
- **Too generic or too specific**: Outline might be too vague ("Benefits" with no depth) or too detailed 
  (straying beyond content pack scope)
- **Missing safety sections**: Might forget to include precautions/contraindications

**Guardrail:**
- **Prompt instruction**: Explicitly require "safety/precautions section if discussing herbs or treatments"
- **Validation check**: Reject outlines without safety section for product/treatment topics

---

#### **Step 2: Writer Agent**

**Role:** Generates article draft following outline with Kerala Ayurveda brand voice

**Input Schema:**
```json
{
  "brief": "...",
  "outline": { /* from Step 1 */ },
  "target_length": "medium"
}
```

**Output Schema:**
```json
{
  "draft": "# Introduction to Ashwagandha for Stress\n\nIn today's fast-paced world...",
  "claims": [
    "Ashwagandha is traditionally used to support the body's ability to adapt to stress",
    "May help maintain restful sleep",
    "..."
  ]
}
```

**Likely Failure Mode:**
- **Adding unsourced claims**: LLM might add plausible but unverified Ayurveda facts not in content pack
- **Repetitive content**: Might reuse same phrases too often
- **Loss of structure**: Could deviate from outline

**Guardrail:**
- **Claim extraction**: Automatically extract factual claims (heuristic: sentences with "traditionally used", 
  "helps", "supports", etc.)
- **Fact-check next**: These claims are verified in Step 3
- **Temperature setting**: Keep at 0.5 (not too creative, stay grounded)

---

#### **Step 3: Fact-Checker Agent**

**Role:** Verify draft claims against content pack using RAG; add citations

**Input Schema:**
```json
{
  "draft": "...",
  "claims": ["Claim 1", "Claim 2", ...]
}
```

**Output Schema:**
```json
{
  "verified_draft": "... [with citation markers added]",
  "all_citations": [
    {"doc_id": "...", "section_id": "...", "excerpt": "..."}
  ],
  "fact_check_results": [
    {
      "claim": "Ashwagandha supports stress resilience",
      "is_supported": true,
      "citation": { /* citation object */ },
      "explanation": "Supported by product dossier"
    }
  ],
  "flagged_claims": ["Claim X that couldn't be verified"]
}
```

**Likely Failure Mode:**
- **False positives**: Accepting a claim as "supported" when retrieval only partially matches
- **Over-flagging**: Being too strict and rejecting valid paraphrases
- **Not catching hallucinations**: If retrieval misses a claim, hallucination slips through

**Guardrails:**
1. **Max unsupported claims**: Reject drafts with >2 flagged claims (hard limit)
2. **Medical claim check**: Any claim about health benefits MUST have a citation (no exceptions)
3. **Prohibited language filter**: Scan for banned phrases ("miracle cure", "guaranteed", "cures disease")
4. **Temperature**: Set to 0.1 for fact-checking (maximize accuracy)

---

#### **Step 4: Tone Editor Agent**

**Role:** Validate Kerala Ayurveda brand voice and ensure safety disclaimers

**Input Schema:**
```json
{
  "verified_draft": "..."
}
```

**Output Schema:**
```json
{
  "final_draft": "... [with tone edits and disclaimer]",
  "tone_suggestions": [
    "Consider softening claim in para 3 to 'may help' instead of 'helps'",
    "Add transition between sections 2 and 3"
  ],
  "safety_disclaimer_added": true
}
```

**Likely Failure Mode:**
- **Over-editing**: Changing meaning or removing valid content
- **Inconsistent style**: Not maintaining Kerala Ayurveda's warm-yet-grounded tone uniformly
- **Missing disclaimers**: Forgetting to add required safety boilerplate

**Guardrails:**
1. **Mandatory disclaimer check**: Verify presence of standard safety disclaimer; auto-add if missing
2. **Prohibited phrase scan**: Final check for banned language
3. **Tone checklist**: Prompt explicitly lists Kerala Ayurveda do's and don'ts from style guide
4. **Revert option**: If too many tone issues flagged (>5), return draft to Writer Agent (future enhancement)

---

### 2. Minimal Evaluation Loop

#### **Golden Set Idea**

Create a small test set of **3-5 briefs** with **expected outputs** ("golden drafts"):

**Example Golden Items:**

| Brief | Expected Characteristics |
|-------|-------------------------|
| "Write about Triphala for digestion" | - Mentions three fruits (Amalaki, Bibhitaki, Haritaki)<br>- Includes safety note about pregnancy/medical conditions<br>- Uses "traditionally used to support"<br>- Has citations from product dossier |
| "Explain Vata dosha" | - Describes keywords (light, dry, mobile)<br>- Balanced and imbalanced tendencies<br>- Educational tone, not prescriptive<br>- Citations from dosha guide |
| "Benefits of Ashwagandha" | - Covers stress, sleep support<br>- Mentions contraindications (thyroid, pregnancy)<br>- Brand voice: warm, grounded<br>- Citations from Ashwagandha dossier |

#### **What to Score**

1. **Grounding / Citation Correctness (Critical)**
   - Are all facts supported by content pack?
   - Are citations accurate (correct doc_id, section_id)?
   - Metric: **% claims with valid citations** (target: >90%)

2. **Brand Voice / Tone Adherence**
   - Uses Kerala Ayurveda preferred language?
   - Avoids prohibited phrases?
   - Metric: **Binary pass/fail** on tone checklist (6-8 criteria)

3. **Safety Compliance**
   - Disclaimer present?
   - No medical claims without sources?
   - No dosing instructions?
   - Metric: **Safety guardrail pass rate** (target: 100%)

4. **Structural Quality**
   - Follows outline?
   - Logical flow between sections?
   - Metric: **Outline adherence score** (1-5 rating, manual)

#### **Metrics to Track Over Time**

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Hallucination Rate** | <5% | % of claims without valid citations in fact-checker output |
| **Fact-Check Pass Rate** | >95% | % of fact-check results marked "is_supported": true |
| **Tone Guardrail Violations** | 0 | Count of prohibited phrases detected by Tone Editor |
| **Safety Disclaimer Coverage** | 100% | % of articles with required disclaimer |
| **Editor Acceptance Rate** | >80%</br>(aspirational) | % of drafts accepted by human editors without major changes<br>(requires human feedback tracking) |
| **Avg. Citations per Article** | 3-6 | Track citation count to ensure grounding |

**Tracking Mechanism:**
- Log all workflow outputs to structured JSON files
- Build simple dashboard/notebook to aggregate metrics
- Weekly review: Plot trends (e.g., hallucination rate over time)

#### **Feedback Loop:**
1. **Human editor review**: Editors mark issues in generated drafts (factual error, tone problem, missing citation)
2. **Annotate failure cases**: Tag with failure mode (hallucination, tone, prohibited language, etc.)
3. **Update prompts**: Refine agent prompts based on recurring issues
4. **Re-test golden set**: After prompt changes, re-run on golden set to verify improvement
5. **Expand golden set**: Add new edge cases as they're discovered

---

### 3. Prioritization for First 2 Weeks

#### **Definitely Ship in 2 Weeks:**

1. **Basic RAG Q&A System** (Week 1, Days 1-3)
   - Document loading and chunking
   - Vector store setup (ChromaDB)
   - Simple Q&A endpoint with citations
   - **Why first**: Foundation for everything else; Growth team can start testing with internal Q&A immediately
   - **Useful immediately**: Helps team answer customer questions faster, even before article generation

2. **Simple Article Generation Workflow** (Week 1, Days 4-7)
   - Outline Agent only (hardcode simple Writer as LLM call)Write Agent
   - Fact-Checker Agent (core value: grounding)
   - Basic Tone Editor (at minimum: add disclaimer)
   - **Why prioritize**: These3 agents deliver 80% of value (structured output, fact-checked, safe)
   - **Shipping criteria**: Can generate one usable draft end-to-end

3. **Critical Guardrails** (Week 2, Days 1-3)
   - Max unsupported claims limit
   - Prohibited language filter
   - Auto-add safety disclaimer
   - **Why critical**: Protects brand reputation; prevents legal/medical risks

4. **FastAPI Endpoints + Basic Testing** (Week 2, Days 4-5)
   - Two endpoints: `/api/query`, `/api/generate-article`
   - Manual testing with 5-6 test queries/briefs
   - One-page user guide for Growth team
   - **Why ship**: Makes system actually usable by team (not just scripts)

5. **Initial Golden Set (3 items)** (Week 2, Day 6)
   - 3 test briefs with expected outputs
   - Run workflow, manually compare
   - Document baseline metrics
   - **Why include**: Enables iterative improvement; shows we're thinking about quality

#### **Explicitly Postpone (and Why):**

1. **Advanced Hybrid Retrieval (BM25 + semantic)**
   - **Why postpone**: Semantic search alone is good enough for our focused content pack
   - **When to revisit**: If user testing shows retrieval misses (unlikely with 9 well-structured docs)
   - **Effort**: Medium; benefit: Low in short term

2. **Inline Citation Insertion**
   - **Why postpone**: Appending citations at end is sufficient for editor workflow
   - Current approach: Fact-Checker returns citations separately; editors add inline manually if desired
   - **When to revisit**: If editors request it for efficiency
   - **Effort**: Medium-high (complex text manipulation); benefit: Nice-to-have

3. **Automated Re-writing on Fact-Check Failure**
   - **Why postpone**: Better to flag issues and let human decide for now
   - Autonomously re-writing carries risk of quality degradation
   - **When to revisit**: After 20-30 drafts reviewed, if patterns emerge
   - **Effort**: High; benefit: Medium (could save editor time, but risky)

4. **Advanced Evaluation Dashboard**
   - **Why postpone**: Manual review of golden set is enough initially
   - **When to build**: After 1-2 weeks of real usage, when we have data to visualize
   - **Effort**: Medium; benefit: Low until we have volume
   - **Week 2**: Just track metrics in spreadsheet

5. **Multi-turn Conversation for Q&A**
   - **Why postpone**: Single-turn Q&A covers vast majority of use cases
   - Content pack is static; most questions don't need follow-ups
   - **When to revisit**: If Growth team requests it after testing
   - **Effort**: Medium (state management); benefit: Low for initial MVP

6. **LangGraph for Workflow Orchestration**
   - **Why postpone**: Sequential function calls work fine for linear workflow
   - Current approach: Simple Python functions chained in `workflow.py`
   - **When to revisit**: If we add conditional branching (e.g., "if fact-check fails badly, restart Writer")
   - **Effort**: Medium (learning curve); benefit: Low for linear workflow

---

**Pragmatic Decision-Making Logic:**

**Ship if:**
- Required for safety (guardrails, disclaimers)
- Unblocks internal users immediately (Q&A, article generation)
- Establishes evaluation baseline (golden set)

**Postpone if:**
- Optimization without clear user pain point (hybrid retrieval, inline citations)
- Nice-to-have automation that risks quality (auto-rewrite)
- Infrastructure we don't have data for yet (dashboard)

**Two-week goal**: 
> *"Growth team can ask questions via API, generate a first draft article with verified facts and proper tone, and we have 3 examples showing it works."*

That's concrete, useful, and shippable.

---
============================================================
Workflow Complete!
============================================================


================================================================================
FINAL DRAFT
================================================================================

## Introduction to Stress Management with Ashwagandha
Stress is an inevitable part of modern life, and its impact on our health can be significant. When left unmanaged, stress may lead to anxiety, fatigue, and a weakened immune system. Traditionally, Ayurvedic practitioners have recommended natural stress management techniques to gently support overall well-being. One such technique involves the use of Ashwagandha, an Ayurvedic herb that has been traditionally used to support stress relief and promote relaxation. You may find that incorporating Ashwagandha into your daily routine can be a valuable addition to your stress management strategy.     

## Benefits of Ashwagandha for Stress Management
Ashwagandha has been studied for its potential to reduce cortisol levels and anxiety, which may help maintain a healthy stress response. Many people notice that Ashwagandha enhances mental clarity and focus, allowing them to approach challenging situations with greater ease. Additionally, Ashwagandha may help promote relaxation and improve sleep quality, which is essential for overall well-being. By gently supporting the body's natural stress response, Ashwagandha can be a useful tool in managing stress and promoting overall health.

## Usage of Ashwagandha for Stress Relief
Ashwagandha is available in various forms, including capsules, powders, and teas. While there are different ways to incorporate Ashwagandha into your daily routine, it's essential to consult with a healthcare professional to determine the best approach for your individual needs. You may find that combining Ashwagandha with other stress-reducing practices, such as meditation or yoga, can enhance its benefits. For example, starting your day with a warm cup of Ashwagandha tea or adding Ashwagandha powder to your morning smoothie can be a great way to set a positive tone for the day.

## Precautions and Safety Considerations
As with any herbal supplement, it's crucial to be aware of potential interactions with medications, such as blood thinners or diabetes medications. Certain individuals, such as those who are pregnant or breastfeeding, should consult with their healthcare provider before using Ashwagandha. It's also important to note that Ashwagandha may not be suitable for everyone, and individual results may vary. To ensure safe and effective use, it's essential to consult with a healthcare professional before adding Ashwagandha to your stress management routine. Please consult with a healthcare professional before using Ashwagandha, especially if you have any underlying medical conditions or are taking medications.

## Incorporating Ashwagandha into Daily Life
Incorporating Ashwagandha into your daily routine can be simple and convenient. You may consider adding Ashwagandha capsules to your daily supplement routine or sipping on Ashwagandha tea before bed to promote relaxation. Some practical tips for adding Ashwagandha to your daily life include:
* Starting your day with a warm cup of Ashwagandha tea
* Adding Ashwagandha powder to your morning smoothie or oatmeal
* Practicing meditation or yoga with Ashwagandha tea
* Setting realistic goals for stress reduction and overall well-being
By making a few simple lifestyle changes, such as regular exercise and mindfulness practices, you can enhance the benefits of Ashwagandha and promote overall well-being.

## Conclusion and Call to Action
In conclusion, Ashwagandha has been traditionally used to support stress relief and promote relaxation. By incorporating Ashwagandha into your daily routine, you may find that it gently supports your body's natural stress response and enhances your overall well-being. We invite you to explore the benefits of Ashwagandha and discover how it can be a valuable addition to your stress management strategy. As you consider trying Ashwagandha, remember to consult with a healthcare professional to determine the best approach for your individual needs. With a holistic approach to stress management, you can take the first step towards a healthier, happier you.

## Reflection

### Time Spent
Approximately **4.5 hours** focused time:
- **1.5 hours**: Reading assignment, exploring content pack, planning approach
- **2 hours**: Implementing RAG system (document loader, retriever, QA chain)
- **1 hour**: Implementing agentic workflow (agents, orchestration)
- **0.5-1 hour**: Writing this response document
- **Ongoing**: Testing and debugging (~30 min scattered)

### What Was Most Interesting

**Most interesting**: 
- **Balancing grounding vs. natural language**: The fact-checking agent design was fascinating—deciding when 
  a claim is "supported enough" versus when it's hallucination. The tension between strict verification 
  (rejecting valid paraphrases) and being too lenient (accepting weak support) is nuanced.
  
- **Brand voice as a technical constraint**: Treating Kerala Ayurveda's tone guidelines as engineerable 
  requirements (parse prompts for prohibited phrases, enforce disclaimer presence) made "soft" content 
  requirements feel concrete. It was like turning a style guide into a validation schema.

**Most unclear:**
- **Citation granularity**: How specific should citations be? Document-level? Section-level? Sentence-level 
  with line numbers? I chose section-level as a pragmatic middle ground, but real user feedback would clarify.
  
- **Acceptable hallucination rate**: What's the actual threshold for "too many unsupported claims"? I set 
  it at 2, but that's a guess. Ideally, I'd like to discuss with Growth/Product teams what risk tolerance is 
  acceptable for drafts (since humans edit anyway).

### AI Tool Usage

**Tools Used: Claude (Anthropic) and ChatGPT (OpenAI)**

**How I used them:**

1. **Code scaffolding** (~30% of code)
   - Generated boilerplate for FastAPI routes, Pydantic schemas
   - Asked for LangChain LCEL syntax examples (I'm more familiar with older LangChain chains)
   - Saved time on imports and basic structure

2. **Debugging edge cases** (~15 min)
   - When ChromaDB initialization had issues, pasted error and got resolution suggestions
   - Helped identify that I needed to handle empty retrieval results

3. **Brainstorming failure modes**
   - Asked ChatGPT: "What could go wrong with a fact-checking agent using RAG?"
   - Got ideas: false positives, over-flagging, missing context
   - I evaluated and adapted them to Kerala Ayurveda's specific risks

4. **Rephrasing this document**
   - Initial draft of this response was too verbose
   - Used Claude to shorten some sections (e.g., rephrased the "Prioritization" explanations to be more concise)

**What I did myself (didn't delegate to AI):**

- **Overall architecture decisions**: 4-agent workflow structure, which agents, what responsibilities
- **Prompt engineering**: All agent prompts (Outline, Writer, Fact-Checker, Tone Editor) I wrote from scratch, 
  iterating based on Kerala Ayurveda's content pack
- **Guardrail design**: Chose specific guardrails (max unsupported claims = 2, prohibited phrase list) based 
  on risk analysis
- **Evaluation framework**: Golden set idea, metrics to track, 2-week prioritization—all my judgment calls
- **Code logic for claim extraction, citation tracking**: Heuristics and parsing functions I designed

**Why this approach:**
- AI is excellent for boilerplate and syntax I'm not fluent in (recent LangChain versions)
- I didn't want AI to make design decisions (e.g., "how many agents?" "what's the passing criteria?") because 
  those require domain context and pragmatic judgment
- Used AI as a **thought partner** (brainstorming), not a **decision maker**

**Honesty note**: 
I could have auto-generated this entire response with ChatGPT, but as Nishant's follow-up email emphasized, 
that would leave me unable to defend choices in an interview. Every technical decision here (chunking strategy, 
agent workflow, guardrails) I can explain the "why" because I made those calls myself.

---

## Appendix: Running the System

### Setup Instructions

1. **Clone/Download Repository**
   ```bash
   cd e:/kerala
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   # Copy example env file
   cp .env.example .env
   
   # Edit .env and add your Groq API key
   # Get free key at: https://console.groq.com
   ```

4. **Run FastAPI Server**
   ```bash
   python -m uvicorn src.main:app --reload
   ```

5. **Test Q&A Endpoint**
   ```bash
   curl -X POST http://localhost:8000/api/query \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the benefits of Triphala?"}'
   ```

6. **Test Article Generation**
   ```bash
   curl -X POST http://localhost:8000/api/generate-article \
     -H "Content-Type: application/json" \
     -d '{
       "brief": "Write about stress management with Ashwagandha",
       "target_length": "medium",
       "include_sections": ["benefits", "usage", "precautions"]
     }'
   ```

### Project Structure
```
e:/kerala/
├── src/
│   ├── main.py                    # FastAPI app
│   ├── config.py                  # Configuration
│   ├── models/schemas.py          # Pydantic models
│   ├── rag/
│   │   ├── document_loader.py     # Chunking logic
│   │   ├── retriever.py           # Vector store & retrieval
│   │   ├── citation_tracker.py    # Citation extraction
│   │   └── qa_chain.py            # Q&A chain (answer_user_query)
│   └── agents/
│       ├── outline_agent.py       # Outline creation
│       ├── writer_agent.py        # Draft generation
│       ├── fact_checker_agent.py  # RAG-based verification
│       ├── tone_editor_agent.py   # Brand voice validation
│       └── workflow.py            # Orchestration
├── kerala_ayurveda_content_pack_v1/  # Content files
├── requirements.txt
└── .env                           # API keys
```

---

**Thank you for this opportunity. I'm excited to discuss this design and implementation in the interview round!**

---

*Namaste* 🙏
