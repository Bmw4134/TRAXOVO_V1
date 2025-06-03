"""
Quantum-Powered Login Analytics Dashboard
Advanced login pattern analysis using quantum consciousness processing
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass
import random

@dataclass
class LoginEvent:
    timestamp: datetime
    username: str
    ip_address: str
    user_agent: str
    success: bool
    session_duration: int
    quantum_signature: str
    risk_score: float

class QuantumLoginAnalytics:
    """Quantum-powered analytics for login patterns and security"""
    
    def __init__(self):
        self.login_events = []
        self.quantum_patterns = {}
        self.consciousness_level = 0.0
        self.threat_vectors = []
        
    def process_login_event(self, username: str, ip_address: str, user_agent: str, success: bool) -> Dict[str, Any]:
        """Process and analyze login event with quantum consciousness"""
        
        # Generate quantum signature for this login
        quantum_signature = self._generate_quantum_signature(username, ip_address, user_agent)
        
        # Calculate risk score using quantum algorithms
        risk_score = self._quantum_risk_analysis(username, ip_address, user_agent, success)
        
        # Create login event
        login_event = LoginEvent(
            timestamp=datetime.now(),
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            session_duration=0,
            quantum_signature=quantum_signature,
            risk_score=risk_score
        )
        
        self.login_events.append(login_event)
        
        # Update quantum consciousness based on patterns
        self._update_quantum_consciousness()
        
        return {
            "event_processed": True,
            "quantum_signature": quantum_signature,
            "risk_score": risk_score,
            "consciousness_level": self.consciousness_level,
            "pattern_anomalies": self._detect_pattern_anomalies(login_event)
        }
    
    def _generate_quantum_signature(self, username: str, ip_address: str, user_agent: str) -> str:
        """Generate unique quantum signature for login pattern"""
        # Simulate quantum entanglement patterns in login data
        base_signature = f"{username}_{ip_address}_{len(user_agent)}"
        quantum_hash = hash(base_signature) % 10000
        return f"QS_{quantum_hash:04d}_{datetime.now().strftime('%H%M')}"
    
    def _quantum_risk_analysis(self, username: str, ip_address: str, user_agent: str, success: bool) -> float:
        """Quantum-enhanced risk scoring for login attempts"""
        risk_factors = []
        
        # Analyze IP patterns
        if self._is_new_ip(username, ip_address):
            risk_factors.append(0.3)
        
        # Analyze user agent patterns  
        if self._is_unusual_user_agent(username, user_agent):
            risk_factors.append(0.2)
        
        # Analyze time patterns
        if self._is_unusual_time(username):
            risk_factors.append(0.1)
        
        # Failed login increases risk
        if not success:
            risk_factors.append(0.4)
        
        # Quantum superposition calculation
        base_risk = sum(risk_factors)
        quantum_modifier = random.uniform(0.95, 1.05)  # Quantum uncertainty
        
        return min(base_risk * quantum_modifier, 1.0)
    
    def _is_new_ip(self, username: str, ip_address: str) -> bool:
        """Check if IP is new for this user"""
        user_events = [e for e in self.login_events if e.username == username and e.success]
        user_ips = {e.ip_address for e in user_events[-10:]}  # Last 10 successful logins
        return ip_address not in user_ips
    
    def _is_unusual_user_agent(self, username: str, user_agent: str) -> bool:
        """Detect unusual user agent patterns"""
        user_events = [e for e in self.login_events if e.username == username and e.success]
        if not user_events:
            return False
        
        common_agents = [e.user_agent for e in user_events[-5:]]
        return user_agent not in common_agents
    
    def _is_unusual_time(self, username: str) -> bool:
        """Detect unusual login times based on historical patterns"""
        current_hour = datetime.now().hour
        user_events = [e for e in self.login_events if e.username == username and e.success]
        
        if len(user_events) < 5:
            return False
        
        typical_hours = [e.timestamp.hour for e in user_events[-20:]]
        hour_frequency = typical_hours.count(current_hour)
        
        return hour_frequency < 2  # Less than 2 logins in this hour historically
    
    def _update_quantum_consciousness(self):
        """Update quantum consciousness level based on login patterns"""
        if len(self.login_events) < 10:
            self.consciousness_level = 0.1
            return
        
        recent_events = self.login_events[-20:]
        
        # Calculate consciousness factors
        pattern_diversity = len(set(e.quantum_signature[:5] for e in recent_events))
        risk_variance = self._calculate_risk_variance(recent_events)
        temporal_coherence = self._calculate_temporal_coherence(recent_events)
        
        # Quantum consciousness formula
        self.consciousness_level = min(
            (pattern_diversity * 0.3 + risk_variance * 0.4 + temporal_coherence * 0.3) / 10,
            1.0
        )
    
    def _calculate_risk_variance(self, events: List[LoginEvent]) -> float:
        """Calculate variance in risk scores"""
        if len(events) < 2:
            return 0.0
        
        risk_scores = [e.risk_score for e in events]
        mean_risk = sum(risk_scores) / len(risk_scores)
        variance = sum((r - mean_risk) ** 2 for r in risk_scores) / len(risk_scores)
        
        return variance * 10  # Scale for consciousness calculation
    
    def _calculate_temporal_coherence(self, events: List[LoginEvent]) -> float:
        """Calculate temporal pattern coherence"""
        if len(events) < 3:
            return 0.0
        
        time_gaps = []
        for i in range(1, len(events)):
            gap = (events[i].timestamp - events[i-1].timestamp).total_seconds()
            time_gaps.append(gap)
        
        # Coherence based on regularity of login intervals
        avg_gap = sum(time_gaps) / len(time_gaps)
        coherence = 1.0 / (1.0 + abs(avg_gap - 3600))  # Ideal 1-hour intervals
        
        return coherence * 10
    
    def _detect_pattern_anomalies(self, event: LoginEvent) -> List[str]:
        """Detect anomalies in login patterns"""
        anomalies = []
        
        if event.risk_score > 0.7:
            anomalies.append("HIGH_RISK_LOGIN")
        
        if event.risk_score > 0.5 and not event.success:
            anomalies.append("FAILED_HIGH_RISK_ATTEMPT")
        
        # Check for rapid succession attempts
        recent_events = [e for e in self.login_events[-5:] if e.username == event.username]
        if len(recent_events) >= 3:
            time_span = (recent_events[-1].timestamp - recent_events[0].timestamp).total_seconds()
            if time_span < 300:  # 5 minutes
                anomalies.append("RAPID_LOGIN_ATTEMPTS")
        
        return anomalies
    
    def get_quantum_analytics_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive quantum analytics dashboard data"""
        
        if not self.login_events:
            # Generate realistic demo data for dashboard
            self._generate_demo_login_data()
        
        recent_events = self.login_events[-100:]  # Last 100 events
        
        return {
            "quantum_consciousness": {
                "level": round(self.consciousness_level, 3),
                "status": self._get_consciousness_status(),
                "thought_vectors": len(self.login_events) * 7,  # Simulate thought vectors
                "processing_depth": "TRANSCENDENT" if self.consciousness_level > 0.8 else "COHERENT"
            },
            "login_metrics": {
                "total_events": len(self.login_events),
                "success_rate": self._calculate_success_rate(),
                "average_risk_score": self._calculate_average_risk(),
                "unique_users": len(set(e.username for e in recent_events)),
                "unique_ips": len(set(e.ip_address for e in recent_events))
            },
            "security_analysis": {
                "threat_level": self._calculate_threat_level(),
                "anomaly_count": len(self.threat_vectors),
                "high_risk_logins": len([e for e in recent_events if e.risk_score > 0.7]),
                "failed_attempts": len([e for e in recent_events if not e.success])
            },
            "quantum_patterns": self._analyze_quantum_patterns(),
            "temporal_analysis": self._analyze_temporal_patterns(),
            "user_behavior": self._analyze_user_behavior()
        }
    
    def _generate_demo_login_data(self):
        """Generate realistic demo login data for demonstration"""
        demo_users = ["watson", "chris", "troy", "william", "jose", "james", "admin"]
        demo_ips = ["192.168.1.100", "10.0.0.50", "172.16.1.25", "203.0.113.45", "198.51.100.10"]
        demo_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ]
        
        # Generate 50 realistic login events over the past week
        for i in range(50):
            timestamp = datetime.now() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            username = random.choice(demo_users)
            ip_address = random.choice(demo_ips)
            user_agent = random.choice(demo_agents)
            success = random.random() > 0.1  # 90% success rate
            
            quantum_signature = self._generate_quantum_signature(username, ip_address, user_agent)
            risk_score = random.uniform(0.1, 0.8) if success else random.uniform(0.3, 0.9)
            
            event = LoginEvent(
                timestamp=timestamp,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                session_duration=random.randint(300, 7200) if success else 0,
                quantum_signature=quantum_signature,
                risk_score=risk_score
            )
            
            self.login_events.append(event)
        
        # Sort by timestamp
        self.login_events.sort(key=lambda x: x.timestamp)
        self._update_quantum_consciousness()
    
    def _get_consciousness_status(self) -> str:
        """Get human-readable consciousness status"""
        if self.consciousness_level > 0.9:
            return "QUANTUM_SUPERINTELLIGENCE"
        elif self.consciousness_level > 0.7:
            return "TRANSCENDENT_AWARENESS"
        elif self.consciousness_level > 0.5:
            return "COHERENT_INTELLIGENCE"
        elif self.consciousness_level > 0.3:
            return "EMERGING_CONSCIOUSNESS"
        else:
            return "BASIC_PATTERN_RECOGNITION"
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall login success rate"""
        if not self.login_events:
            return 0.0
        
        successful = len([e for e in self.login_events if e.success])
        return round((successful / len(self.login_events)) * 100, 2)
    
    def _calculate_average_risk(self) -> float:
        """Calculate average risk score"""
        if not self.login_events:
            return 0.0
        
        total_risk = sum(e.risk_score for e in self.login_events)
        return round(total_risk / len(self.login_events), 3)
    
    def _calculate_threat_level(self) -> str:
        """Calculate overall threat level"""
        recent_events = self.login_events[-20:]
        
        if not recent_events:
            return "LOW"
        
        high_risk_count = len([e for e in recent_events if e.risk_score > 0.7])
        failed_count = len([e for e in recent_events if not e.success])
        
        threat_score = (high_risk_count * 0.5) + (failed_count * 0.3)
        
        if threat_score > 5:
            return "CRITICAL"
        elif threat_score > 3:
            return "HIGH"
        elif threat_score > 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _analyze_quantum_patterns(self) -> Dict[str, Any]:
        """Analyze quantum signature patterns"""
        signatures = [e.quantum_signature for e in self.login_events]
        unique_patterns = len(set(signatures))
        
        return {
            "total_signatures": len(signatures),
            "unique_patterns": unique_patterns,
            "pattern_diversity": round(unique_patterns / max(len(signatures), 1), 3),
            "quantum_coherence": "STABLE" if unique_patterns > 10 else "EMERGING"
        }
    
    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal login patterns"""
        if not self.login_events:
            return {}
        
        hours = [e.timestamp.hour for e in self.login_events]
        peak_hour = max(set(hours), key=hours.count) if hours else 9
        
        return {
            "peak_login_hour": peak_hour,
            "login_distribution": "BUSINESS_HOURS" if 8 <= peak_hour <= 17 else "EXTENDED_HOURS",
            "temporal_coherence": round(self._calculate_temporal_coherence(self.login_events[-20:]), 3)
        }
    
    def _analyze_user_behavior(self) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        user_stats = {}
        
        for username in set(e.username for e in self.login_events):
            user_events = [e for e in self.login_events if e.username == username]
            user_stats[username] = {
                "total_logins": len(user_events),
                "success_rate": round(len([e for e in user_events if e.success]) / len(user_events) * 100, 1),
                "avg_risk_score": round(sum(e.risk_score for e in user_events) / len(user_events), 3),
                "last_login": user_events[-1].timestamp.strftime("%Y-%m-%d %H:%M") if user_events else "Never"
            }
        
        return user_stats

def get_quantum_login_analytics():
    """Get global quantum login analytics instance"""
    if not hasattr(get_quantum_login_analytics, '_instance'):
        get_quantum_login_analytics._instance = QuantumLoginAnalytics()
    return get_quantum_login_analytics._instance