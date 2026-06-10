"""
AEME - Retrieval Router
========================
Unified retrieval across all three memory tiers.
"""

import asyncio
import time
from typing import List, Dict, Any
from models import RetrievalResult


class UnifiedRetrievalRouter:
    """Hybrid search across STM, MTM, and LTM"""
    
    def __init__(self, controller):
        self.controller = controller

    async def retrieve_context(
        self, 
        query: str, 
        stm_enabled: bool = True,
        mtm_enabled: bool = True,
        ltm_enabled: bool = True,
        mtm_top_k: int = 5,
        mtm_threshold: float = 0.0,
        ltm_max_hops: int = 2
    ) -> RetrievalResult:
        """
        Perform unified context retrieval across all memory tiers.
        
        Args:
            query: Query string
            stm_enabled: Include STM results
            mtm_enabled: Include MTM results
            ltm_enabled: Include LTM results
            mtm_top_k: Number of MTM results
            mtm_threshold: Minimum similarity threshold
            ltm_max_hops: Maximum graph traversal depth
            
        Returns:
            RetrievalResult with combined context
        """
        start_time = time.time()
        
        # Get query embedding
        query_embedding = [0.0] * self.controller.embedding_dim
        if hasattr(self.controller, 'embedding_service') and self.controller.embedding_service:
            query_embedding = await self.controller.embedding_service.get_embedding(query)
        
        # Parallel retrieval from all tiers
        tasks = []
        
        if stm_enabled:
            tasks.append(self.controller.stm.search(query))
        else:
            tasks.append(self._empty_results())
        
        if mtm_enabled:
            tasks.append(
                self.controller.mtm.search(
                    query_embedding, 
                    top_k=mtm_top_k, 
                    threshold=mtm_threshold
                )
            )
        else:
            tasks.append(self._empty_results())
        
        if ltm_enabled:
            keywords = query.lower().split()
            tasks.append(
                self.controller.ltm.search_graph(
                    keywords, 
                    max_hops=ltm_max_hops
                )
            )
        else:
            tasks.append(self._empty_results())
        
        stm_res, mtm_res, ltm_res = await asyncio.gather(*tasks)
        
        # Build unified context
        context_parts = []
        
        if stm_res:
            context_parts.append("--- Short-Term Buffer Context ---")
            context_parts.extend([f"• {r['packet'].content}" for r in stm_res])
        
        if mtm_res:
            context_parts.append("--- Mid-Term Episodic Context ---")
            context_parts.extend([
                f"• [{r['score']:.2f}] {r['packet'].content}" 
                for r in mtm_res
            ])
        
        if ltm_res:
            context_parts.append("--- Long-Term Semantic Context ---")
            context_parts.extend([f"• {r['triplet']}" for r in ltm_res])
        
        latency = (time.time() - start_time) * 1000
        
        return RetrievalResult(
            combined_context="\n".join(context_parts),
            stm_results=[
                {"content": r['packet'].content, "score": r['score']} 
                for r in stm_res
            ],
            mtm_results=[
                {"content": r['packet'].content, "score": r['score']} 
                for r in mtm_res
            ],
            ltm_results=[
                {"triplet": r['triplet'], "score": r['score']} 
                for r in ltm_res
            ],
            metrics={
                "latency_ms": latency, 
                "total_items": len(stm_res) + len(mtm_res) + len(ltm_res)
            }
        )
    
    async def _empty_results(self):
        """Return empty results"""
        await asyncio.sleep(0)
        return []
