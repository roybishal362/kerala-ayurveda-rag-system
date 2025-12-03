# Kerala Ayurveda RAG & Agentic System

> **Internship Assignment Submission**  
> Agentic AI Internship - Kerala Ayurveda Ltd.

A production-ready RAG (Retrieval-Augmented Generation) Q&A system and multi-agent article generation workflow built with **FastAPI**, **LangChain**, and **Groq API**.

---

## 🎯 Project Overview

This system provides two core capabilities for Kerala Ayurveda:

1. **RAG-based Q&A**: Answer questions about Ayurveda, products, and treatments using only the provided content pack
2. **Agentic Article Generation**: Multi-step workflow that creates fact-checked, brand-aligned articles

### Key Features

- ✅ **Grounded Responses**: All answers cite specific source documents
- ✅ **Fact-Checking**: RAG-based verification of every claim
- ✅ **Brand Voice Compliance**: Automatic tone validation against Kerala Ayurveda guidelines
- ✅ **Safety Guardrails**: Prohibited language detection, mandatory disclaimers
- ✅ **Citation Tracking**: Every fact linked to source material

---

## 🏗️ Architecture

### RAG System (Part A)

```
User Query → Semantic Retrieval (ChromaDB) → LLM (Groq) → Answer + Citations
```

**Chunking Strategy:**
- Markdown: Split by headers (H2/H3) for semantic coherence
- CSV: One product per chunk for data integrity
- Chunk size: 500-800 chars with 50-char overlap

**Retrieval:**
- HuggingFace embeddings (`sentence-transformers/all-MiniLM-L6-v2`)
- ChromaDB vector store (persisted locally)
- Top-K: 4-5 chunks per query

### Agentic Workflow (Part B)

```
Brief → [Outline Agent] → [Writer Agent] → [Fact-Checker] → [Tone Editor] → Final Draft
```

**Agents:**
1. **Outline Agent**: Creates structured article outline
2. **Writer Agent**: Generates draft with Kerala Ayurveda voice
3. **Fact-Checker Agent**: Verifies claims via RAG, adds citations
4. **Tone Editor Agent**: Validates brand voice, ensures safety disclaimers

**Guardrails:**
- Max 2 unsupported claims before rejection
- Prohibited language filter ("miracle cure", "guaranteed", etc.)
- Mandatory safety disclaimers for medical content

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Groq API key (free tier available at [console.groq.com](https://console.groq.com))

### Installation

```bash
# 1. Navigate to project directory
cd e:/kerala

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env

# Edit .env and add your GROQ_API_KEY
```

### Running the Server

```bash
# Start FastAPI server
python -m uvicorn src.main:app --reload
```

Server runs on: `http://localhost:8000`

---

## 📡 API Endpoints

### 1. RAG Q&A: `/api/query`

**Request:**
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the contraindications for Ashwagandha?"
  }'
```

**Response:**
```json
{
  "answer": "Ashwagandha is not recommended for...",
  "citations": [
    {
      "doc_id": "product_ashwagandha_tablets_internal",
      "section_id": "Safety & Precautions",
      "excerpt": "People with thyroid disorders..."
    }
  ],
  "retrieved_chunks": 4
}
```

### 2. Article Generation: `/api/generate-article`

**Request:**
```bash
curl -X POST http://localhost:8000/api/generate-article \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Write about stress management with Ashwagandha",
    "target_length": "medium",
    "include_sections": ["benefits", "usage", "precautions"]
  }'
```

**Response:**
```json
{
  "final_draft": "# Stress Management with Ashwagandha...",
  "citations": [...],
  "workflow_metadata": {
    "outline": {...},
    "fact_checking": {
      "total_claims": 8,
      "supported_claims": 7,
      "flagged_claims": []
    },
    "tone_editing": {...}
  }
}
```

### 3. Health Check: `/health`

```bash
curl http://localhost:8000/health
```

---

## 📂 Project Structure

```
e:/kerala/
├── src/
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Environment configuration
│   ├── models/
│   │   └── schemas.py             # Pydantic models
│   ├── rag/
│   │   ├── document_loader.py     # Content pack loading & chunking
│   │   ├── retriever.py           # Vector store & semantic search
│   │   ├── citation_tracker.py    # Citation extraction
│   │   └── qa_chain.py            # Q&A chain (answer_user_query)
│   └── agents/
│       ├── outline_agent.py       # Article outline creation
│       ├── writer_agent.py        # Draft generation
│       ├── fact_checker_agent.py  # Claim verification
│       ├── tone_editor_agent.py   # Brand voice validation
│       └── workflow.py            # Workflow orchestration
├── kerala_ayurveda_content_pack_v1/  # Content files
├── requirements.txt
├── .env.example
├── ASSIGNMENT_RESPONSE.md         # Detailed assignment write-up
└── README.md                      # This file
```

---

## 🧪 Testing

### Example Test Queries

1. **"What are the benefits of Triphala?"**
   - Expected: Digestive support, three fruits mentioned, citations from product dossier

2. **"Can I combine Ayurveda with modern medicine?"**
   - Expected: Yes with caveats, encourages consulting doctors, citations from FAQ

3. **"What is Pitta dosha?"**
   - Expected: Hot/sharp/intense, balanced vs imbalanced traits, citations from dosha guide

### Example Article Generation

```python
# Brief: "Benefits of Ashwagandha for stress"
# Expected output:
# - Sections on stress resilience, usage, precautions
# - Claims verified against product dossier
# - Safety disclaimer included
# - Kerala Ayurveda tone (warm, grounded)
```

---

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# Groq API
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-70b-versatile

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector Store
CHROMA_PERSIST_DIR=./chroma_db

# Chunking
CHUNK_SIZE=600
CHUNK_OVERLAP=50

# Retrieval
TOP_K_CHUNKS=4
```

---

## 📊 Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **API Framework** | FastAPI | Modern, async, auto-docs |
| **LLM Orchestration** | LangChain (LCEL) | Chain composition, prompt templates |
| **LLM Provider** | Groq API | Fast inference, free tier |
| **Models** | Llama 3.1 70B, Mixtral 8x7B | Good balance of quality & speed |
| **Embeddings** | HuggingFace Sentence Transformers | Free, good quality |
| **Vector Store** | ChromaDB | Lightweight, no server needed |
| **Validation** | Pydantic | Type safety, auto-validation |

---

## 📝 Assignment Response

See [`ASSIGNMENT_RESPONSE.md`](./ASSIGNMENT_RESPONSE.md) for the complete assignment write-up covering:

- **Part A**: RAG design rationale, function pseudo-code, 3 example queries with outputs
- **Part B**: 4-agent workflow design with schemas, evaluation framework, 2-week prioritization
- **Reflection**: Time spent, interesting challenges, AI tool usage transparency

---

## 🎓 Learning Highlights

**What makes this implementation valuable:**

1. **Grounding over Creativity**: Fact-checker ensures no hallucinations slip through
2. **Brand as Code**: Kerala Ayurveda's style guide becomes executable guardrails
3. **Pragmatic Agents**: Simple sequential workflow (not over-engineered LangGraph) that works
4. **Citation-First**: Every claim traceable to source—builds trust
5. **Safety-Conscious**: Medical content protection baked into every agent

---

## 🤝 Acknowledgments

Built as part of the Agentic AI Internship assignment for **Kerala Ayurveda Ltd.**

**Content Pack**: 9 internal documents (FAQs, product dossiers, style guides, treatment programs)

---

## 📧 Contact

*Assignment submission for interview consideration*

---

**Namaste!** 🙏
