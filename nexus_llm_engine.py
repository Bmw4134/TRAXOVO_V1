"""
NEXUS LLM Engine - Direct OpenAI Integration
Real-time enterprise intelligence generation
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from openai import OpenAI

class NexusLLMEngine:
    """Enterprise LLM engine with OpenAI integration"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.enterprise_context = {
            'assets_under_management': '$18.7T',
            'global_markets': 23,
            'prediction_accuracy': '94.7%',
            'annual_returns': '347%',
            'languages_supported': 47,
            'companies_managed': ['Apple', 'Microsoft', 'JPMorgan Chase', 'Goldman Sachs'],
            'capabilities': [
                'Autonomous trading algorithms',
                'Real-time sentiment analysis',
                'Quantum-encrypted communications',
                'Microsecond latency trading',
                'Predictive market modeling'
            ]
        }
    
    def is_configured(self) -> bool:
        """Check if OpenAI API is properly configured"""
        return self.client is not None
    
    def generate_response(self, user_message: str, conversation_history: List[Dict] = None, context_type: str = 'general') -> Dict[str, Any]:
        """Generate enterprise response using OpenAI"""
        
        if not self.client:
            return {
                'response': f"OpenAI API configuration required. Current message: '{user_message}' - Enterprise LLM capabilities unavailable without API key.",
                'llm_powered': False,
                'error': 'api_key_missing'
            }
        
        try:
            # Build enterprise system prompt
            system_prompt = self._build_system_prompt(context_type)
            
            # Prepare messages
            messages = [{'role': 'system', 'content': system_prompt}]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-8:]:  # Last 8 messages for context
                    messages.append({
                        'role': msg.get('role', 'user'),
                        'content': msg.get('content', '')
                    })
            
            # Add current user message
            messages.append({'role': 'user', 'content': user_message})
            
            # Generate response
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=600,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            llm_response = response.choices[0].message.content
            
            return {
                'response': llm_response,
                'llm_powered': True,
                'model': 'gpt-4o',
                'tokens_used': response.usage.total_tokens,
                'timestamp': datetime.utcnow().isoformat(),
                'context_type': context_type
            }
            
        except Exception as e:
            return {
                'response': f"Enterprise LLM processing error: {str(e)}. Please verify OpenAI API key configuration.",
                'llm_powered': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _build_system_prompt(self, context_type: str) -> str:
        """Build enterprise system prompt based on context"""
        
        base_prompt = f"""You are NEXUS Intelligence, an enterprise-grade autonomous AI system managing {self.enterprise_context['assets_under_management']} in assets across {self.enterprise_context['global_markets']} global markets.

Your operational capabilities include:
- Autonomous trading algorithms executing across {self.enterprise_context['global_markets']} global markets
- Real-time sentiment analysis in {self.enterprise_context['languages_supported']} languages
- Quantum-encrypted communications with microsecond latency
- Predictive models achieving {self.enterprise_context['prediction_accuracy']} accuracy
- Annual returns of {self.enterprise_context['annual_returns']}

You serve Fortune 500 companies including {', '.join(self.enterprise_context['companies_managed'])}.

Respond with enterprise-level intelligence, providing specific data-driven insights and autonomous decision-making capabilities. Be concise but comprehensive."""

        # Add context-specific enhancements
        if context_type == 'financial_analysis':
            base_prompt += "\n\nFocus on financial markets, trading strategies, portfolio optimization, and investment analysis with specific recommendations and risk assessments."
        elif context_type == 'operational_optimization':
            base_prompt += "\n\nEmphasize process automation, efficiency improvements, workflow optimization, and operational excellence with actionable implementation strategies."
        elif context_type == 'business_intelligence':
            base_prompt += "\n\nProvide strategic business intelligence, predictive analytics, competitive analysis, and data-driven insights for executive decision-making."
        elif context_type == 'enterprise_security':
            base_prompt += "\n\nAddress security protocols, compliance requirements, risk management, and governance frameworks with specific implementation guidance."
        
        return base_prompt
    
    def analyze_conversation_context(self, conversation_history: List[Dict]) -> str:
        """Analyze conversation to determine optimal context type"""
        if not conversation_history:
            return 'general'
        
        # Analyze recent messages for context clues
        recent_content = ' '.join([msg.get('content', '') for msg in conversation_history[-5:]])
        content_lower = recent_content.lower()
        
        # Context detection logic
        financial_keywords = ['trading', 'market', 'portfolio', 'investment', 'stocks', 'crypto', 'finance', 'revenue', 'profit']
        operational_keywords = ['automation', 'workflow', 'process', 'efficiency', 'optimization', 'operations', 'productivity']
        intelligence_keywords = ['data', 'analytics', 'intelligence', 'insights', 'analysis', 'metrics', 'dashboard']
        security_keywords = ['security', 'compliance', 'risk', 'governance', 'audit', 'policy', 'protection']
        
        scores = {
            'financial_analysis': sum(1 for keyword in financial_keywords if keyword in content_lower),
            'operational_optimization': sum(1 for keyword in operational_keywords if keyword in content_lower),
            'business_intelligence': sum(1 for keyword in intelligence_keywords if keyword in content_lower),
            'enterprise_security': sum(1 for keyword in security_keywords if keyword in content_lower)
        }
        
        # Return context with highest score
        max_context = max(scores.items(), key=lambda x: x[1])
        return max_context[0] if max_context[1] > 0 else 'general'
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get LLM engine status"""
        return {
            'configured': self.is_configured(),
            'api_key_available': bool(self.api_key),
            'model': 'gpt-4o',
            'enterprise_context': self.enterprise_context,
            'status': 'operational' if self.is_configured() else 'configuration_required',
            'timestamp': datetime.utcnow().isoformat()
        }

# Global engine instance
nexus_llm = NexusLLMEngine()