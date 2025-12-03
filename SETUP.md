# Quick Setup Guide

## Kerala Ayurveda RAG & Agentic System

### Prerequisites
- Python 3.10 or higher
- Groq API key (get free at https://console.groq.com)

---

### Step 1: Install Dependencies

```bash
cd e:/kerala
pip install -r requirements.txt
```

**Note**: This will install:
- FastAPI, uvicorn
- LangChain, langchain-groq
- ChromaDB
- sentence-transformers
- Other dependencies

Installation takes ~5 minutes depending on internet speed.

---

### Step 2: Configure Groq API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env in your text editor
# Add your Groq API key:
GROQ_API_KEY=your_actual_api_key_here
```

**Getting a Groq API Key:**
1. Go to https://console.groq.com
2. Sign up (free)
3. Navigate to API Keys section
4. Create a new key
5. Copy and paste into `.env`

---

### Step 3: Run the FastAPI Server

```bash
python -m uvicorn src.main:app --reload
```

**Expected Output:**
```
Kerala Ayurveda RAG & Agentic System
====================================
✓ Groq API key configured
✓ Content pack path: ./kerala_ayurveda_content_pack_v1
✓ Model: llama-3.1-70b-versatile
✓ Embeddings: sentence-transformers/all-MiniLM-L6-v2

Initializing RAG system...
Loading embedding model...
✓ Embeddings model loaded
Loading documents from content pack...
✓ Loaded 42 document chunks
Creating new vector store...
✓ Created and persisted vector store
✓ Retriever configured (top-k=4)
✓ QA Chain initialized with LCEL
✓ RAG system ready

Initializing agentic workflow...
✓ All agents initialized
✓ Agentic workflow ready

System Ready!
====================================
```

Server runs on: **http://localhost:8000**

---

### Step 4: Test the System

#### Option A: Use Test Scripts

**Test RAG Q&A:**
```bash
python test_rag.py
```

**Test Article Generation:**
```bash
python test_workflow.py
```

#### Option B: Use API Directly

**Test Q&A (curl):**
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the benefits of Triphala?"}'
```

**Test Article Generation (curl):**
```bash
curl -X POST http://localhost:8000/api/generate-article \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Write about stress management with Ashwagandha",
    "target_length": "medium"
  }'
```

#### Option C: Use Browser

1. Go to http://localhost:8000/docs
2. FastAPI auto-generates interactive API documentation
3. Click "Try it out" on any endpoint
4. Test directly in browser

---

### Troubleshooting

#### Error: "GROQ_API_KEY not set"
- Make sure you created `.env` file
- Check that the key is correctly formatted: `GROQ_API_KEY=gsk_...`
- Restart the server after editing `.env`

#### Error: "ModuleNotFoundError"
- Run `pip install -r requirements.txt` again
- Make sure you're in the `e:/kerala` directory

#### ChromaDB Initialization Issues
- Delete the `chroma_db` folder and restart
- The system will recreate the vector store

#### Slow First Query
- First query is slower (~10-20 seconds) due to model loading
- Subsequent queries are fast (~2-3 seconds)

---

### Next Steps

- **Read the full assignment response**: `ASSIGNMENT_RESPONSE.md`
- **Explore the code**: Start with `src/main.py` and follow imports
- **Try different queries**: Test with various Ayurveda questions
- **Generate articles**: Experiment with different briefs

---

### Files to Review

1. **ASSIGNMENT_RESPONSE.md** - Complete assignment writeup
2. **README.md** - Detailed project documentation
3. **src/rag/qa_chain.py** - See the `answer_user_query` function
4. **src/agents/workflow.py** - See the 4-agent workflow

---

### Contact

For questions or issues with this assignment submission, please refer to the assignment response document or reach out during the interview round.

---

**Quick Command Reference:**

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
# (edit .env with your API key)

# Run server
python -m uvicorn src.main:app --reload

# Test
python test_rag.py
python test_workflow.py
```

---

Namaste! 🙏
