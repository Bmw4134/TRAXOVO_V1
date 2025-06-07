#!/usr/bin/env python3
"""
NEXUS Total Recall Protocol
Complete integration of voice commands, legacy automation, archive search, and visual validation
"""

import os
import json
import sqlite3
import glob
import zipfile
from datetime import datetime
from typing import Dict, List, Any, Optional
import nexus_voice_commands
import nexus_legacy_automation

class NexusTotalRecall:
    """Complete NEXUS Total Recall system with all integrations"""
    
    def __init__(self):
        self.recall_db = "nexus_total_recall.db"
        self.voice_system = nexus_voice_commands.NexusVoiceCommands()
        self.automation_system = nexus_legacy_automation.NexusLegacyAutomation()
        self.setup_recall_database()
        self.scan_uploaded_files()
        
    def setup_recall_database(self):
        """Initialize total recall tracking database"""
        conn = sqlite3.connect(self.recall_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recall_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                session_data TEXT,
                voice_commands_count INTEGER DEFAULT 0,
                archive_searches_count INTEGER DEFAULT 0,
                automations_triggered INTEGER DEFAULT 0,
                ui_interactions TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploaded_file_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT,
                file_type TEXT,
                processing_status TEXT,
                automation_opportunities TEXT,
                cached_content TEXT,
                indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_type TEXT NOT NULL,
                trigger_pattern TEXT,
                automation_action TEXT,
                success_rate REAL DEFAULT 1.0,
                last_executed DATETIME,
                execution_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def scan_uploaded_files(self):
        """Scan all uploaded files and cache for automation triggers"""
        uploaded_files = []
        
        # Scan attached_assets directory
        if os.path.exists('attached_assets'):
            for file_path in glob.glob('attached_assets/*'):
                if os.path.isfile(file_path):
                    uploaded_files.append(file_path)
        
        # Scan current directory for relevant files
        for pattern in ['*.zip', '*.py', '*.json', '*.xlsx', '*.csv', '*.pdf']:
            uploaded_files.extend(glob.glob(pattern))
        
        # Process each file
        for file_path in uploaded_files:
            self.cache_uploaded_file(file_path)
        
        # Cache legacy automation opportunities
        self.identify_legacy_automation_triggers()
    
    def cache_uploaded_file(self, file_path: str):
        """Cache uploaded file for future recall"""
        try:
            filename = os.path.basename(file_path)
            file_type = self.detect_file_type(filename)
            
            # Read file content if possible
            cached_content = ""
            automation_opportunities = []
            
            if file_type in ['python', 'json', 'text']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        cached_content = f.read()[:5000]  # First 5KB
                        
                    # Identify automation opportunities
                    if 'automation' in cached_content.lower():
                        automation_opportunities.append("Automation script detected")
                    if 'api' in cached_content.lower():
                        automation_opportunities.append("API integration opportunity")
                    if 'database' in cached_content.lower():
                        automation_opportunities.append("Database automation potential")
                        
                except:
                    pass
            
            # Store in cache database
            conn = sqlite3.connect(self.recall_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO uploaded_file_cache 
                (filename, file_path, file_type, processing_status, automation_opportunities, cached_content)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                filename,
                file_path,
                file_type,
                "cached",
                json.dumps(automation_opportunities),
                cached_content
            ))
            
            conn.commit()
            conn.close()
            
            # Index in voice system for archive search
            self.voice_system.index_legacy_report(file_path, cached_content)
            
        except Exception as e:
            print(f"Error caching file {file_path}: {e}")
    
    def detect_file_type(self, filename: str) -> str:
        """Detect file type from filename"""
        ext = filename.lower().split('.')[-1] if '.' in filename else 'unknown'
        
        type_mapping = {
            'py': 'python',
            'js': 'javascript',
            'html': 'html',
            'json': 'json',
            'zip': 'archive',
            'xlsx': 'excel',
            'csv': 'csv',
            'pdf': 'pdf',
            'txt': 'text',
            'md': 'markdown'
        }
        
        return type_mapping.get(ext, 'unknown')
    
    def identify_legacy_automation_triggers(self):
        """Identify potential legacy automation triggers from cached files"""
        conn = sqlite3.connect(self.recall_db)
        cursor = conn.cursor()
        
        # Get all cached files
        cursor.execute('SELECT filename, cached_content FROM uploaded_file_cache WHERE cached_content != ""')
        files = cursor.fetchall()
        
        automation_triggers = []
        
        for filename, content in files:
            content_lower = content.lower()
            
            # Report automation triggers
            if any(word in content_lower for word in ['report', 'dashboard', 'analytics']):
                automation_triggers.append({
                    "trigger_type": "report_automation",
                    "trigger_pattern": f"Report processing in {filename}",
                    "automation_action": "auto_generate_reports",
                    "source_file": filename
                })
            
            # Data processing triggers
            if any(word in content_lower for word in ['excel', 'csv', 'data', 'processing']):
                automation_triggers.append({
                    "trigger_type": "data_processing",
                    "trigger_pattern": f"Data processing in {filename}",
                    "automation_action": "auto_process_data",
                    "source_file": filename
                })
            
            # API integration triggers
            if any(word in content_lower for word in ['api', 'request', 'response', 'endpoint']):
                automation_triggers.append({
                    "trigger_type": "api_automation",
                    "trigger_pattern": f"API integration in {filename}",
                    "automation_action": "auto_api_calls",
                    "source_file": filename
                })
        
        # Store automation triggers
        for trigger in automation_triggers:
            cursor.execute('''
                INSERT OR REPLACE INTO automation_triggers 
                (trigger_type, trigger_pattern, automation_action)
                VALUES (?, ?, ?)
            ''', (
                trigger["trigger_type"],
                trigger["trigger_pattern"],
                trigger["automation_action"]
            ))
        
        conn.commit()
        conn.close()
        
        return automation_triggers
    
    def activate_voice_command_overlay(self) -> str:
        """Generate complete voice command overlay HTML"""
        return '''
<div id="nexus-total-recall-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 50000;">
    
    <!-- Voice Command Activation Indicator -->
    <div id="voice-active-indicator" style="position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: rgba(55, 66, 250, 0.9); color: white; padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: bold; display: none; pointer-events: auto; backdrop-filter: blur(10px);">
        🎤 Voice Command Active - Listening...
    </div>
    
    <!-- Gesture Mode Indicator -->
    <div id="gesture-mode-indicator" style="position: fixed; top: 60px; right: 20px; background: rgba(67, 233, 123, 0.9); color: black; padding: 6px 12px; border-radius: 15px; font-size: 11px; font-weight: bold; pointer-events: auto; backdrop-filter: blur(10px);">
        Gesture Mode: ON | D•A•I•E
    </div>
    
    <!-- Archive Search Status -->
    <div id="archive-search-status" style="position: fixed; bottom: 80px; left: 20px; background: rgba(67, 233, 123, 0.9); color: black; padding: 6px 12px; border-radius: 15px; font-size: 10px; font-weight: bold; pointer-events: auto; backdrop-filter: blur(10px); display: none;">
        🔍 Archive Search: <span id="search-result-count">0</span> results
    </div>
    
    <!-- Automation Status -->
    <div id="automation-status" style="position: fixed; bottom: 120px; left: 20px; background: rgba(250, 112, 154, 0.9); color: white; padding: 6px 12px; border-radius: 15px; font-size: 10px; font-weight: bold; pointer-events: auto; backdrop-filter: blur(10px); display: none;">
        ⚡ Automation: <span id="automation-count">0</span> active
    </div>
    
</div>

<!-- Total Recall Command Panel -->
<div id="total-recall-panel" style="position: fixed; top: 100px; left: 50%; transform: translateX(-50%); width: 400px; background: rgba(26, 26, 46, 0.95); border: 2px solid #3742fa; border-radius: 12px; z-index: 49500; display: none; backdrop-filter: blur(15px); pointer-events: auto;">
    <div style="padding: 15px; border-bottom: 1px solid #3742fa; color: #3742fa; font-weight: bold; text-align: center; display: flex; justify-content: space-between; align-items: center;">
        <span>🧠 NEXUS Total Recall Protocol</span>
        <span id="close-total-recall" style="cursor: pointer; color: #ff4757; font-size: 18px;">×</span>
    </div>
    <div style="padding: 20px;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
            <button onclick="activateVoiceRecall()" style="padding: 12px; background: linear-gradient(45deg, #3742fa, #00d4ff); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 12px;">
                🎤 Voice Recall
            </button>
            <button onclick="activateArchiveSearch()" style="padding: 12px; background: linear-gradient(45deg, #43e97b, #38f9d7); color: black; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 12px;">
                🔍 Archive Search
            </button>
            <button onclick="activateAutomationRecall()" style="padding: 12px; background: linear-gradient(45deg, #fa709a, #fee140); color: black; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 12px;">
                ⚡ Automation Recall
            </button>
            <button onclick="activateVisualValidation()" style="padding: 12px; background: linear-gradient(45deg, #667eea, #764ba2); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 12px;">
                👁️ Visual Validation
            </button>
        </div>
        <div id="recall-status" style="background: rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 6px; color: #fff; font-size: 11px; text-align: center;">
            Total Recall System Ready - All modules operational
        </div>
    </div>
</div>

<script>
let totalRecallActive = false;
let voiceRecallActive = false;
let automationRecallActive = false;

function toggleTotalRecall() {
    const panel = document.getElementById('total-recall-panel');
    totalRecallActive = !totalRecallActive;
    panel.style.display = totalRecallActive ? 'block' : 'none';
    
    if (totalRecallActive) {
        logValidation('Total Recall Activated', true);
        initializeTotalRecallSystems();
    }
}

function initializeTotalRecallSystems() {
    // Initialize all recall systems
    fetch('/api/nexus/total-recall/initialize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'initialize_all' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateRecallStatus(data.status);
            logValidation('Total Recall Systems Online', true);
        }
    })
    .catch(error => {
        logValidation('Total Recall Init Failed', false);
    });
}

function activateVoiceRecall() {
    voiceRecallActive = !voiceRecallActive;
    const indicator = document.getElementById('voice-active-indicator');
    
    if (voiceRecallActive) {
        indicator.style.display = 'block';
        toggleVoiceInterface();
        logValidation('Voice Recall Activated', true);
        
        // Auto-hide after 30 seconds
        setTimeout(() => {
            if (voiceRecallActive) {
                indicator.style.display = 'none';
                voiceRecallActive = false;
            }
        }, 30000);
    } else {
        indicator.style.display = 'none';
    }
}

function activateArchiveSearch() {
    const status = document.getElementById('archive-search-status');
    const isVisible = status.style.display !== 'none';
    status.style.display = isVisible ? 'none' : 'block';
    
    if (!isVisible) {
        toggleArchiveSearch();
        logValidation('Archive Search Activated', true);
        
        // Update search count
        fetch('/api/nexus/search-archives', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: 'automation' })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('search-result-count').textContent = data.total_results || 0;
        });
    }
}

function activateAutomationRecall() {
    const status = document.getElementById('automation-status');
    const isVisible = status.style.display !== 'none';
    status.style.display = isVisible ? 'none' : 'block';
    automationRecallActive = !automationRecallActive;
    
    if (automationRecallActive) {
        logValidation('Automation Recall Activated', true);
        
        // Get automation count
        fetch('/api/nexus/automation-status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('automation-count').textContent = data.active_automations || 0;
        });
    }
}

function activateVisualValidation() {
    toggleValidationPanel();
    logValidation('Visual Validation Activated', true);
}

function updateRecallStatus(status) {
    document.getElementById('recall-status').textContent = status;
}

// Enhanced keyboard shortcuts for total recall
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.shiftKey && e.key === 'T') { 
        e.preventDefault(); 
        toggleTotalRecall(); 
    }
    if (e.ctrlKey && e.shiftKey && e.key === 'R') { 
        e.preventDefault(); 
        activateVoiceRecall(); 
    }
});

// Close panel handler
document.getElementById('close-total-recall').addEventListener('click', toggleTotalRecall);

// Initialize total recall on load
setTimeout(() => {
    console.log('NEXUS Total Recall Protocol initialized');
    logValidation('Total Recall Protocol Ready', true);
}, 2000);
</script>
'''
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status for all systems"""
        try:
            conn = sqlite3.connect(self.recall_db)
            cursor = conn.cursor()
            
            # Get automation triggers count
            cursor.execute('SELECT COUNT(*) FROM automation_triggers')
            triggers_count = cursor.fetchone()[0]
            
            # Get cached files count
            cursor.execute('SELECT COUNT(*) FROM uploaded_file_cache')
            cached_files = cursor.fetchone()[0]
            
            # Get recent session activity
            cursor.execute('''
                SELECT session_type, voice_commands_count, archive_searches_count, automations_triggered
                FROM recall_sessions 
                ORDER BY last_activity DESC 
                LIMIT 1
            ''')
            recent_session = cursor.fetchone()
            
            conn.close()
            
            status = {
                "total_recall_active": True,
                "automation_triggers": triggers_count,
                "cached_files": cached_files,
                "voice_system": "operational",
                "archive_system": "operational",
                "legacy_automation": "operational",
                "recent_activity": {
                    "voice_commands": recent_session[1] if recent_session else 0,
                    "archive_searches": recent_session[2] if recent_session else 0,
                    "automations_triggered": recent_session[3] if recent_session else 0
                } if recent_session else {"voice_commands": 0, "archive_searches": 0, "automations_triggered": 0}
            }
            
            return status
            
        except Exception as e:
            return {
                "total_recall_active": False,
                "error": str(e)
            }
    
    def log_recall_session(self, session_type: str, session_data: Dict[str, Any]):
        """Log recall session activity"""
        try:
            conn = sqlite3.connect(self.recall_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO recall_sessions 
                (session_type, session_data, voice_commands_count, archive_searches_count, automations_triggered)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session_type,
                json.dumps(session_data),
                session_data.get('voice_commands', 0),
                session_data.get('archive_searches', 0),
                session_data.get('automations_triggered', 0)
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error logging recall session: {e}")
            return False

def create_total_recall_system():
    """Create complete NEXUS Total Recall system"""
    return NexusTotalRecall()

if __name__ == "__main__":
    total_recall = create_total_recall_system()
    print("NEXUS Total Recall Protocol Ready - All systems operational")