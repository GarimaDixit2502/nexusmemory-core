"""
AEME - Memory Layers
====================
Three-tiered memory architecture: STM, MTM, LTM
"""

import time
import asyncio
import numpy as np
import networkx as nx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from models import MemoryPacket


class DecayParameters(BaseModel):
    """Configuration for episodic memory decay"""
    similarity_weight: float = 0.5
    recency_weight: float = 0.3
    frequency_weight: float = 0.2
    decay_halflife_hours: float = 24.0


class ShortTermBuffer:
    """FIFO rolling queue for immediate working memory"""
    
    def __init__(self, max_capacity: int = 10):
        self.max_capacity = max_capacity
        self.buffer: List[MemoryPacket] = []
        self.lock = asyncio.Lock()

    async def add(self, packet: MemoryPacket) -> Optional[MemoryPacket]:
        """Add packet, return evicted packet if full"""
        async with self.lock:
            evicted = None
            if len(self.buffer) >= self.max_capacity:
                evicted = self.buffer.pop(0)
            self.buffer.append(packet)
            return evicted

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Simple keyword search"""
        async with self.lock:
            results = []
            for p in self.buffer:
                if query.lower() in p.content.lower():
                    p.access_count += 1
                    p.last_accessed = time.time()
                    results.append({"packet": p, "score": 1.0, "tier": "STM"})
            return results


class MidTermEpisodicLayer:
    """Vector-based episodic memory with decay-weighted retrieval"""
    
    def __init__(
        self, 
        embedding_dim: int = 384, 
        max_capacity: int = 500, 
        decay_params: DecayParameters = None
    ):
        self.embedding_dim = embedding_dim
        self.max_capacity = max_capacity
        self.decay_params = decay_params or DecayParameters()
        self.packets: List[MemoryPacket] = []
        self.lock = asyncio.Lock()

    async def add(self, packet: MemoryPacket) -> Optional[MemoryPacket]:
        """Add packet with decay-based eviction if full"""
        async with self.lock:
            evicted = None
            if len(self.packets) >= self.max_capacity:
                # Evict lowest-scored packet
                query_embedding = packet.embedding or [0.0] * self.embedding_dim
                scores = [await self._calculate_score(p, query_embedding) for p in self.packets]
                min_idx = np.argmin(scores)
                evicted = self.packets.pop(min_idx)
            self.packets.append(packet)
            return evicted

    async def _calculate_score(
        self, 
        packet: MemoryPacket, 
        query_embedding: List[float]
    ) -> float:
        """
        Calculate decay-weighted relevance score.
        
        Combines: Cosine similarity + Temporal decay + Access frequency
        """
        if not packet.embedding:
            return 0.0
        
        # Cosine similarity
        dot_prod = np.dot(packet.embedding, query_embedding)
        norm_a = np.linalg.norm(packet.embedding)
        norm_b = np.linalg.norm(query_embedding)
        similarity = dot_prod / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0
        
        # Temporal decay (exponential)
        age_hours = (time.time() - packet.timestamp) / 3600.0
        decay = np.exp(-np.log(2) * age_hours / self.decay_params.decay_halflife_hours)
        
        # Frequency normalization
        freq = 1.0 - (1.0 / (1.0 + packet.access_count))
        
        # Weighted combination
        return (
            self.decay_params.similarity_weight * similarity +
            self.decay_params.recency_weight * decay +
            self.decay_params.frequency_weight * freq
        )

    async def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5, 
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant packets using decay-weighted similarity"""
        async with self.lock:
            if not self.packets:
                return []
            
            scored_results = []
            for p in self.packets:
                score = await self._calculate_score(p, query_embedding)
                if score >= threshold:
                    p.access_count += 1
                    p.last_accessed = time.time()
                    scored_results.append({
                        "packet": p, 
                        "score": float(score), 
                        "tier": "MTM"
                    })
            
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            return scored_results[:top_k]


class LongTermSemanticGraph:
    """NetworkX-powered semantic knowledge graph"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.lock = asyncio.Lock()

    async def add_triplet(
        self, 
        subject: str, 
        predicate: str, 
        obj: str, 
        weight: float = 1.0
    ):
        """Add entity-relationship triplet to graph"""
        async with self.lock:
            # Normalize entities
            s = str(subject).strip().lower().replace(" ", "_")
            o = str(obj).strip().lower().replace(" ", "_")
            p = str(predicate).strip().lower().replace(" ", "_")
            
            # Add nodes if they don't exist
            if not self.graph.has_node(s):
                self.graph.add_node(s, type="entity")
            if not self.graph.has_node(o):
                self.graph.add_node(o, type="entity")
            
            # Add or update edge
            if self.graph.has_edge(s, o):
                existing_weight = self.graph[s][o].get("weight", 1.0)
                self.graph[s][o]["weight"] = max(existing_weight, weight)
            else:
                self.graph.add_edge(s, o, relation=p, weight=weight)

    async def search_graph(
        self, 
        query_keywords: List[str], 
        max_hops: int = 2
    ) -> List[Dict[str, Any]]:
        """Multi-hop BFS traversal from query keywords"""
        async with self.lock:
            results = []
            visited_nodes = set()
            
            for keyword in query_keywords:
                clean_kw = keyword.strip().lower().replace(" ", "_")
                matched_nodes = [n for n in self.graph.nodes if clean_kw in n]
                
                for start_node in matched_nodes:
                    if start_node in visited_nodes:
                        continue
                    
                    queue = [(start_node, 0)]
                    local_visited = {start_node}
                    
                    while queue:
                        node, depth = queue.pop(0)
                        visited_nodes.add(node)
                        
                        for neighbor in self.graph.neighbors(node):
                            if neighbor not in local_visited and depth < max_hops:
                                local_visited.add(neighbor)
                                queue.append((neighbor, depth + 1))
                                edge_data = self.graph[node][neighbor]
                                results.append({
                                    "triplet": f"({node}) --[{edge_data['relation']}]--> ({neighbor})",
                                    "score": float(edge_data.get("weight", 1.0) / (depth + 1)),
                                    "tier": "LTM"
                                })
            return results
