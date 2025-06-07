#!/usr/bin/env python3
"""
NEXUS Voice Commands & Archive Search System
Easy voice navigation and comprehensive archive/cache search functionality
"""

import os
import json
import sqlite3
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import glob

class NexusVoiceCommands:
    """Voice command processing and archive search system"""
    
    def __init__(self):
        self.voice_db = "nexus_voice.db"
        self.archive_db = "nexus_archives.db"
        self.setup_voice_database()
        self.setup_archive_database()
        
    def setup_voice_database(self):
        """Initialize voice command database"""
        conn = sqlite3.connect(self.voice_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_phrase TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target_route TEXT,
                parameters TEXT,
                success_rate REAL DEFAULT 1.0,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                command_text TEXT,
                recognized_action TEXT,
                executed BOOLEAN DEFAULT FALSE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize default voice commands
        self.setup_default_commands()
    
    def setup_archive_database(self):
        """Initialize archive and cache search database"""
        conn = sqlite3.connect(self.archive_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS archived_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_path TEXT,
                content_text TEXT,
                file_type TEXT,
                file_size INTEGER,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                tags TEXT,
                summary TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                content TEXT,
                context TEXT,
                relevance_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_default_commands(self):
        """Setup default voice commands"""
        default_commands = [
            ("go to admin", "navigate", "/admin-direct", "{}"),
            ("open dashboard", "navigate", "/nexus-dashboard", "{}"),
            ("show executive", "navigate", "/executive-dashboard", "{}"),
            ("upload file", "navigate", "/upload", "{}"),
            ("open intelligence", "action", "intelligence_feed", "{}"),
            ("start automation", "action", "start_automation", "{}"),
            ("check status", "action", "system_status", "{}"),
            ("search archives", "action", "search_archives", "{}"),
            ("show validation", "action", "validation_panel", "{}"),
            ("run diagnostics", "action", "diagnostics", "{}"),
            ("analyze system", "action", "ai_analysis", "{}"),
            ("home page", "navigate", "/", "{}"),
            ("nexus home", "navigate", "/", "{}"),
            ("emergency admin", "navigate", "/admin-direct", '{"emergency": true}')
        ]
        
        conn = sqlite3.connect(self.voice_db)
        cursor = conn.cursor()
        
        for phrase, action_type, target, params in default_commands:
            cursor.execute('''
                INSERT OR IGNORE INTO voice_commands 
                (command_phrase, action_type, target_route, parameters)
                VALUES (?, ?, ?, ?)
            ''', (phrase, action_type, target, params))
        
        conn.commit()
        conn.close()
    
    def process_voice_command(self, voice_text: str) -> Dict[str, Any]:
        """Process voice command and return action"""
        voice_text = voice_text.lower().strip()
        
        conn = sqlite3.connect(self.voice_db)
        cursor = conn.cursor()
        
        # Find matching command
        cursor.execute('''
            SELECT command_phrase, action_type, target_route, parameters
            FROM voice_commands
            ORDER BY success_rate DESC, usage_count DESC
        ''')
        
        commands = cursor.fetchall()
        best_match = None
        highest_score = 0
        
        for phrase, action_type, target, params in commands:
            score = self.calculate_similarity(voice_text, phrase)
            if score > highest_score and score > 0.6:  # 60% similarity threshold
                highest_score = score
                best_match = (phrase, action_type, target, params)
        
        if best_match:
            phrase, action_type, target, params = best_match
            
            # Update usage count
            cursor.execute('''
                UPDATE voice_commands 
                SET usage_count = usage_count + 1
                WHERE command_phrase = ?
            ''', (phrase,))
            
            # Log session
            session_id = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            cursor.execute('''
                INSERT INTO voice_sessions 
                (session_id, command_text, recognized_action)
                VALUES (?, ?, ?)
            ''', (session_id, voice_text, f"{action_type}:{target}"))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "action_type": action_type,
                "target": target,
                "parameters": json.loads(params),
                "confidence": highest_score,
                "matched_phrase": phrase
            }
        
        conn.close()
        return {
            "success": False,
            "error": "No matching command found",
            "suggestions": self.get_command_suggestions(voice_text)
        }
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def get_command_suggestions(self, voice_text: str) -> List[str]:
        """Get command suggestions for unrecognized voice input"""
        conn = sqlite3.connect(self.voice_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT command_phrase FROM voice_commands LIMIT 5')
        suggestions = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return suggestions
    
    def search_archives(self, query: str, file_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search archived documents and cached memory"""
        results = []
        
        # Search archived documents
        conn = sqlite3.connect(self.archive_db)
        cursor = conn.cursor()
        
        # Build search query
        search_conditions = ["content_text LIKE ? OR file_name LIKE ? OR summary LIKE ?"]
        search_params = [f"%{query}%", f"%{query}%", f"%{query}%"]
        
        if file_types:
            file_type_conditions = " OR ".join(["file_type = ?" for _ in file_types])
            search_conditions.append(f"({file_type_conditions})")
            search_params.extend(file_types)
        
        search_query = f"""
            SELECT file_name, file_path, content_text, file_type, processed_at, summary
            FROM archived_documents 
            WHERE {" AND ".join(search_conditions)}
            ORDER BY processed_at DESC
            LIMIT 20
        """
        
        cursor.execute(search_query, search_params)
        documents = cursor.fetchall()
        
        for doc in documents:
            results.append({
                "type": "document",
                "file_name": doc[0],
                "file_path": doc[1],
                "content_preview": doc[2][:200] if doc[2] else "",
                "file_type": doc[3],
                "processed_at": doc[4],
                "summary": doc[5]
            })
        
        # Search cached memory
        cursor.execute('''
            SELECT memory_type, content, context, relevance_score, created_at
            FROM cached_memory
            WHERE content LIKE ? OR context LIKE ?
            ORDER BY relevance_score DESC, last_accessed DESC
            LIMIT 10
        ''', (f"%{query}%", f"%{query}%"))
        
        memories = cursor.fetchall()
        
        for memory in memories:
            results.append({
                "type": "memory",
                "memory_type": memory[0],
                "content": memory[1][:200],
                "context": memory[2],
                "relevance_score": memory[3],
                "created_at": memory[4]
            })
        
        conn.close()
        return results
    
    def index_legacy_report(self, file_path: str, content: str) -> bool:
        """Index a legacy report for archive search"""
        try:
            conn = sqlite3.connect(self.archive_db)
            cursor = conn.cursor()
            
            # Extract file information
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else len(content)
            file_type = file_path.split('.')[-1].lower() if '.' in file_path else 'unknown'
            
            # Generate summary (first 500 chars)
            summary = content[:500] + "..." if len(content) > 500 else content
            
            # Extract tags from content
            tags = self.extract_tags_from_content(content)
            
            cursor.execute('''
                INSERT INTO archived_documents 
                (file_name, file_path, content_text, file_type, file_size, summary, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (file_name, file_path, content, file_type, file_size, summary, json.dumps(tags)))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error indexing report: {e}")
            return False
    
    def extract_tags_from_content(self, content: str) -> List[str]:
        """Extract relevant tags from document content"""
        tags = []
        
        # Common business/technical terms
        tag_patterns = [
            r'\b(automation|analysis|report|data|system|process|workflow)\b',
            r'\b(revenue|profit|cost|budget|financial|economic)\b',
            r'\b(performance|efficiency|optimization|improvement)\b',
            r'\b(security|compliance|risk|audit|governance)\b',
            r'\b(api|database|integration|interface|platform)\b'
        ]
        
        content_lower = content.lower()
        
        for pattern in tag_patterns:
            matches = re.findall(pattern, content_lower)
            tags.extend(matches)
        
        # Remove duplicates and return
        return list(set(tags))
    
    def cache_memory(self, memory_type: str, content: str, context: str, relevance_score: float = 1.0):
        """Cache important information in memory for future search"""
        try:
            conn = sqlite3.connect(self.archive_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO cached_memory 
                (memory_type, content, context, relevance_score, last_accessed)
                VALUES (?, ?, ?, ?, ?)
            ''', (memory_type, content, context, relevance_score, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error caching memory: {e}")
            return False
    
    def get_voice_command_interface_html(self) -> str:
        """Generate HTML interface for voice commands"""
        return '''
<div id="voice-command-interface" style="position: fixed; top: 120px; left: 20px; width: 300px; background: rgba(26, 26, 46, 0.95); border: 1px solid #3742fa; border-radius: 8px; z-index: 46000; display: none; backdrop-filter: blur(10px);">
    <div style="padding: 12px; border-bottom: 1px solid #3742fa; color: #3742fa; font-weight: bold; display: flex; justify-content: space-between; align-items: center;">
        <span>🎤 Voice Commands</span>
        <span id="close-voice-interface" style="cursor: pointer; color: #ff4757;">×</span>
    </div>
    <div style="padding: 15px;">
        <div style="margin-bottom: 15px;">
            <button id="start-voice-recognition" style="width: 100%; padding: 10px; background: linear-gradient(45deg, #3742fa, #00d4ff); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                🎤 Start Voice Command
            </button>
        </div>
        <div id="voice-status" style="color: #888; font-size: 11px; margin-bottom: 10px;">
            Click to start voice recognition
        </div>
        <div id="recognized-text" style="background: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 4px; color: #fff; font-size: 12px; min-height: 40px; margin-bottom: 10px;">
            Voice input will appear here...
        </div>
        <div style="border-top: 1px solid rgba(55, 66, 250, 0.3); padding-top: 10px;">
            <div style="color: #3742fa; font-size: 10px; font-weight: bold; margin-bottom: 5px;">Quick Commands:</div>
            <div style="color: #ccc; font-size: 9px; line-height: 1.4;">
                • "go to admin" - Admin panel<br>
                • "open dashboard" - Main dashboard<br>
                • "upload file" - File upload<br>
                • "search archives" - Search docs<br>
                • "start automation" - Begin automation<br>
                • "check status" - System status
            </div>
        </div>
    </div>
</div>

<div id="archive-search-interface" style="position: fixed; top: 120px; right: 20px; width: 350px; background: rgba(26, 26, 46, 0.95); border: 1px solid #43e97b; border-radius: 8px; z-index: 45000; display: none; backdrop-filter: blur(10px);">
    <div style="padding: 12px; border-bottom: 1px solid #43e97b; color: #43e97b; font-weight: bold; display: flex; justify-content: space-between; align-items: center;">
        <span>🔍 Archive Search</span>
        <span id="close-archive-interface" style="cursor: pointer; color: #ff4757;">×</span>
    </div>
    <div style="padding: 15px;">
        <div style="margin-bottom: 15px;">
            <input type="text" id="archive-search-input" placeholder="Search archives, cache, memory..." style="width: 100%; padding: 8px; background: rgba(255, 255, 255, 0.1); border: 1px solid #43e97b; border-radius: 4px; color: white; font-size: 12px;">
        </div>
        <div style="margin-bottom: 15px;">
            <button id="search-archives-btn" style="width: 100%; padding: 8px; background: linear-gradient(45deg, #43e97b, #38f9d7); color: black; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                Search All Archives
            </button>
        </div>
        <div id="archive-results" style="max-height: 300px; overflow-y: auto; color: #fff; font-size: 11px;">
            <div style="text-align: center; color: #888; padding: 20px;">
                Enter search terms above
            </div>
        </div>
    </div>
</div>

<script>
let voiceCommandVisible = false;
let archiveSearchVisible = false;
let recognition = null;

function toggleVoiceInterface() {
    const panel = document.getElementById('voice-command-interface');
    voiceCommandVisible = !voiceCommandVisible;
    panel.style.display = voiceCommandVisible ? 'block' : 'none';
    
    if (voiceCommandVisible) {
        setupVoiceRecognition();
    }
}

function toggleArchiveSearch() {
    const panel = document.getElementById('archive-search-interface');
    archiveSearchVisible = !archiveSearchVisible;
    panel.style.display = archiveSearchVisible ? 'block' : 'none';
}

function setupVoiceRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onstart = function() {
            document.getElementById('voice-status').textContent = 'Listening... Speak your command';
            document.getElementById('start-voice-recognition').textContent = '🔴 Listening...';
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('recognized-text').textContent = transcript;
            processVoiceCommand(transcript);
        };
        
        recognition.onerror = function(event) {
            document.getElementById('voice-status').textContent = 'Error: ' + event.error;
            document.getElementById('start-voice-recognition').textContent = '🎤 Start Voice Command';
        };
        
        recognition.onend = function() {
            document.getElementById('voice-status').textContent = 'Voice recognition ended';
            document.getElementById('start-voice-recognition').textContent = '🎤 Start Voice Command';
        };
    } else {
        document.getElementById('voice-status').textContent = 'Voice recognition not supported';
    }
}

function processVoiceCommand(transcript) {
    fetch('/api/nexus/voice-command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice_text: transcript })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.action_type === 'navigate') {
                window.location.href = data.target;
            } else if (data.action_type === 'action') {
                executeVoiceAction(data.target, data.parameters);
            }
            
            document.getElementById('voice-status').textContent = 
                `Executed: ${data.matched_phrase} (${Math.round(data.confidence * 100)}% confidence)`;
        } else {
            document.getElementById('voice-status').textContent = 'Command not recognized';
        }
    })
    .catch(error => {
        document.getElementById('voice-status').textContent = 'Error processing command';
    });
}

function executeVoiceAction(action, parameters) {
    switch(action) {
        case 'intelligence_feed':
            toggleIntelligenceFeed();
            break;
        case 'validation_panel':
            toggleValidationPanel();
            break;
        case 'search_archives':
            toggleArchiveSearch();
            break;
        case 'system_status':
            logValidation('Voice Command: System Status', true);
            break;
        case 'start_automation':
            logValidation('Voice Command: Start Automation', true);
            break;
        case 'ai_analysis':
            logValidation('Voice Command: AI Analysis', true);
            break;
    }
}

function searchArchives() {
    const query = document.getElementById('archive-search-input').value;
    if (!query) return;
    
    fetch('/api/nexus/search-archives', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        displayArchiveResults(data.results);
    })
    .catch(error => {
        document.getElementById('archive-results').innerHTML = 
            '<div style="color: #ff4757;">Search error occurred</div>';
    });
}

function displayArchiveResults(results) {
    const container = document.getElementById('archive-results');
    
    if (!results || results.length === 0) {
        container.innerHTML = '<div style="color: #888; text-align: center; padding: 20px;">No results found</div>';
        return;
    }
    
    container.innerHTML = results.map(result => `
        <div style="margin-bottom: 12px; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 4px; border-left: 3px solid ${result.type === 'document' ? '#43e97b' : '#3742fa'};">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: ${result.type === 'document' ? '#43e97b' : '#3742fa'}; font-weight: bold; font-size: 10px;">
                    ${result.type.toUpperCase()}: ${result.file_name || result.memory_type}
                </span>
                <span style="color: #888; font-size: 9px;">
                    ${new Date(result.processed_at || result.created_at).toLocaleDateString()}
                </span>
            </div>
            <div style="color: #fff; font-size: 10px; line-height: 1.3;">
                ${result.content_preview || result.content}
            </div>
            ${result.summary ? `<div style="color: #ccc; font-size: 9px; margin-top: 4px; font-style: italic;">${result.summary}</div>` : ''}
        </div>
    `).join('');
}

// Event listeners
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.shiftKey && e.key === 'M') { e.preventDefault(); toggleVoiceInterface(); }
    if (e.ctrlKey && e.shiftKey && e.key === 'S') { e.preventDefault(); toggleArchiveSearch(); }
});

// Setup when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('start-voice-recognition').addEventListener('click', function() {
        if (recognition) {
            recognition.start();
        }
    });
    
    document.getElementById('search-archives-btn').addEventListener('click', searchArchives);
    
    document.getElementById('archive-search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchArchives();
        }
    });
    
    document.getElementById('close-voice-interface').addEventListener('click', toggleVoiceInterface);
    document.getElementById('close-archive-interface').addEventListener('click', toggleArchiveSearch);
});
</script>
'''

def create_voice_command_system():
    """Create voice command and archive search system"""
    return NexusVoiceCommands()

if __name__ == "__main__":
    voice_system = create_voice_command_system()
    print("NEXUS Voice Commands & Archive Search System Ready")