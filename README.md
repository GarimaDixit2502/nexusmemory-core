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

## Screenshots

<img width="946" height="727" alt="Screenshot 2026-06-11 at 12 42 29 AM" src="https://github.com/user-attachments/assets/b2b0c703-8c3e-47c3-b4d8-fc2117676e6c" />
<img width="949" height="716" alt="Screenshot 2026-06-11 at 12 42 50 AM" src="https://github.com/user-attachments/assets/3c6b46c0-5264-465d-8c4d-841cf25c2f88" />
<img width="949" height="708" alt="Screenshot 2026-06-11 at 12 42 58 AM" src="https://github.com/user-attachments/assets/1fc1511a-97de-456e-9d2d-24ef0dcb47d8" />
<img width="949" height="704" alt="Screenshot 2026-06-11 at 12 43 09 AM" src="https://github.com/user-attachments/assets/41647954-4874-4357-acc3-8e31020f7ecc" />
<img width="949" height="709" alt="Screenshot 2026-06-11 at 12 43 36 AM" src="https://github.com/user-attachments/assets/4d976e43-4077-4146-bf20-18d4e011079e" />
<img width="946" height="713" alt="Screenshot 2026-06-11 at 12 44 00 AM" src="https://github.com/user-attachments/assets/17284750-794c-4ac5-b86b-171f0ecac5fc" />
<img width="946" height="710" alt="Screenshot 2026-06-11 at 12 44 32 AM" src="https://github.com/user-attachments/assets/85327833-55b8-4f3e-9e61-7d1b6ab463ff" />
