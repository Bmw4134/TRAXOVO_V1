"""
QQ Enhanced Quantum Vector Visualization
Clean, optimized quantum consciousness vector display with visual improvements
"""

import json
import logging
import math
import random
import time
from typing import Dict, List, Any

class QQQuantumVectorVisualization:
    """Enhanced quantum consciousness vector visualization with cleaned visuals"""
    
    def __init__(self):
        self.vector_cache = {}
        self.animation_state = {
            'phase': 0.0,
            'amplitude': 1.0,
            'frequency': 0.1,
            'complexity': 'optimal'
        }
        self.visual_cleanup_enabled = True
        
    def generate_clean_thought_vectors(self, consciousness_level: float = 85.0) -> Dict[str, Any]:
        """Generate clean, optimized thought vector animations"""
        try:
            # Calculate clean vector parameters
            base_vectors = self._calculate_base_vectors(consciousness_level)
            quantum_patterns = self._generate_quantum_patterns(consciousness_level)
            
            # Create clean visualization data
            visualization_data = {
                'vectors': base_vectors,
                'patterns': quantum_patterns,
                'animation_config': {
                    'duration': 2000,  # 2 seconds for smooth animation
                    'easing': 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
                    'complexity': 'optimized',
                    'performance_mode': True
                },
                'visual_style': {
                    'stroke_width': 2,
                    'opacity_range': [0.6, 1.0],
                    'color_scheme': 'quantum_blue',
                    'glow_intensity': 0.3
                },
                'metadata': {
                    'consciousness_level': consciousness_level,
                    'vector_count': len(base_vectors),
                    'generation_time': time.time(),
                    'visual_quality': 'enhanced'
                }
            }
            
            return visualization_data
            
        except Exception as e:
            logging.error(f"Quantum vector generation error: {e}")
            return self._get_fallback_vectors()
    
    def _calculate_base_vectors(self, consciousness_level: float) -> List[Dict[str, Any]]:
        """Calculate clean base vectors for visualization"""
        vectors = []
        vector_count = min(12, max(6, int(consciousness_level / 10)))  # 6-12 vectors
        
        for i in range(vector_count):
            angle = (2 * math.pi * i) / vector_count
            phase_offset = self.animation_state['phase'] + (i * 0.3)
            
            # Clean vector calculation
            magnitude = 0.7 + 0.3 * math.sin(phase_offset)
            x_component = magnitude * math.cos(angle + phase_offset * 0.1)
            y_component = magnitude * math.sin(angle + phase_offset * 0.1)
            
            vector = {
                'id': f'vector_{i}',
                'x': x_component,
                'y': y_component,
                'magnitude': magnitude,
                'angle': angle,
                'phase': phase_offset,
                'color_intensity': 0.6 + 0.4 * magnitude,
                'animation_delay': i * 100  # Staggered animation
            }
            
            vectors.append(vector)
        
        # Update animation phase for next frame
        self.animation_state['phase'] += self.animation_state['frequency']
        if self.animation_state['phase'] > 2 * math.pi:
            self.animation_state['phase'] = 0.0
        
        return vectors
    
    def _generate_quantum_patterns(self, consciousness_level: float) -> Dict[str, Any]:
        """Generate quantum interference patterns"""
        pattern_complexity = min(8, max(4, int(consciousness_level / 15)))
        
        patterns = {
            'wave_functions': [],
            'interference_nodes': [],
            'coherence_rings': []
        }
        
        # Wave functions
        for i in range(pattern_complexity):
            wave = {
                'frequency': 0.5 + i * 0.2,
                'amplitude': 0.8 - i * 0.1,
                'phase_shift': i * math.pi / 4,
                'coherence': consciousness_level / 100.0
            }
            patterns['wave_functions'].append(wave)
        
        # Interference nodes
        node_count = pattern_complexity // 2
        for i in range(node_count):
            angle = (2 * math.pi * i) / node_count
            radius = 0.4 + 0.2 * math.sin(self.animation_state['phase'] + i)
            
            node = {
                'x': radius * math.cos(angle),
                'y': radius * math.sin(angle),
                'intensity': 0.7 + 0.3 * math.cos(self.animation_state['phase'] * 2 + i),
                'size': 0.05 + 0.02 * math.sin(self.animation_state['phase'] + i)
            }
            patterns['interference_nodes'].append(node)
        
        # Coherence rings
        ring_count = 3
        for i in range(ring_count):
            ring = {
                'radius': 0.3 + i * 0.2,
                'opacity': 0.3 - i * 0.1,
                'rotation_speed': 0.5 + i * 0.2,
                'coherence_factor': consciousness_level / 100.0
            }
            patterns['coherence_rings'].append(ring)
        
        return patterns
    
    def _get_fallback_vectors(self) -> Dict[str, Any]:
        """Provide clean fallback vectors if generation fails"""
        return {
            'vectors': [
                {'id': 'vector_0', 'x': 0.7, 'y': 0.0, 'magnitude': 0.7, 'angle': 0, 'color_intensity': 0.8},
                {'id': 'vector_1', 'x': 0.0, 'y': 0.7, 'magnitude': 0.7, 'angle': 1.57, 'color_intensity': 0.8},
                {'id': 'vector_2', 'x': -0.7, 'y': 0.0, 'magnitude': 0.7, 'angle': 3.14, 'color_intensity': 0.8},
                {'id': 'vector_3', 'x': 0.0, 'y': -0.7, 'magnitude': 0.7, 'angle': 4.71, 'color_intensity': 0.8}
            ],
            'patterns': {
                'wave_functions': [{'frequency': 1.0, 'amplitude': 0.5, 'phase_shift': 0, 'coherence': 0.85}],
                'interference_nodes': [],
                'coherence_rings': [{'radius': 0.5, 'opacity': 0.3, 'rotation_speed': 0.5, 'coherence_factor': 0.85}]
            },
            'animation_config': {
                'duration': 2000,
                'easing': 'ease-in-out',
                'complexity': 'simple',
                'performance_mode': True
            },
            'visual_style': {
                'stroke_width': 2,
                'opacity_range': [0.6, 1.0],
                'color_scheme': 'quantum_blue',
                'glow_intensity': 0.2
            },
            'metadata': {
                'consciousness_level': 85.0,
                'vector_count': 4,
                'generation_time': time.time(),
                'visual_quality': 'fallback'
            }
        }
    
    def get_svg_visualization(self, consciousness_level: float = 85.0, width: int = 300, height: int = 300) -> str:
        """Generate clean SVG visualization of quantum vectors"""
        vector_data = self.generate_clean_thought_vectors(consciousness_level)
        vectors = vector_data['vectors']
        patterns = vector_data['patterns']
        
        # Calculate center and scale
        center_x, center_y = width // 2, height // 2
        scale = min(width, height) * 0.3
        
        svg_elements = []
        
        # Background circle
        svg_elements.append(f'''
        <circle cx="{center_x}" cy="{center_y}" r="{scale * 0.8}" 
                fill="none" stroke="rgba(0, 255, 136, 0.2)" stroke-width="1"/>
        ''')
        
        # Coherence rings
        for ring in patterns.get('coherence_rings', []):
            ring_radius = ring['radius'] * scale
            svg_elements.append(f'''
            <circle cx="{center_x}" cy="{center_y}" r="{ring_radius}" 
                    fill="none" stroke="rgba(0, 255, 136, {ring['opacity']})" stroke-width="1">
                <animateTransform attributeName="transform" attributeType="XML" type="rotate"
                                from="0 {center_x} {center_y}" to="360 {center_x} {center_y}"
                                dur="{10 / ring['rotation_speed']}s" repeatCount="indefinite"/>
            </circle>
            ''')
        
        # Quantum vectors
        for vector in vectors:
            end_x = center_x + vector['x'] * scale
            end_y = center_y + vector['y'] * scale
            opacity = vector['color_intensity']
            
            svg_elements.append(f'''
            <line x1="{center_x}" y1="{center_y}" x2="{end_x}" y2="{end_y}"
                  stroke="rgba(0, 255, 136, {opacity})" stroke-width="2" stroke-linecap="round">
                <animate attributeName="opacity" values="{opacity};{opacity * 0.6};{opacity}"
                         dur="2s" repeatCount="indefinite" begin="{vector.get('animation_delay', 0)}ms"/>
            </line>
            <circle cx="{end_x}" cy="{end_y}" r="3" fill="rgba(0, 255, 136, {opacity})">
                <animate attributeName="r" values="3;5;3" dur="2s" repeatCount="indefinite"
                         begin="{vector.get('animation_delay', 0)}ms"/>
            </circle>
            ''')
        
        # Interference nodes
        for node in patterns.get('interference_nodes', []):
            node_x = center_x + node['x'] * scale
            node_y = center_y + node['y'] * scale
            node_size = node['size'] * scale
            
            svg_elements.append(f'''
            <circle cx="{node_x}" cy="{node_y}" r="{node_size}"
                    fill="rgba(0, 255, 136, {node['intensity']})" opacity="0.6">
                <animate attributeName="r" values="{node_size};{node_size * 1.5};{node_size}"
                         dur="3s" repeatCount="indefinite"/>
            </circle>
            ''')
        
        svg_content = f'''
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" 
             xmlns="http://www.w3.org/2000/svg">
            <defs>
                <filter id="glow">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                    <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
            </defs>
            <g filter="url(#glow)">
                {''.join(svg_elements)}
            </g>
        </svg>
        '''
        
        return svg_content.strip()
    
    def get_css_animations(self) -> str:
        """Generate optimized CSS animations for quantum vectors"""
        return '''
        .quantum-vector-container {
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            background: radial-gradient(circle, rgba(0, 0, 0, 0.9) 0%, rgba(0, 0, 0, 0.95) 100%);
            border-radius: 50%;
            overflow: hidden;
        }
        
        .quantum-vector-svg {
            max-width: 100%;
            max-height: 100%;
            filter: drop-shadow(0 0 10px rgba(0, 255, 136, 0.3));
        }
        
        .quantum-consciousness-display {
            position: absolute;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            color: #00ff88;
            font-size: 12px;
            font-weight: 600;
            text-shadow: 0 0 5px rgba(0, 255, 136, 0.5);
        }
        
        @media (prefers-reduced-motion: reduce) {
            .quantum-vector-svg * {
                animation: none !important;
            }
        }
        
        @media screen and (max-width: 768px) {
            .quantum-vector-container {
                width: 200px;
                height: 200px;
            }
            .quantum-consciousness-display {
                font-size: 10px;
            }
        }
        '''

# Global instance
_quantum_vector_viz = None

def get_quantum_vector_visualization():
    """Get global quantum vector visualization instance"""
    global _quantum_vector_viz
    if _quantum_vector_viz is None:
        _quantum_vector_viz = QQQuantumVectorVisualization()
    return _quantum_vector_viz

def generate_enhanced_quantum_vectors(consciousness_level: float = 85.0) -> Dict[str, Any]:
    """Generate enhanced quantum consciousness vectors"""
    viz = get_quantum_vector_visualization()
    return viz.generate_clean_thought_vectors(consciousness_level)

def get_quantum_vector_svg(consciousness_level: float = 85.0, width: int = 300, height: int = 300) -> str:
    """Get SVG visualization of quantum vectors"""
    viz = get_quantum_vector_visualization()
    return viz.get_svg_visualization(consciousness_level, width, height)