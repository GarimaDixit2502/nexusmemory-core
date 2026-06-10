# AEME Full-Stack Application - Setup & Deployment Guide

## 🎯 What You're Building

A professional **full-stack web application** for your AEME system:

- **Backend**: FastAPI REST API server
- **Frontend**: Interactive dashboard with live metrics and graph visualization
- **Real-time**: Auto-refreshing metrics every 2 seconds
- **Visual**: D3.js force-directed graph of semantic knowledge

---

## 📁 Project Structure

Create this folder structure:

```
aeme-fullstack/
├── main.py                    # FastAPI server
├── index.html                 # Frontend dashboard
├── models.py                  # Data models (from your fixed files)
├── memory_layers.py           # Memory tiers (from your fixed files)
├── embedding_service.py       # Embeddings (from your fixed files)
├── controller.py              # Controller (from your fixed files)
├── knowledge_extraction.py    # LLM extraction (from your fixed files)
├── router.py                  # Retrieval router (from your fixed files)
├── requirements.txt           # Updated dependencies
└── venv/                      # Virtual environment
```

---

## 🚀 Complete Setup Instructions

### Step 1: Create Project Folder

```bash
# Create new folder for full-stack app
mkdir ~/Desktop/aeme-fullstack
cd ~/Desktop/aeme-fullstack
```

### Step 2: Copy Your Fixed Files

Copy these 6 files from your working `aeme` folder:

```bash
# From your ~/Desktop/aeme folder, copy:
cp ~/Desktop/aeme/models.py .
cp ~/Desktop/aeme/memory_layers.py .
cp ~/Desktop/aeme/embedding_service.py .
cp ~/Desktop/aeme/controller.py .
cp ~/Desktop/aeme/knowledge_extraction.py .
cp ~/Desktop/aeme/router.py .
```

### Step 3: Add New Full-Stack Files

Download and add these 3 NEW files I just created:
1. **main.py** - FastAPI server
2. **index.html** - Frontend dashboard
3. **requirements.txt** - Updated dependencies

### Step 4: Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate it
source venv/bin/activate
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Your existing dependencies (numpy, networkx, sentence-transformers, etc.)

### Step 6: Set OpenAI API Key (Optional)

```bash
# For LLM extraction (optional - works without it)
export OPENAI_API_KEY='your-openai-api-key-here'
```

If you don't set this, the system will use heuristic extraction (still works great!).

### Step 7: Start the Server

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 8: Open the Dashboard

Open your browser and go to:
```
http://localhost:8000
```

You should see the **AEME Dashboard**! 🎉

---

## 🖥️ Using the Dashboard

### 1. **Ingest Content**
- Type or paste text in the "Ingest Content" textarea
- Click "Add to Memory"
- See metrics update in real-time

### 2. **Query Memory**
- Enter a search query
- Toggle STM/MTM/LTM checkboxes to filter tiers
- Click "Search Memory"
- View results from each tier with relevance scores

### 3. **View Knowledge Graph**
- Click "Refresh Graph" to visualize the semantic network
- Nodes = entities
- Edges = relationships
- Hover to see connections

### 4. **Force Consolidation**
- Click "Force Consolidate Now" to immediately move MTM → LTM
- Watch the graph grow!

### 5. **Monitor Metrics**
- Live metrics update every 2 seconds automatically
- See STM, MTM, LTM sizes
- Track LLM vs heuristic extraction stats

---

## 📡 API Endpoints Reference

### `POST /api/ingest`
Ingest new content into memory

**Request:**
```json
{
  "content": "Machine learning is a subset of AI.",
  "metadata": {}
}
```

**Response:**
```json
{
  "success": true,
  "packet_id": "abc123...",
  "message": "Content ingested successfully",
  "current_metrics": {
    "stm_size": 5,
    "mtm_size": 10,
    "ltm_nodes": 25,
    "ltm_edges": 40
  }
}
```

### `POST /api/query`
Query memory for relevant context

**Request:**
```json
{
  "query": "how does machine learning work",
  "stm_enabled": true,
  "mtm_enabled": true,
  "ltm_enabled": true,
  "mtm_top_k": 5,
  "mtm_threshold": 0.3,
  "ltm_max_hops": 2
}
```

**Response:**
```json
{
  "query": "...",
  "combined_context": "--- Short-Term Buffer Context ---\n...",
  "stm_results": [...],
  "mtm_results": [...],
  "ltm_results": [...],
  "metrics": {"latency_ms": 45.2}
}
```

### `GET /api/metrics`
Get current system metrics

**Response:**
```json
{
  "short_term_size": 5,
  "mid_term_size": 10,
  "long_term_nodes": 25,
  "long_term_edges": 40,
  "total_packets_processed": 100,
  "consolidations_performed": 5,
  ...
}
```

### `GET /api/graph`
Get semantic graph structure for visualization

**Response:**
```json
{
  "nodes": [
    {"id": "machine_learning", "label": "Machine Learning", "type": "entity", "group": 1},
    {"id": "neural_networks", "label": "Neural Networks", "type": "entity", "group": 2}
  ],
  "links": [
    {"source": "machine_learning", "target": "neural_networks", "relation": "uses", "weight": 0.9}
  ],
  "stats": {
    "num_nodes": 25,
    "num_edges": 40,
    "density": 0.067
  }
}
```

### `POST /api/consolidate`
Manually trigger consolidation

**Request:**
```json
{
  "batch_size": 10
}
```

**Response:**
```json
{
  "success": true,
  "packets_consolidated": 10,
  "message": "Consolidated 10 packets into semantic graph",
  "updated_metrics": {
    "ltm_nodes": 30,
    "ltm_edges": 45,
    "mtm_size": 5
  }
}
```

---

## 🧪 Testing the API

### Using curl:

```bash
# Test health check
curl http://localhost:8000/health

# Ingest content
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "Machine learning algorithms learn from data."}'

# Query memory
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "mtm_top_k": 3}'

# Get metrics
curl http://localhost:8000/api/metrics

# Get graph
curl http://localhost:8000/api/graph
```

### Using Python:

```python
import requests

BASE_URL = "http://localhost:8000"

# Ingest
response = requests.post(f"{BASE_URL}/api/ingest", json={
    "content": "Deep learning uses neural networks."
})
print(response.json())

# Query
response = requests.post(f"{BASE_URL}/api/query", json={
    "query": "neural networks",
    "mtm_top_k": 5
})
print(response.json()['combined_context'])

# Metrics
response = requests.get(f"{BASE_URL}/api/metrics")
print(response.json())
```

---

## ⚙️ Configuration

### Change Server Port

```bash
# In main.py, change line at the bottom:
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=3000,  # Change to any port you want
    reload=True
)
```

### Disable Auto-Reload (Production)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Enable HTTPS (Production)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 \
  --ssl-keyfile ./key.pem \
  --ssl-certfile ./cert.pem
```

---

## 🎨 Frontend Features

### Interactive Elements:
- ✅ Real-time metrics (auto-refresh every 2s)
- ✅ Ingestion form with instant feedback
- ✅ Query interface with tier filtering
- ✅ D3.js force-directed graph visualization
- ✅ Manual consolidation trigger
- ✅ Responsive design (works on mobile)

### Keyboard Shortcuts:
- `Ctrl+Enter` in ingestion textarea → Submit
- `Enter` in query field → Search

### Visual Feedback:
- Success/error messages with colors
- Loading states during API calls
- Animated metrics updates
- Interactive graph with physics simulation

---

## 🐛 Troubleshooting

### "Address already in use"
Port 8000 is taken. Change the port:
```bash
uvicorn main:app --port 8001
```

### "ModuleNotFoundError: No module named 'fastapi'"
Install dependencies:
```bash
pip install -r requirements.txt
```

### Frontend can't connect to API
Check CORS is enabled (already done in main.py)

### Graph doesn't render
1. Check browser console for errors
2. Make sure you've ingested content
3. Click "Force Consolidate Now"
4. Click "Refresh Graph"

### Slow embedding generation
First embedding loads the model (~5 seconds). Subsequent ones are fast.

---

## 🎯 Quick Start Summary

```bash
# 1. Setup
mkdir aeme-fullstack
cd aeme-fullstack
python3 -m venv venv
source venv/bin/activate

# 2. Add all 9 files (6 existing + 3 new)

# 3. Install
pip install -r requirements.txt

# 4. Run
python main.py

# 5. Open browser
# http://localhost:8000
```

---

## 🎉 Success Indicators

When working correctly, you should see:

**In Terminal:**
```
INFO:     Started server process
INFO:controller:Using real embeddings (dimension: 384)
INFO:controller:Initialized EpistemicMemoryController
INFO:controller:Started background consolidation loop
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**In Browser:**
- Dashboard loads with metrics showing "0" initially
- Can ingest content successfully
- Can query and see results
- Graph updates after consolidation

**That's your production-ready AEME web application!** 🚀
