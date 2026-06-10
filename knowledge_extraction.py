"""
AEME - Knowledge Extraction Service
====================================
LLM-powered triplet extraction using OpenAI structured outputs.
"""

import asyncio
import re
import os
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from collections import Counter

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from models import MemoryPacket, KnowledgeTriplet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of knowledge extraction"""
    triplets: List[KnowledgeTriplet] = field(default_factory=list)
    packet_ids: List[str] = field(default_factory=list)
    extraction_method: str = "heuristic"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __len__(self) -> int:
        return len(self.triplets)


class KnowledgeExtractor:
    """LLM-powered knowledge extraction with heuristic fallback"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_retries: int = 3,
        timeout: float = 30.0,
        use_llm: bool = True
    ):
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.use_llm = use_llm
        
        # Statistics
        self._total_extractions = 0
        self._llm_extractions = 0
        self._heuristic_extractions = 0
        self._failed_extractions = 0
        
        # Initialize OpenAI client
        if self.use_llm:
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI library not installed. Falling back to heuristic extraction.")
                self.use_llm = False
                self.client = None
            else:
                api_key = api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("No OpenAI API key found. Falling back to heuristic extraction.")
                    self.use_llm = False
                    self.client = None
                else:
                    self.client = AsyncOpenAI(
                        api_key=api_key,
                        max_retries=max_retries,
                        timeout=timeout
                    )
                    logger.info(f"Initialized KnowledgeExtractor with {model} (LLM mode enabled)")
        else:
            self.client = None
            logger.info("Initialized KnowledgeExtractor (heuristic mode only)")
    
    async def extract_from_packet(
        self,
        packet: MemoryPacket,
        max_triplets: int = 10
    ) -> ExtractionResult:
        """Extract knowledge triplets from a single packet"""
        self._total_extractions += 1
        
        if self.use_llm and self.client is not None:
            try:
                result = await self._extract_with_llm(packet.content, max_triplets)
                
                # Add source packet ID
                for triplet in result.triplets:
                    triplet.source_packet_id = packet.packet_id
                
                result.packet_ids = [packet.packet_id]
                result.extraction_method = "llm"
                self._llm_extractions += 1
                
                logger.debug(f"LLM extracted {len(result.triplets)} triplets from packet {packet.packet_id}")
                return result
                
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}. Falling back to heuristic.")
                self._failed_extractions += 1
        
        # Fallback to heuristic
        result = self._extract_with_heuristics(packet.content, max_triplets)
        
        for triplet in result.triplets:
            triplet.source_packet_id = packet.packet_id
        
        result.packet_ids = [packet.packet_id]
        result.extraction_method = "heuristic"
        self._heuristic_extractions += 1
        
        return result
    
    async def extract_from_packets(
        self,
        packets: List[MemoryPacket],
        max_triplets_per_packet: int = 5
    ) -> ExtractionResult:
        """Extract knowledge from multiple packets efficiently"""
        tasks = [
            self.extract_from_packet(packet, max_triplets_per_packet)
            for packet in packets
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined = ExtractionResult()
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Extraction failed: {result}")
                continue
            
            combined.triplets.extend(result.triplets)
            combined.packet_ids.extend(result.packet_ids)
        
        # Deduplicate
        combined.triplets = self._deduplicate_triplets(combined.triplets)
        
        combined.extraction_method = (
            "llm" if self._llm_extractions > self._heuristic_extractions
            else "heuristic"
        )
        combined.metadata = {
            'total_packets': len(packets),
            'llm_count': self._llm_extractions,
            'heuristic_count': self._heuristic_extractions
        }
        
        logger.info(f"Extracted {len(combined.triplets)} unique triplets from {len(packets)} packets")
        
        return combined
    
    async def _extract_with_llm(self, text: str, max_triplets: int = 10) -> ExtractionResult:
        """Extract using OpenAI structured outputs"""
        
        system_prompt = """You are a knowledge extraction expert. Extract entity-relationship triplets from text.

Guidelines:
1. Extract triplets as (Subject, Predicate, Object)
2. Normalize to lowercase with underscores
3. Use clear, semantic predicates (is_subset_of, uses, enables, etc.)
4. Focus on factual relationships
5. Return up to {max_triplets} most important triplets

Examples:
- "ML is a subset of AI" → (machine_learning, is_subset_of, artificial_intelligence)
- "Neural nets use backprop" → (neural_networks, use, backpropagation)"""

        user_prompt = f"""Extract knowledge triplets from this text:

{text}

Return JSON with this exact structure:
{{
  "triplets": [
    {{"subject": "entity1", "predicate": "relationship", "object": "entity2", "confidence": 0.95}}
  ]
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt.format(max_triplets=max_triplets)},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse response
            import json
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Create KnowledgeTriplet objects using 'obj' field
            triplets = []
            for item in data.get("triplets", []):
                try:
                    # CRITICAL: Use 'obj' field to match models.py
                    triplet = KnowledgeTriplet(
                        subject=item["subject"],
                        predicate=item["predicate"],
                        obj=item["object"],  # API returns 'object', we map to 'obj'
                        confidence=item.get("confidence", 0.9)
                    )
                    triplets.append(triplet)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse triplet: {item}, error: {e}")
                    continue
            
            result = ExtractionResult(triplets=triplets)
            result.metadata = {
                'model': self.model,
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
            
            return result
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            raise
    
    def _extract_with_heuristics(self, text: str, max_triplets: int = 10) -> ExtractionResult:
        """Fallback heuristic extraction using patterns"""
        
        text_lower = text.lower()
        triplets = []
        
        # Pattern matching for common relationships
        patterns = [
            (r'(\w+(?:\s+\w+){0,2})\s+is\s+a\s+(?:type\s+of\s+)?(\w+(?:\s+\w+){0,2})', 'is_type_of'),
            (r'(\w+(?:\s+\w+){0,2})\s+is\s+(?:a\s+)?subset\s+of\s+(\w+(?:\s+\w+){0,2})', 'is_subset_of'),
            (r'(\w+(?:\s+\w+){0,2})\s+uses?\s+(\w+(?:\s+\w+){0,2})', 'uses'),
            (r'(\w+(?:\s+\w+){0,2})\s+requires?\s+(\w+(?:\s+\w+){0,2})', 'requires'),
            (r'(\w+(?:\s+\w+){0,2})\s+enables?\s+(\w+(?:\s+\w+){0,2})', 'enables'),
            (r'(\w+(?:\s+\w+){0,2})\s+learns?\s+from\s+(\w+(?:\s+\w+){0,2})', 'learns_from'),
            (r'(\w+(?:\s+\w+){0,2})\s+processes?\s+(\w+(?:\s+\w+){0,2})', 'processes'),
            (r'(\w+(?:\s+\w+){0,2})\s+and\s+(\w+(?:\s+\w+){0,2})', 'related_to'),
        ]
        
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'this', 'that'
        }
        
        for pattern, predicate in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if len(match) == 2:
                    subject, obj = match
                    subject = subject.strip()
                    obj = obj.strip()
                    
                    if (len(subject) > 2 and len(obj) > 2 and
                        subject not in stopwords and obj not in stopwords and
                        subject != obj):
                        
                        # CRITICAL: Create with 'obj' field
                        triplet = KnowledgeTriplet(
                            subject=subject,
                            predicate=predicate,
                            obj=obj,
                            confidence=0.6
                        )
                        triplets.append(triplet)
        
        # Deduplicate and limit
        triplets = self._deduplicate_triplets(triplets)[:max_triplets]
        
        return ExtractionResult(
            triplets=triplets,
            metadata={'method': 'heuristic'}
        )
    
    def _deduplicate_triplets(self, triplets: List[KnowledgeTriplet]) -> List[KnowledgeTriplet]:
        """Remove duplicates, keeping highest confidence"""
        seen = {}
        
        for triplet in triplets:
            key = (triplet.subject, triplet.predicate, triplet.obj)
            
            if key not in seen or triplet.confidence > seen[key].confidence:
                seen[key] = triplet
        
        return list(seen.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get extraction statistics"""
        return {
            'total_extractions': self._total_extractions,
            'llm_extractions': self._llm_extractions,
            'heuristic_extractions': self._heuristic_extractions,
            'failed_extractions': self._failed_extractions,
            'llm_success_rate': (
                self._llm_extractions / self._total_extractions
                if self._total_extractions > 0 else 0
            ),
            'use_llm_enabled': self.use_llm,
            'model': self.model if self.use_llm else None
        }


# Global singleton
_extractor = None


def get_knowledge_extractor(
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
    use_llm: bool = True
) -> KnowledgeExtractor:
    """Get or create global knowledge extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = KnowledgeExtractor(
            api_key=api_key,
            model=model,
            use_llm=use_llm
        )
    return _extractor
