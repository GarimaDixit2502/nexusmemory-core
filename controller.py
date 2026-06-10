"""
AEME - Controller
=================
Main orchestrator for the three-tiered memory system.
"""

import asyncio
import time
import logging
import numpy as np
from typing import List, Optional, Dict, Any

from models import MemoryPacket, SystemMetrics
from memory_layers import ShortTermBuffer, MidTermEpisodicLayer, LongTermSemanticGraph
from embedding_service import get_embedding_service, get_embedding_dimension
from knowledge_extraction import get_knowledge_extractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EpistemicMemoryController:
    """Main controller for the three-tiered memory system"""
    
    def __init__(
        self,
        stm_capacity: int = 10,
        mtm_capacity: int = 500,
        embedding_dim: Optional[int] = None,
        consolidation_threshold: int = 50,
        consolidation_interval_seconds: float = 30.0,
        use_real_embeddings: bool = True,
        use_llm_extraction: bool = True,
        openai_api_key: Optional[str] = None,
        extraction_model: str = "gpt-4o-mini"
    ):
        self.use_real_embeddings = use_real_embeddings
        self.use_llm_extraction = use_llm_extraction
        
        # Initialize embedding service
        if self.use_real_embeddings:
            self.embedding_service = get_embedding_service()
            self.embedding_dim = get_embedding_dimension()
            logger.info(f"Using real embeddings (dimension: {self.embedding_dim})")
        else:
            self.embedding_service = None
            self.embedding_dim = embedding_dim or 384
            logger.info(f"Using mock embeddings (dimension: {self.embedding_dim})")
        
        # Initialize knowledge extractor
        self.knowledge_extractor = get_knowledge_extractor(
            api_key=openai_api_key,
            model=extraction_model,
            use_llm=use_llm_extraction
        )
        
        if use_llm_extraction:
            logger.info(f"Using LLM knowledge extraction with {extraction_model}")
        else:
            logger.info("Using heuristic knowledge extraction")
        
        # Initialize memory tiers
        self.stm = ShortTermBuffer(max_capacity=stm_capacity)
        self.mtm = MidTermEpisodicLayer(
            embedding_dim=self.embedding_dim,
            max_capacity=mtm_capacity
        )
        self.ltm = LongTermSemanticGraph()
        
        self.consolidation_threshold = consolidation_threshold
        self.consolidation_interval = consolidation_interval_seconds
        
        self.metrics = SystemMetrics()
        self._running = False
        self._consolidation_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        logger.info(
            f"Initialized EpistemicMemoryController "
            f"(STM={stm_capacity}, MTM={mtm_capacity}, "
            f"consolidation_threshold={consolidation_threshold})"
        )
    
    async def start(self) -> None:
        """Start background consolidation tasks"""
        if self._running:
            logger.warning("Controller already running")
            return
        
        # Initialize embedding service
        if self.use_real_embeddings and self.embedding_service:
            await self.embedding_service.initialize()
        
        self._running = True
        self._consolidation_task = asyncio.create_task(
            self._background_consolidation_loop()
        )
        logger.info("Started background consolidation loop")
    
    async def stop(self) -> None:
        """Stop background tasks gracefully"""
        if not self._running:
            return
        
        self._running = False
        
        if self._consolidation_task:
            self._consolidation_task.cancel()
            try:
                await self._consolidation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped controller")
    
    async def ingest_packet(self, packet: MemoryPacket) -> None:
        """Ingest a new memory packet"""
        evicted = await self.stm.add(packet)
        
        if evicted is not None:
            await self._promote_to_mtm(evicted)
        
        async with self._lock:
            self.metrics.total_packets_processed += 1
            self.metrics.short_term_size = len(self.stm.buffer)
    
    async def _promote_to_mtm(self, packet: MemoryPacket) -> None:
        """Promote packet from STM to MTM"""
        # Generate embedding if missing
        if packet.embedding is None:
            if self.use_real_embeddings and self.embedding_service:
                packet.embedding = await self.embedding_service.get_embedding(packet.content)
                logger.debug(f"Generated real embedding for packet {packet.packet_id}")
            else:
                # Mock embedding
                np.random.seed(hash(packet.content) % (2**32))
                embedding = np.random.randn(self.embedding_dim).astype(float)
                embedding = embedding / (np.linalg.norm(embedding) + 1e-10)
                packet.embedding = embedding.tolist()
        
        evicted_packet = await self.mtm.add(packet)
        
        async with self._lock:
            self.metrics.mid_term_size = len(self.mtm.packets)
        
        # Check consolidation threshold
        mtm_size = len(self.mtm.packets)
        if mtm_size >= self.consolidation_threshold:
            logger.info(f"MTM threshold reached ({mtm_size}), triggering consolidation")
            await self.consolidate_episodic_to_semantic()
    
    async def _background_consolidation_loop(self) -> None:
        """Background consolidation task"""
        while self._running:
            try:
                await asyncio.sleep(self.consolidation_interval)
                
                mtm_size = len(self.mtm.packets)
                if mtm_size >= self.consolidation_threshold:
                    logger.info("Background consolidation triggered")
                    await self.consolidate_episodic_to_semantic()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in consolidation loop: {e}", exc_info=True)
    
    async def consolidate_episodic_to_semantic(self, batch_size: Optional[int] = None) -> int:
        """Consolidate MTM packets into LTM graph using LLM extraction"""
        
        if batch_size is None:
            batch_size = max(1, self.consolidation_threshold // 2)
        
        # Get packets from MTM
        async with self.mtm.lock:
            all_packets = list(self.mtm.packets)
        
        if len(all_packets) == 0:
            logger.debug("No packets in MTM to consolidate")
            return 0
        
        # Sample oldest packets
        packets_to_consolidate = sorted(all_packets, key=lambda p: p.timestamp)[:batch_size]
        
        logger.info(f"Starting consolidation of {len(packets_to_consolidate)} packets")
        
        # Extract knowledge
        try:
            extraction_result = await self.knowledge_extractor.extract_from_packets(
                packets_to_consolidate,
                max_triplets_per_packet=5
            )
            
            logger.info(
                f"Extracted {len(extraction_result.triplets)} triplets "
                f"using {extraction_result.extraction_method} method"
            )
            
            # Update metrics
            async with self._lock:
                if extraction_result.extraction_method == "llm":
                    self.metrics.llm_extractions += len(packets_to_consolidate)
                else:
                    self.metrics.heuristic_extractions += len(packets_to_consolidate)
            
        except Exception as e:
            logger.error(f"Knowledge extraction failed: {e}")
            async with self._lock:
                self.metrics.failed_extractions += len(packets_to_consolidate)
            return 0
        
        # Add triplets to graph
        entities_added = set()
        edges_added = 0
        
        for triplet in extraction_result.triplets:
            try:
                await self.ltm.add_triplet(
                    subject=triplet.subject,
                    predicate=triplet.predicate,
                    obj=triplet.obj,
                    weight=triplet.confidence
                )
                
                entities_added.add(triplet.subject)
                entities_added.add(triplet.obj)
                edges_added += 1
                
            except Exception as e:
                logger.warning(f"Failed to add triplet: {e}")
        
        # Update metrics
        async with self._lock:
            self.metrics.consolidations_performed += 1
            async with self.ltm.lock:
                self.metrics.long_term_nodes = self.ltm.graph.number_of_nodes()
                self.metrics.long_term_edges = self.ltm.graph.number_of_edges()
        
        logger.info(
            f"Consolidation complete: {len(entities_added)} entities, "
            f"{edges_added} edges added (method: {extraction_result.extraction_method})"
        )
        
        return len(packets_to_consolidate)
    
    async def get_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        async with self._lock:
            self.metrics.short_term_size = len(self.stm.buffer)
            self.metrics.mid_term_size = len(self.mtm.packets)
            
            async with self.ltm.lock:
                self.metrics.long_term_nodes = self.ltm.graph.number_of_nodes()
                self.metrics.long_term_edges = self.ltm.graph.number_of_edges()
            
            return SystemMetrics(**self.metrics.model_dump())
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """Get knowledge extraction statistics"""
        return self.knowledge_extractor.get_statistics()
    
    async def force_consolidation(self) -> int:
        """Force immediate consolidation"""
        logger.info("Forcing consolidation")
        return await self.consolidate_episodic_to_semantic(batch_size=None)
