"""
AEME - FastAPI Backend Server
==============================
Production-ready API server for the Autonomous Epistemic Memory Engine.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import uvicorn
import os

from models import MemoryPacket, SystemMetrics
from controller import EpistemicMemoryController
from router import UnifiedRetrievalRouter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory where main.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Global instances
controller: Optional[EpistemicMemoryController] = None
router: Optional[UnifiedRetrievalRouter] = None


# ============================================================================
# API Request/Response Models
# ============================================================================

class IngestRequest(BaseModel):
    """Request model for ingesting new content"""
    content: str = Field(..., min_length=1, description="Text content to ingest")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")


class IngestResponse(BaseModel):
    """Response model for ingestion"""
    success: bool
    packet_id: str
    message: str
    current_metrics: Dict[str, int]


class QueryRequest(BaseModel):
    """Request model for context retrieval"""
    query: str = Field(..., min_length=1, description="Query string")
    stm_enabled: bool = Field(default=True, description="Include STM results")
    mtm_enabled: bool = Field(default=True, description="Include MTM results")
    ltm_enabled: bool = Field(default=True, description="Include LTM results")
    mtm_top_k: int = Field(default=5, ge=1, le=20, description="Number of MTM results")
    mtm_threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Similarity threshold")
    ltm_max_hops: int = Field(default=2, ge=1, le=5, description="Max graph traversal hops")


class QueryResponse(BaseModel):
    """Response model for retrieval"""
    query: str
    combined_context: str
    stm_results: List[Dict[str, Any]]
    mtm_results: List[Dict[str, Any]]
    ltm_results: List[Dict[str, Any]]
    metrics: Dict[str, Any]


class MetricsResponse(BaseModel):
    """Response model for system metrics"""
    short_term_size: int
    mid_term_size: int
    long_term_nodes: int
    long_term_edges: int
    consolidations_performed: int
    total_packets_processed: int
    llm_extractions: int
    heuristic_extractions: int
    failed_extractions: int
    extraction_statistics: Dict[str, Any]


class GraphData(BaseModel):
    """Response model for graph visualization"""
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    stats: Dict[str, Any]


class ConsolidateRequest(BaseModel):
    """Request model for manual consolidation"""
    batch_size: Optional[int] = Field(default=None, description="Number of packets to consolidate")


class ConsolidateResponse(BaseModel):
    """Response model for consolidation"""
    success: bool
    packets_consolidated: int
    message: str
    updated_metrics: Dict[str, int]


# ============================================================================
# Lifespan Context Manager
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async lifespan context manager for FastAPI.
    Initializes and cleans up the AEME system.
    """
    global controller, router
    
    # Startup
    logger.info("Starting AEME system...")
    
    controller = EpistemicMemoryController(
        stm_capacity=3,  # Reduced from 10 - fills faster!
        mtm_capacity=500,
        consolidation_threshold=5,  # Reduced from 50 - consolidates faster!
        consolidation_interval_seconds=60.0,
        use_real_embeddings=True,
        use_llm_extraction=True  # Set to False if no OpenAI API key
    )
    
    router = UnifiedRetrievalRouter(controller)
    
    await controller.start()
    
    logger.info("✓ AEME system started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AEME system...")
    await controller.stop()
    logger.info("✓ AEME system stopped")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Autonomous Epistemic Memory Engine (AEME)",
    description="Three-tiered memory system with LLM-powered knowledge extraction",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Serve the frontend dashboard"""
    return FileResponse("index.html")


@app.get("/nexuslogo.png")
async def serve_logo():
    """Serve the logo image"""
    logo_path = os.path.join(BASE_DIR, "nexuslogo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    else:
        raise HTTPException(status_code=404, detail="Logo not found")


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_content(request: IngestRequest):
    """
    Ingest new content into the memory system.
    
    The content flows through: STM → MTM → LTM (with automatic consolidation)
    """
    try:
        # Create memory packet
        packet = MemoryPacket(
            content=request.content,
            metadata=request.metadata or {}
        )
        
        # Ingest into system
        await controller.ingest_packet(packet)
        
        # Get current metrics
        metrics = await controller.get_metrics()
        
        logger.info(f"Ingested packet {packet.packet_id}")
        
        return IngestResponse(
            success=True,
            packet_id=packet.packet_id,
            message="Content ingested successfully",
            current_metrics={
                "stm_size": metrics.short_term_size,
                "mtm_size": metrics.mid_term_size,
                "ltm_nodes": metrics.long_term_nodes,
                "ltm_edges": metrics.long_term_edges
            }
        )
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/api/query", response_model=QueryResponse)
async def query_memory(request: QueryRequest):
    """
    Query the memory system for relevant context.
    
    Performs hybrid retrieval across all three tiers.
    """
    try:
        # Perform unified retrieval
        result = await router.retrieve_context(
            query=request.query,
            stm_enabled=request.stm_enabled,
            mtm_enabled=request.mtm_enabled,
            ltm_enabled=request.ltm_enabled,
            mtm_top_k=request.mtm_top_k,
            mtm_threshold=request.mtm_threshold,
            ltm_max_hops=request.ltm_max_hops
        )
        
        logger.info(
            f"Query '{request.query}' returned {len(result.stm_results)} STM, "
            f"{len(result.mtm_results)} MTM, {len(result.ltm_results)} LTM results"
        )
        
        return QueryResponse(
            query=result.combined_context.split('\n')[0] if result.combined_context else request.query,
            combined_context=result.combined_context,
            stm_results=result.stm_results,
            mtm_results=result.mtm_results,
            ltm_results=result.ltm_results,
            metrics=result.metrics
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get current system metrics and statistics.
    
    Includes memory tier sizes, consolidation stats, and extraction performance.
    """
    try:
        metrics = await controller.get_metrics()
        extraction_stats = controller.get_extraction_statistics()
        
        return MetricsResponse(
            short_term_size=metrics.short_term_size,
            mid_term_size=metrics.mid_term_size,
            long_term_nodes=metrics.long_term_nodes,
            long_term_edges=metrics.long_term_edges,
            consolidations_performed=metrics.consolidations_performed,
            total_packets_processed=metrics.total_packets_processed,
            llm_extractions=metrics.llm_extractions,
            heuristic_extractions=metrics.heuristic_extractions,
            failed_extractions=metrics.failed_extractions,
            extraction_statistics=extraction_stats
        )
        
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@app.get("/api/graph", response_model=GraphData)
async def get_graph():
    """
    Get the current semantic graph structure for visualization.
    
    Returns nodes and edges in a format compatible with D3.js force layout.
    """
    try:
        async with controller.ltm.lock:
            graph = controller.ltm.graph
            
            # Extract nodes
            nodes = []
            for node_id in graph.nodes():
                node_data = graph.nodes[node_id]
                nodes.append({
                    "id": node_id,
                    "label": node_id.replace("_", " ").title(),
                    "type": node_data.get("type", "entity"),
                    "group": hash(node_id) % 5  # For color grouping
                })
            
            # Extract edges (links)
            links = []
            for source, target, edge_data in graph.edges(data=True):
                links.append({
                    "source": source,
                    "target": target,
                    "relation": edge_data.get("relation", "related_to"),
                    "weight": edge_data.get("weight", 1.0)
                })
            
            stats = {
                "num_nodes": graph.number_of_nodes(),
                "num_edges": graph.number_of_edges(),
                "density": (
                    graph.number_of_edges() / (graph.number_of_nodes() * (graph.number_of_nodes() - 1))
                    if graph.number_of_nodes() > 1 else 0
                )
            }
        
        return GraphData(nodes=nodes, links=links, stats=stats)
        
    except Exception as e:
        logger.error(f"Graph retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Graph retrieval failed: {str(e)}")


@app.post("/api/consolidate", response_model=ConsolidateResponse)
async def trigger_consolidation(request: ConsolidateRequest):
    """
    Manually trigger consolidation from MTM to LTM.
    
    Useful for forcing immediate knowledge graph updates.
    """
    try:
        packets_consolidated = await controller.consolidate_episodic_to_semantic(
            batch_size=request.batch_size
        )
        
        metrics = await controller.get_metrics()
        
        return ConsolidateResponse(
            success=True,
            packets_consolidated=packets_consolidated,
            message=f"Consolidated {packets_consolidated} packets into semantic graph",
            updated_metrics={
                "ltm_nodes": metrics.long_term_nodes,
                "ltm_edges": metrics.long_term_edges,
                "mtm_size": metrics.mid_term_size
            }
        )
        
    except Exception as e:
        logger.error(f"Consolidation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Consolidation failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "system": "AEME",
        "version": "1.0.0"
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
