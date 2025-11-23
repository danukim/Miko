"""
Enhanced Memory System for Mitsuha AI
Provides intelligent memory management with temporal awareness, importance scoring, and repetition detection.

Author: DogeLord
Date: 2025-11-22
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import numpy as np


class ImportanceScorer:
    """
    Analyzes message content and assigns importance scores (0.0-1.0).
    Higher scores indicate more important memories that should be retained long-term.
    """
    
    def __init__(self):
        # Keywords for different importance categories
        self.high_importance_keywords = [
            'my name is', 'i am', 'my favorite', 'i like', 'i love', 'i hate',
            'my birthday', 'i work', 'i live', 'remember that', 'my family',
            'my friend', 'my pet', 'important to me', 'never forget',
            'i prefer', 'my hobby', 'my job', 'i study', 'my school'
        ]
        
        self.medium_high_keywords = [
            'sad', 'happy', 'excited', 'angry', 'feel', 'important',
            'significant', 'remember', 'frustrated', 'worried', 'nervous',
            'proud', 'grateful', 'love', 'hate', 'fear', 'hope'
        ]
        
        self.medium_keywords = [
            'task', 'todo', 'remind', 'schedule', 'need to', 'should',
            'please', 'can you', 'would you', 'could you', 'help me',
            'working on', 'planning', 'going to', 'will do'
        ]
        
        self.low_keywords = [
            'just', 'yeah', 'okay', 'interesting', 'cool', 'nice',
            'i see', 'i think', 'maybe', 'perhaps', 'probably',
            'sort of', 'kind of', 'i guess'
        ]
        
        self.very_low_keywords = [
            'hello', 'hi', 'hey', 'goodbye', 'bye', 'see you',
            'how are you', 'good morning', 'good night', 'good afternoon',
            'how\'s it going', 'what\'s up', 'thanks', 'thank you',
            'you\'re welcome', 'no problem'
        ]
    
    def score_message(self, role: str, content: str) -> Tuple[float, List[str]]:
        """
        Calculate importance score for a message.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            
        Returns:
            Tuple of (importance_score, tags)
        """
        content_lower = content.lower()
        tags = []
        
        # Check for keyword matches
        high_score = sum(1 for kw in self.high_importance_keywords if kw in content_lower)
        medium_high_score = sum(1 for kw in self.medium_high_keywords if kw in content_lower)
        medium_score = sum(1 for kw in self.medium_keywords if kw in content_lower)
        low_score = sum(1 for kw in self.low_keywords if kw in content_lower)
        very_low_score = sum(1 for kw in self.very_low_keywords if kw in content_lower)
        
        # Calculate base importance
        if high_score > 0:
            importance = 0.85 + min(high_score * 0.05, 0.15)  # 0.85-1.0
            tags.append('personal_fact')
        elif medium_high_score > 0:
            importance = 0.65 + min(medium_high_score * 0.05, 0.15)  # 0.65-0.8
            tags.append('emotional')
        elif medium_score > 0:
            importance = 0.5 + min(medium_score * 0.05, 0.15)  # 0.5-0.65
            tags.append('task')
        elif very_low_score > 0:
            importance = 0.1 + min(very_low_score * 0.02, 0.08)  # 0.1-0.18
            tags.append('greeting')
        elif low_score > 0:
            importance = 0.25 + min(low_score * 0.05, 0.15)  # 0.25-0.4
            tags.append('chitchat')
        else:
            # Default for neutral messages
            importance = 0.35
            tags.append('general')
        
        # Adjust based on role
        if role == 'assistant':
            # Assistant responses are generally less important unless high-importance
            if importance < 0.7:
                importance *= 0.8
            tags.append('response')
        
        # Check for specific patterns
        if re.search(r'(wave|thumbs-up|nodding|shaking head|clap)', content_lower):
            tags.append('gesture')
            importance = max(importance, 0.2)  # Gestures are low importance
        
        # Check for questions
        if '?' in content:
            tags.append('question')
        
        # Length bonus for detailed messages (likely more important)
        word_count = len(content.split())
        if word_count > 50:
            importance += 0.05
        elif word_count > 100:
            importance += 0.1
        
        # Cap at 1.0
        importance = min(importance, 1.0)
        
        return importance, tags


class EnhancedMemory:
    """
    Enhanced memory system that wraps vectordb.Memory with additional capabilities:
    - Temporal awareness and decay
    - Importance scoring
    - Smart retrieval combining similarity, recency, and importance
    - Repetition detection
    """
    
    def __init__(self, base_memory, conversation_file: str = "conversation.jsonl"):
        """
        Initialize enhanced memory system.
        
        Args:
            base_memory: Instance of vectordb.Memory
            conversation_file: Path to conversation.jsonl file
        """
        self.base_memory = base_memory
        self.conversation_file = conversation_file
        self.importance_scorer = ImportanceScorer()
        self.messages_cache = []  # Cache for loaded messages with metadata
        
        # Load and process existing conversation
        self._load_and_process_conversation()
    
    def _load_and_process_conversation(self):
        """Load conversation.jsonl and ensure all messages have importance scores."""
        try:
            with open(self.conversation_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            updated = False
            processed_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    message = json.loads(line)
                    
                    # Add importance and tags if missing (backward compatibility)
                    if 'importance' not in message:
                        importance, tags = self.importance_scorer.score_message(
                            message.get('role', 'user'),
                            message.get('content', '')
                        )
                        message['importance'] = importance
                        message['tags'] = tags
                        updated = True
                    
                    if 'tags' not in message:
                        message['tags'] = []
                        updated = True
                    
                    processed_lines.append(message)
                    self.messages_cache.append(message)
                    
                except json.JSONDecodeError:
                    continue
            
            # If we added importance scores, rewrite the file
            if updated:
                with open(self.conversation_file, 'w', encoding='utf-8') as f:
                    for msg in processed_lines:
                        f.write(json.dumps(msg, ensure_ascii=False) + '\n')
                        
        except FileNotFoundError:
            # File doesn't exist yet, will be created on first save
            pass
    
    def save_with_metadata(self, message_data: Dict[str, Any]):
        """
        Save message with calculated importance score and tags.
        
        Args:
            message_data: Dict with keys: role, date, time, content
        """
        # Calculate importance and tags
        importance, tags = self.importance_scorer.score_message(
            message_data.get('role', 'user'),
            message_data.get('content', '')
        )
        
        # Add metadata
        message_data['importance'] = importance
        message_data['tags'] = tags
        
        # Save to conversation.jsonl
        with open(self.conversation_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(message_data, ensure_ascii=False) + '\n')
        
        # Update cache
        self.messages_cache.append(message_data)
        
        # Save to vectordb
        self.base_memory.save([json.dumps(message_data, ensure_ascii=False)])
    
    def _parse_datetime(self, date_str: str, time_str: str) -> Optional[datetime]:
        """
        Parse date and time strings to datetime object.
        Handles both MM/DD/YYYY and YYYY-MM-DD formats.
        
        Args:
            date_str: Date string
            time_str: Time string in HH:MM:SS format
            
        Returns:
            datetime object or None if parsing fails
        """
        try:
            # Try MM/DD/YYYY format
            if '/' in date_str:
                dt = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %H:%M:%S")
            # Try YYYY-MM-DD format
            else:
                dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            return dt
        except (ValueError, AttributeError):
            return None
    
    def calculate_temporal_factor(self, message_time: datetime, current_time: datetime) -> float:
        """
        Calculate temporal relevance factor (0.0-1.0) based on message age.
        
        More recent messages get higher scores:
        - Last hour: 1.0
        - Last 24 hours: 0.8-1.0
        - Last week: 0.5-0.8
        - Last month: 0.3-0.5
        - Older: 0.1-0.3
        
        Args:
            message_time: When the message was created
            current_time: Current time
            
        Returns:
            Temporal factor between 0.0 and 1.0
        """
        time_diff = current_time - message_time
        hours = time_diff.total_seconds() / 3600
        
        if hours <= 1:
            return 1.0
        elif hours <= 24:
            # Linear decay from 1.0 to 0.8 over 24 hours
            return 1.0 - (hours - 1) * 0.2 / 23
        elif hours <= 168:  # 1 week
            # Linear decay from 0.8 to 0.5 over 1 week
            return 0.8 - (hours - 24) * 0.3 / 144
        elif hours <= 720:  # 30 days
            # Linear decay from 0.5 to 0.3 over 1 month
            return 0.5 - (hours - 168) * 0.2 / 552
        else:
            # Very old messages: 0.1 to 0.3 based on age
            days = hours / 24
            if days <= 90:
                return 0.3 - (days - 30) * 0.2 / 60
            else:
                return 0.1
    
    def search_smart(self, query: str, current_time: datetime, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve memories using combined scoring:
        - Vector similarity (50%)
        - Temporal decay (30%)
        - Importance weighting (20%)
        
        Args:
            query: Search query
            current_time: Current datetime
            top_n: Number of results to return
            
        Returns:
            List of message dicts with metadata, sorted by combined score
        """
        # Get vector similarity results from base memory
        # Get more than needed to have candidates for reranking
        vector_results = self.base_memory.search(query, top_n=min(top_n * 3, 20))
        
        scored_results = []
        
        for result in vector_results:
            try:
                # Parse the message from chunk
                message = json.loads(result['chunk'])
                
                # Get vector similarity score (normalized to 0-1)
                similarity_score = result.get('score', 0.5)
                
                # Get importance score
                importance_score = message.get('importance', 0.4)
                
                # Calculate temporal factor
                message_time = self._parse_datetime(
                    message.get('date', ''),
                    message.get('time', '')
                )
                
                if message_time:
                    temporal_factor = self.calculate_temporal_factor(message_time, current_time)
                else:
                    temporal_factor = 0.3  # Default for unparseable dates
                
                # Combined score: 50% similarity + 30% temporal + 20% importance
                combined_score = (
                    0.5 * similarity_score +
                    0.3 * temporal_factor +
                    0.2 * importance_score
                )
                
                scored_results.append({
                    'message': message,
                    'similarity_score': similarity_score,
                    'temporal_factor': temporal_factor,
                    'importance_score': importance_score,
                    'combined_score': combined_score,
                    'chunk': result['chunk']  # Keep original for compatibility
                })
                
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Sort by combined score
        scored_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Return top N
        return scored_results[:top_n]
    
    def detect_repetition(self, query: str, current_time: datetime, time_window_hours: int = 24, 
                         similarity_threshold: float = 0.75) -> Optional[Dict[str, Any]]:
        """
        Check if a similar query was made recently.
        
        Args:
            query: Current query
            current_time: Current datetime
            time_window_hours: How far back to check (default 24 hours)
            similarity_threshold: Minimum similarity to consider repetition (0-1)
            
        Returns:
            Dict with repetition metadata if found, None otherwise
        """
        # Get recent user messages
        recent_messages = []
        cutoff_time = current_time.timestamp() - (time_window_hours * 3600)
        
        for message in reversed(self.messages_cache):  # Start from most recent
            if message.get('role') != 'user':
                continue
                
            # Parse message time
            msg_time = self._parse_datetime(
                message.get('date', ''),
                message.get('time', '')
            )
            
            if msg_time and msg_time.timestamp() >= cutoff_time:
                recent_messages.append(message)
        
        # Search for similar messages in recent history
        if not recent_messages:
            return None
        
        # Use vector search to find similar queries
        vector_results = self.base_memory.search(query, top_n=10)
        
        for result in vector_results:
            try:
                message = json.loads(result['chunk'])
                
                # Only check user messages
                if message.get('role') != 'user':
                    continue
                
                # Check if within time window
                msg_time = self._parse_datetime(
                    message.get('date', ''),
                    message.get('time', '')
                )
                
                if not msg_time or msg_time.timestamp() < cutoff_time:
                    continue
                
                # Check similarity
                similarity = result.get('score', 0)
                if similarity >= similarity_threshold:
                    # Don't flag the exact same message (current query)
                    time_diff_seconds = abs(current_time.timestamp() - msg_time.timestamp())
                    if time_diff_seconds < 10:  # Same message if within 10 seconds
                        continue
                    
                    # Found a repetition
                    hours_ago = (current_time - msg_time).total_seconds() / 3600
                    return {
                        'is_repetition': True,
                        'previous_query': message.get('content', ''),
                        'hours_ago': hours_ago,
                        'similarity': similarity,
                        'previous_time': msg_time.strftime("%m/%d/%Y %H:%M:%S")
                    }
            
            except (json.JSONDecodeError, KeyError):
                continue
        
        return None
    
    def get_recent_context(self, n_messages: int = 6) -> List[Dict[str, Any]]:
        """
        Get the most recent N messages for context.
        
        Args:
            n_messages: Number of recent messages to retrieve
            
        Returns:
            List of recent message dicts
        """
        return self.messages_cache[-n_messages:] if len(self.messages_cache) >= n_messages else self.messages_cache
