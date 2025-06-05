"""
JavaScript Conflict Resolver
Fixes JavaScript function conflicts across TRAXOVO platform
"""

from flask import Flask

def create_js_fix_routes(app):
    """Add JavaScript fix routes"""
    
    @app.route('/js/common-functions.js')
    def common_js_functions():
        """Common JavaScript functions to prevent conflicts"""
        return '''
// Common JavaScript functions for TRAXOVO platform
function toggleCommandMenu() {
    const menu = document.getElementById('commandMenu');
    if (menu) {
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }
}

function toggleFullscreen() {
    if (document.fullscreenElement) {
        document.exitFullscreen();
    } else {
        document.documentElement.requestFullscreen();
    }
}

function openSystem(systemName) {
    const systemUrls = {
        'master-brain': '/master-brain',
        'fleet-operations': '/gauge-assets',
        'failure-analysis': '/failure-analysis',
        'dashboard-customizer': '/dashboard-customizer',
        'github-sync': '/github-sync',
        'trd-system': '/trd',
        'bmi-sweep': '/bmi/sweep',
        'watson-console': '/watson/console',
        'user-management': '/role-management',
        'watson-force-render': '/watson/force-render',
        'system-inspector': '/bare-bones-inspector',
        'internal-integration': '/internal-repos',
        'automation': '/automation-dashboard'
    };
    
    const url = systemUrls[systemName];
    if (url) {
        window.open(url, '_blank');
    } else {
        alert('System not found: ' + systemName);
    }
}

function downloadUniversalComponents() {
    window.open('/api/download/universal-components', '_blank');
}

function downloadFullIntelligencePackage() {
    window.open('/api/download/full-intelligence-package', '_blank');
}

// Automation functions
async function analyzeTask() {
    const taskDescription = document.getElementById('taskDescription');
    if (!taskDescription || !taskDescription.value) {
        alert('Please describe the task you want to automate');
        return;
    }
    
    try {
        const response = await fetch('/api/automation/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({task_description: taskDescription.value})
        });
        
        const result = await response.json();
        
        const analysisResult = document.getElementById('analysisResult');
        if (analysisResult) {
            analysisResult.innerHTML = `
                <div class="analysis-result">
                    <h4>Automation Analysis</h4>
                    <p><strong>Type:</strong> ${result.automation_type}</p>
                    <p><strong>Feasible:</strong> <span class="status-active">Yes</span></p>
                    <p><strong>Estimated Time:</strong> ${result.estimated_time}</p>
                    <p><strong>Complexity:</strong> <span class="complexity-${result.complexity.toLowerCase()}">${result.complexity}</span></p>
                    <h5>Implementation Steps:</h5>
                    <ul>
                        ${result.implementation_plan.steps.map(step => `<li>${step}</li>`).join('')}
                    </ul>
                    <h5>Benefits:</h5>
                    <ul>
                        ${result.benefits.map(benefit => `<li>${benefit}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
    } catch (error) {
        alert('Analysis failed: ' + error.message);
    }
}

async function implementAutomation() {
    const taskDescription = document.getElementById('taskDescription');
    if (!taskDescription || !taskDescription.value) {
        alert('Please describe the task you want to automate');
        return;
    }
    
    try {
        const response = await fetch('/api/automation/implement', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({task_description: taskDescription.value})
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Automation implemented successfully!\\n\\nAutomation ID: ${result.automation_id}\\nStatus: ${result.status}\\nNext Execution: ${result.next_execution}`);
            if (typeof loadAutomationHistory === 'function') loadAutomationHistory();
            taskDescription.value = '';
            const analysisResult = document.getElementById('analysisResult');
            if (analysisResult) analysisResult.innerHTML = '';
        } else {
            alert('Implementation failed: ' + result.message);
        }
    } catch (error) {
        alert('Implementation failed: ' + error.message);
    }
}
''', 200, {'Content-Type': 'application/javascript'}