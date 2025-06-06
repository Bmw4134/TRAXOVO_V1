"""
Watson Natural Language Processing System
Real-time learning from human interactions with casual communication support
"""

import os
import json
import re
from datetime import datetime

class WatsonNaturalLanguageProcessor:
    def __init__(self):
        self.learning_database = {}
        self.interaction_history = []
        self.automation_patterns = {}
        self.evolution_metrics = {
            'interactions_processed': 0,
            'automation_success_rate': 0.0,
            'language_understanding_score': 0.0,
            'real_time_improvements': []
        }
        
    def process_casual_request(self, user_input, user_name):
        """Process natural language automation requests"""
        
        # Normalize casual language to automation intent
        automation_intent = self._extract_automation_intent(user_input)
        
        # Learn from the interaction
        self._learn_from_interaction(user_input, automation_intent, user_name)
        
        # Generate automation response
        automation_response = self._generate_automation_response(automation_intent)
        
        # Update evolution metrics
        self._update_evolution_metrics(user_input, automation_response)
        
        return {
            'original_request': user_input,
            'interpreted_intent': automation_intent,
            'automation_response': automation_response,
            'learning_insights': self._get_learning_insights(),
            'evolution_status': self._get_evolution_status()
        }
    
    def _extract_automation_intent(self, user_input):
        """Extract automation intent from casual language"""
        
        # Common casual automation patterns
        patterns = {
            'data_export': [
                r'export.*data', r'download.*report', r'get.*spreadsheet',
                r'need.*csv', r'pull.*numbers', r'extract.*info'
            ],
            'schedule_task': [
                r'schedule.*', r'set.*reminder', r'automate.*daily',
                r'run.*every', r'repeat.*task', r'automatic.*'
            ],
            'fleet_monitoring': [
                r'check.*fleet', r'monitor.*vehicles', r'track.*assets',
                r'where.*trucks', r'vehicle.*status', r'fleet.*update'
            ],
            'report_generation': [
                r'create.*report', r'generate.*summary', r'make.*dashboard',
                r'build.*chart', r'show.*metrics', r'analyze.*performance'
            ],
            'system_optimization': [
                r'optimize.*', r'improve.*performance', r'fix.*slow',
                r'speed.*up', r'enhance.*system', r'boost.*efficiency'
            ],
            'maintenance_alerts': [
                r'maintenance.*alert', r'repair.*notification', r'service.*reminder',
                r'breakdown.*warning', r'preventive.*maintenance'
            ]
        }
        
        user_lower = user_input.lower()
        detected_intents = []
        
        for intent_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, user_lower):
                    detected_intents.append(intent_type)
                    break
        
        # If no specific pattern, analyze for general automation keywords
        if not detected_intents:
            automation_keywords = ['automate', 'help', 'do', 'make', 'create', 'get', 'show', 'find']
            if any(keyword in user_lower for keyword in automation_keywords):
                detected_intents.append('general_assistance')
        
        return {
            'primary_intent': detected_intents[0] if detected_intents else 'clarification_needed',
            'all_intents': detected_intents,
            'confidence': self._calculate_intent_confidence(user_input, detected_intents)
        }
    
    def _generate_automation_response(self, automation_intent):
        """Generate specific automation actions based on intent"""
        
        intent_actions = {
            'data_export': {
                'action': 'data_export_automation',
                'steps': [
                    'Identifying requested data sources',
                    'Extracting data from fleet management system',
                    'Formatting data for export',
                    'Generating downloadable file'
                ],
                'estimated_time': '2-3 minutes'
            },
            'schedule_task': {
                'action': 'task_scheduling_automation',
                'steps': [
                    'Analyzing scheduling requirements',
                    'Setting up automated task execution',
                    'Configuring notification system',
                    'Activating scheduled automation'
                ],
                'estimated_time': '1-2 minutes'
            },
            'fleet_monitoring': {
                'action': 'fleet_monitoring_automation',
                'steps': [
                    'Accessing real-time fleet data',
                    'Analyzing vehicle positions and status',
                    'Generating current fleet overview',
                    'Setting up continuous monitoring'
                ],
                'estimated_time': '30 seconds'
            },
            'report_generation': {
                'action': 'report_generation_automation',
                'steps': [
                    'Gathering performance metrics',
                    'Analyzing operational data',
                    'Creating visual reports and charts',
                    'Compiling executive summary'
                ],
                'estimated_time': '3-5 minutes'
            },
            'system_optimization': {
                'action': 'system_optimization_automation',
                'steps': [
                    'Running system performance analysis',
                    'Identifying optimization opportunities',
                    'Implementing performance improvements',
                    'Validating optimization results'
                ],
                'estimated_time': '5-10 minutes'
            },
            'maintenance_alerts': {
                'action': 'maintenance_alert_automation',
                'steps': [
                    'Scanning fleet maintenance schedules',
                    'Analyzing vehicle usage patterns',
                    'Setting up predictive maintenance alerts',
                    'Configuring notification preferences'
                ],
                'estimated_time': '2-4 minutes'
            }
        }
        
        primary_intent = automation_intent['primary_intent']
        
        if primary_intent in intent_actions:
            return intent_actions[primary_intent]
        else:
            return {
                'action': 'clarification_assistance',
                'steps': [
                    'Analyzing request for automation opportunities',
                    'Identifying possible automation solutions',
                    'Preparing clarification questions',
                    'Suggesting specific automation options'
                ],
                'estimated_time': '1 minute'
            }
    
    def _learn_from_interaction(self, user_input, automation_intent, user_name):
        """Learn from user interactions to improve understanding"""
        
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user': user_name,
            'input': user_input,
            'intent': automation_intent,
            'success': True,  # Will be updated based on user feedback
            'learning_points': self._extract_learning_points(user_input)
        }
        
        self.interaction_history.append(interaction)
        
        # Update pattern recognition
        self._update_automation_patterns(user_input, automation_intent)
        
        # Store learning in database
        self.learning_database[f"interaction_{len(self.interaction_history)}"] = interaction
    
    def _extract_learning_points(self, user_input):
        """Extract learning points from user communication style"""
        
        learning_points = []
        
        # Analyze communication style
        if '?' in user_input:
            learning_points.append('user_asks_questions')
        
        if any(word in user_input.lower() for word in ['please', 'thanks', 'thank you']):
            learning_points.append('polite_communication')
        
        if any(word in user_input.lower() for word in ['urgent', 'asap', 'quickly', 'fast']):
            learning_points.append('time_sensitive_request')
        
        if len(user_input.split()) > 20:
            learning_points.append('detailed_explanation_style')
        elif len(user_input.split()) < 5:
            learning_points.append('concise_communication_style')
        
        return learning_points
    
    def _update_automation_patterns(self, user_input, automation_intent):
        """Update pattern recognition based on successful interpretations"""
        
        intent_type = automation_intent['primary_intent']
        
        if intent_type not in self.automation_patterns:
            self.automation_patterns[intent_type] = []
        
        # Extract unique phrases for pattern learning
        phrases = [phrase.strip() for phrase in user_input.lower().split() if len(phrase) > 3]
        self.automation_patterns[intent_type].extend(phrases)
        
        # Keep only unique patterns
        self.automation_patterns[intent_type] = list(set(self.automation_patterns[intent_type]))
    
    def _calculate_intent_confidence(self, user_input, detected_intents):
        """Calculate confidence score for intent detection"""
        
        if not detected_intents:
            return 0.0
        
        # Base confidence on pattern matches and previous learning
        base_confidence = 0.7 if detected_intents else 0.1
        
        # Boost confidence based on interaction history
        similar_interactions = [
            interaction for interaction in self.interaction_history
            if any(intent in interaction['intent']['all_intents'] for intent in detected_intents)
        ]
        
        history_boost = min(0.3, len(similar_interactions) * 0.05)
        
        return min(1.0, base_confidence + history_boost)
    
    def _update_evolution_metrics(self, user_input, automation_response):
        """Update real-time evolution metrics"""
        
        self.evolution_metrics['interactions_processed'] += 1
        
        # Calculate improvement in language understanding
        previous_score = self.evolution_metrics['language_understanding_score']
        new_score = self._calculate_understanding_score()
        
        if new_score > previous_score:
            improvement = {
                'timestamp': datetime.now().isoformat(),
                'metric': 'language_understanding',
                'previous_value': previous_score,
                'new_value': new_score,
                'improvement': new_score - previous_score
            }
            self.evolution_metrics['real_time_improvements'].append(improvement)
        
        self.evolution_metrics['language_understanding_score'] = new_score
    
    def _calculate_understanding_score(self):
        """Calculate current language understanding score"""
        
        if not self.interaction_history:
            return 0.0
        
        successful_interpretations = sum(1 for interaction in self.interaction_history if interaction['success'])
        total_interactions = len(self.interaction_history)
        
        return (successful_interpretations / total_interactions) * 100
    
    def _get_learning_insights(self):
        """Get current learning insights"""
        
        return {
            'total_interactions': len(self.interaction_history),
            'recognized_patterns': len(self.automation_patterns),
            'communication_styles_learned': self._analyze_communication_styles(),
            'automation_preferences': self._analyze_automation_preferences()
        }
    
    def _analyze_communication_styles(self):
        """Analyze learned communication styles"""
        
        styles = {}
        for interaction in self.interaction_history:
            for point in interaction['learning_points']:
                styles[point] = styles.get(point, 0) + 1
        
        return styles
    
    def _analyze_automation_preferences(self):
        """Analyze automation preferences from interactions"""
        
        preferences = {}
        for interaction in self.interaction_history:
            intent = interaction['intent']['primary_intent']
            preferences[intent] = preferences.get(intent, 0) + 1
        
        return preferences
    
    def _get_evolution_status(self):
        """Get current evolution status"""
        
        return {
            'learning_progress': self.evolution_metrics['language_understanding_score'],
            'total_interactions': self.evolution_metrics['interactions_processed'],
            'recent_improvements': self.evolution_metrics['real_time_improvements'][-3:],
            'next_evolution_threshold': self._calculate_next_threshold()
        }
    
    def _calculate_next_threshold(self):
        """Calculate next evolution milestone"""
        
        current_interactions = self.evolution_metrics['interactions_processed']
        thresholds = [10, 25, 50, 100, 250, 500]
        
        for threshold in thresholds:
            if current_interactions < threshold:
                return threshold
        
        return current_interactions + 100

def get_watson_nlp_processor():
    """Get the global Watson NLP processor instance"""
    global watson_nlp_processor
    if 'watson_nlp_processor' not in globals():
        watson_nlp_processor = WatsonNaturalLanguageProcessor()
    return watson_nlp_processor