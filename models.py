"""
AEME - Data Models
==================
All data structures for the three-tiered memory system.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class MemoryPacket(BaseModel):
    """Core memory unit flowing through the system"""
    packet_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = Field(default_factory=time.time)


class GraphNode(BaseModel):
    """Entity node in semantic graph"""
    id: str
    type: str = "entity"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Relationship edge in semantic graph"""
    source: str
    target: str
    relation: str
    weight: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    """Results from unified retrieval across all tiers"""
    combined_context: str
    stm_results: List[Dict[str, Any]] = Field(default_factory=list)
    mtm_results: List[Dict[str, Any]] = Field(default_factory=list)
    ltm_results: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeTriplet(BaseModel):
    """Extracted entity-relationship triplet"""
    subject: str
    predicate: str
    obj: str  # IMPORTANT: Using 'obj' not 'object' to avoid Python keyword
    confidence: float = 1.0
    source_packet_id: Optional[str] = None


class ConsolidationBatch(BaseModel):
    """Batch of packets for consolidation"""
    packets: List[MemoryPacket]
    extracted_triplets: List[KnowledgeTriplet] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class SystemMetrics(BaseModel):
    """System-wide performance metrics"""
    short_term_size: int = 0
    mid_term_size: int = 0
    long_term_nodes: int = 0
    long_term_edges: int = 0
    consolidations_performed: int = 0
    total_packets_processed: int = 0
    llm_extractions: int = 0
    heuristic_extractions: int = 0
    failed_extractions: int = 0
