# NexusMemory Core

A production-ready three-tier cognitive architecture for LLM memory management.

## Architecture

- **Short-Term Buffer (STM)**: FIFO queue for immediate data processing
- **Mid-Term Episodic Layer (MTM)**: Vector search with decay-based scoring (similarity + recency + frequency)
- **Long-Term Semantic Graph (LTM)**: NetworkX knowledge graph with entity-relationship mapping

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2, 384-dim)
- **Knowledge Extraction**: OpenAI GPT-4o-mini with heuristic fallback
- **Graph**: NetworkX for semantic knowledge representation
- **Frontend**: Vanilla JS, D3.js force-directed graph visualization
- **Design**: Custom warm editorial aesthetic (DM Serif Text, cream/sage/terracotta palette)

## Installation

\`\`\`bash
# Clone repository
git clone https://github.com/GarimaDixit2502/nexusmemory-core.git
cd nexusmemory-core

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key (optional - uses heuristic fallback if not set)
export OPENAI_API_KEY='your-key-here'

# Run server
python main.py

# Open browser
# http://localhost:8000
\`\`\`

## Features

- ✅ Three-tier memory architecture (STM → MTM → LTM)
- ✅ Real-time vector embeddings with sentence-transformers
- ✅ LLM-powered knowledge extraction (OpenAI GPT-4o-mini)
- ✅ Heuristic extraction fallback (no API key required)
- ✅ Interactive D3.js knowledge graph visualization
- ✅ Async consolidation with background workers
- ✅ REST API with FastAPI
- ✅ Production-ready frontend with custom design system

## API Endpoints

- `POST /api/ingest` - Add content to memory
- `POST /api/query` - Retrieve context across all tiers
- `GET /api/metrics` - System statistics
- `GET /api/graph` - Knowledge graph data (nodes + edges)
- `POST /api/consolidate` - Force MTM → LTM consolidation
- `GET /health` - Health check


