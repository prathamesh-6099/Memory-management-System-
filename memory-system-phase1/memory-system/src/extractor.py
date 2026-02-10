"""
Memory Extraction - Phase 1 (Stage 1 & 2 only)
Heuristic filter + Simple classifier (no LLM yet)
"""

import logging
import re
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .config import (
    SENSORY_FILTER_THRESHOLD,
    EXTRACTION_CLASSIFIER_THRESHOLD,
    HEURISTIC_WEIGHTS,
    EXTRACTION_KEYWORDS,
    MEMORY_TYPES,
)

logger = logging.getLogger(__name__)


class MemoryExtractor:
    """Extracts memories from user messages using heuristic + simple classifier"""

    def __init__(self):
        self.extraction_count = 0

    def should_extract(self, message: str) -> Tuple[bool, float]:
        """
        Stage 1: Sensory Memory - Fast heuristic filter
        
        Filters out ~60% of turns before expensive processing:
        - Greetings ("hi", "hello")
        - Acknowledgments ("ok", "thanks")
        - Filler ("um", "uh")
        
        Args:
            message: User's message text
        
        Returns:
            (should_process, score) - True if worth extracting
        """
        message_lower = message.lower().strip()
        
        # Immediate reject: Very short or common greetings
        if len(message_lower) < 5:
            return False, 0.0
        
        greetings = ["hi", "hello", "hey", "thanks", "ok", "okay", "cool", "nice"]
        if message_lower in greetings:
            return False, 0.0
        
        # Calculate heuristic score
        score = 0.0
        
        # Length score (normalized)
        length_score = min(len(message) / 100, 1.0)
        score += length_score * HEURISTIC_WEIGHTS["length"]
        
        # Keyword score
        keyword_matches = 0
        total_keywords = sum(len(kws) for kws in EXTRACTION_KEYWORDS.values())
        
        for keyword_list in EXTRACTION_KEYWORDS.values():
            for keyword in keyword_list:
                if keyword in message_lower:
                    keyword_matches += 1
        
        keyword_score = min(keyword_matches / 3, 1.0)  # Normalize to 3 matches
        score += keyword_score * HEURISTIC_WEIGHTS["keywords"]
        
        # Question score
        question_score = 1.0 if "?" in message else 0.0
        score += question_score * HEURISTIC_WEIGHTS["question"]
        
        # Specificity score (presence of numbers, proper nouns, specific details)
        specificity_indicators = [
            r'\d+',  # Numbers
            r'[A-Z][a-z]+',  # Capitalized words (potential proper nouns)
            r'\b(am|pm|AM|PM)\b',  # Time indicators
            r'@',  # Email/mentions
        ]
        
        specificity_matches = sum(
            1 for pattern in specificity_indicators 
            if re.search(pattern, message)
        )
        specificity_score = min(specificity_matches / 3, 1.0)
        score += specificity_score * HEURISTIC_WEIGHTS["specificity"]
        
        should_process = score >= SENSORY_FILTER_THRESHOLD
        
        logger.debug(
            f"Heuristic filter: score={score:.2f}, "
            f"threshold={SENSORY_FILTER_THRESHOLD}, "
            f"process={should_process}"
        )
        
        return should_process, score

    def classify_and_extract(self, message: str, turn_number: int) -> List[Dict]:
        """
        Stage 2: Simple rule-based classifier
        
        Identifies memory type and extracts key-value pairs.
        Phase 1 uses pattern matching; Phase 3 will add LLM extraction.
        
        Args:
            message: User's message text
            turn_number: Current turn number
        
        Returns:
            List of extracted memory dictionaries
        """
        memories = []
        message_lower = message.lower()
        timestamp = datetime.now().timestamp()
        
        # Pattern-based extraction for each memory type
        
        # PREFERENCE patterns
        preference_patterns = [
            (r"i (?:prefer|like|love|enjoy) (.+)", "preference", 0.8),
            (r"my favorite (.+) is (.+)", "favorite_{}", 0.9),
            (r"i (?:always|usually) (.+)", "habitual_behavior", 0.7),
            (r"i (?:hate|dislike|avoid) (.+)", "negative_preference", 0.8),
        ]
        
        for pattern, key_template, confidence in preference_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                if "{}" in key_template:
                    key = key_template.format(match.group(1).strip())
                    value = match.group(2).strip()
                else:
                    key = key_template
                    value = match.group(1).strip()
                
                memories.append(self._create_memory(
                    memory_type="preference",
                    key=key,
                    value=value,
                    confidence=confidence,
                    turn_number=turn_number,
                    timestamp=timestamp,
                    source_text=message,
                ))
        
        # CONSTRAINT patterns
        constraint_patterns = [
            (r"i (?:can't|cannot|won't) (.+)", "cannot", 0.9),
            (r"i (?:must|have to|need to) (.+)", "must", 0.9),
            (r"i'm (?:allergic to|allergic) (.+)", "allergy", 1.0),
            (r"(?:don't|do not) (.+)", "restriction", 0.7),
        ]
        
        for pattern, key_template, confidence in constraint_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                memories.append(self._create_memory(
                    memory_type="constraint",
                    key=key_template,
                    value=match.group(1).strip(),
                    confidence=confidence,
                    turn_number=turn_number,
                    timestamp=timestamp,
                    source_text=message,
                ))
        
        # ENTITY patterns
        entity_patterns = [
            (r"my (\w+) is (?:named |called )?(\w+)", "my_{}", 0.8),
            (r"my name is (\w+)", "user_name", 0.95),
            (r"i work (?:at|for) (.+?)(?:\.|$)", "employer", 0.8),
            (r"i live in (.+?)(?:\.|$)", "location", 0.85),
        ]
        
        for pattern, key_template, confidence in entity_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                if "{}" in key_template:
                    key = key_template.format(match.group(1).strip())
                    value = match.group(2).strip() if len(match.groups()) > 1 else match.group(1).strip()
                else:
                    key = key_template
                    value = match.group(1).strip()
                
                memories.append(self._create_memory(
                    memory_type="entity",
                    key=key,
                    value=value,
                    confidence=confidence,
                    turn_number=turn_number,
                    timestamp=timestamp,
                    source_text=message,
                ))
        
        # COMMITMENT patterns
        commitment_patterns = [
            (r"i(?:'ll| will) (.+?) by (.+?)(?:\.|$)", "deadline", 0.85),
            (r"i promise (?:to )?(.+)", "promise", 0.9),
            (r"i'm committed to (.+)", "commitment", 0.9),
        ]
        
        for pattern, key_template, confidence in commitment_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                memories.append(self._create_memory(
                    memory_type="commitment",
                    key=key_template,
                    value=match.group(1).strip(),
                    confidence=confidence,
                    turn_number=turn_number,
                    timestamp=timestamp,
                    source_text=message,
                ))
        
        # INSTRUCTION patterns
        instruction_patterns = [
            (r"(?:always|remember to) (.+)", "always", 0.8),
            (r"(?:never|don't ever) (.+)", "never", 0.8),
            (r"make sure (?:to )?(.+)", "make_sure", 0.75),
        ]
        
        for pattern, key_template, confidence in instruction_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                memories.append(self._create_memory(
                    memory_type="instruction",
                    key=key_template,
                    value=match.group(1).strip(),
                    confidence=confidence,
                    turn_number=turn_number,
                    timestamp=timestamp,
                    source_text=message,
                ))
        
        if memories:
            logger.info(f"Extracted {len(memories)} memories from turn {turn_number}")
        
        return memories

    def _create_memory(
        self,
        memory_type: str,
        key: str,
        value: str,
        confidence: float,
        turn_number: int,
        timestamp: float,
        source_text: str,
    ) -> Dict:
        """Create a structured memory record"""
        return {
            "memory_id": f"mem_{uuid.uuid4().hex[:8]}",
            "type": memory_type,
            "key": key,
            "value": value,
            "confidence": confidence,
            "turn_number": turn_number,
            "timestamp": timestamp,
            "source_text": source_text,
        }

    def extract(self, message: str, turn_number: int) -> List[Dict]:
        """
        Full extraction pipeline (Phase 1 version)
        
        Args:
            message: User's message
            turn_number: Current turn number
        
        Returns:
            List of extracted memories (empty if filtered out)
        """
        # Stage 1: Sensory filter
        should_process, heuristic_score = self.should_extract(message)
        
        if not should_process:
            logger.debug(f"Turn {turn_number}: Filtered out by sensory layer")
            return []
        
        # Stage 2: Classify and extract
        memories = self.classify_and_extract(message, turn_number)
        
        # Filter by classifier confidence
        high_confidence_memories = [
            m for m in memories 
            if m['confidence'] >= EXTRACTION_CLASSIFIER_THRESHOLD
        ]
        
        logger.info(
            f"Turn {turn_number}: Extracted {len(high_confidence_memories)}/{len(memories)} "
            f"high-confidence memories (heuristic={heuristic_score:.2f})"
        )
        
        self.extraction_count += len(high_confidence_memories)
        
        return high_confidence_memories
