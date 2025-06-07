"""
NEXUS Conversation Memory System
Persistent conversation tracking with enterprise context
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ConversationHistory(Base):
    __tablename__ = 'conversation_history'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    context_type = Column(String(100), default='general')

class NexusMemory:
    """Enterprise conversation memory with persistent storage"""
    
    def __init__(self):
        # Initialize database connection
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            self.engine = create_engine(database_url)
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.db_session = Session()
        else:
            self.db_session = None
            
        # In-memory fallback
        self.memory_cache = {}
    
    def add_message(self, session_id: str, role: str, content: str, context_type: str = 'general'):
        """Add message to conversation history"""
        if self.db_session:
            try:
                message = ConversationHistory(
                    session_id=session_id,
                    role=role,
                    content=content,
                    context_type=context_type
                )
                self.db_session.add(message)
                self.db_session.commit()
            except Exception as e:
                self.db_session.rollback()
                # Fallback to memory cache
                self._add_to_cache(session_id, role, content, context_type)
        else:
            self._add_to_cache(session_id, role, content, context_type)
    
    def _add_to_cache(self, session_id: str, role: str, content: str, context_type: str):
        """Add to in-memory cache"""
        if session_id not in self.memory_cache:
            self.memory_cache[session_id] = []
        
        self.memory_cache[session_id].append({
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'context_type': context_type
        })
        
        # Keep only last 50 messages per session
        if len(self.memory_cache[session_id]) > 50:
            self.memory_cache[session_id] = self.memory_cache[session_id][-50:]
    
    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Get conversation history for session"""
        if self.db_session:
            try:
                messages = self.db_session.query(ConversationHistory)\
                    .filter_by(session_id=session_id)\
                    .order_by(ConversationHistory.timestamp.desc())\
                    .limit(limit).all()
                
                return [{
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'context_type': msg.context_type
                } for msg in reversed(messages)]
            except Exception:
                pass
        
        # Fallback to cache
        return self.memory_cache.get(session_id, [])[-limit:]
    
    def get_enterprise_context(self, session_id: str) -> str:
        """Get enterprise context for conversation"""
        history = self.get_conversation_history(session_id, 10)
        
        # Analyze conversation patterns for enterprise context
        topics = []
        for msg in history:
            content = msg['content'].lower()
            if any(word in content for word in ['trading', 'market', 'portfolio', 'investment']):
                topics.append('financial_analysis')
            elif any(word in content for word in ['automation', 'workflow', 'process', 'efficiency']):
                topics.append('operational_optimization')
            elif any(word in content for word in ['data', 'analytics', 'intelligence', 'insights']):
                topics.append('business_intelligence')
            elif any(word in content for word in ['security', 'compliance', 'risk', 'governance']):
                topics.append('enterprise_security')
        
        # Generate contextual prompt enhancement
        if 'financial_analysis' in topics:
            return "Focus on financial markets, trading strategies, and investment analysis with specific data and recommendations."
        elif 'operational_optimization' in topics:
            return "Emphasize process automation, efficiency improvements, and operational excellence with actionable insights."
        elif 'business_intelligence' in topics:
            return "Provide data-driven insights, predictive analytics, and strategic business intelligence."
        elif 'enterprise_security' in topics:
            return "Address security protocols, compliance requirements, and risk management strategies."
        else:
            return "Provide comprehensive enterprise-level analysis and strategic recommendations."
    
    def clear_session(self, session_id: str):
        """Clear conversation history for session"""
        if self.db_session:
            try:
                self.db_session.query(ConversationHistory)\
                    .filter_by(session_id=session_id).delete()
                self.db_session.commit()
            except Exception:
                self.db_session.rollback()
        
        if session_id in self.memory_cache:
            del self.memory_cache[session_id]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        stats = {
            'active_sessions': 0,
            'total_messages': 0,
            'session_list': []
        }
        
        if self.db_session:
            try:
                # Get unique sessions from last 24 hours
                yesterday = datetime.utcnow() - timedelta(days=1)
                sessions = self.db_session.query(ConversationHistory.session_id)\
                    .filter(ConversationHistory.timestamp >= yesterday)\
                    .distinct().all()
                
                stats['active_sessions'] = len(sessions)
                stats['session_list'] = [s[0] for s in sessions]
                
                # Get total message count
                total = self.db_session.query(ConversationHistory)\
                    .filter(ConversationHistory.timestamp >= yesterday).count()
                stats['total_messages'] = total
                
            except Exception:
                pass
        
        # Add cache stats
        stats['cache_sessions'] = len(self.memory_cache)
        stats['cache_messages'] = sum(len(msgs) for msgs in self.memory_cache.values())
        
        return stats

# Global memory instance
nexus_memory = NexusMemory()