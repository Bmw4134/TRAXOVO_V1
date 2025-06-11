/**
 * TRAXOVO Integrations Dashboard
 * Trello and Twilio integration functionality with real-time status updates
 */

// Load integration statuses on page load
document.addEventListener('DOMContentLoaded', function() {
    loadIntegrationStatuses();
    setInterval(loadIntegrationStatuses, 30000); // Update every 30 seconds
});

async function loadIntegrationStatuses() {
    try {
        // Load Trello integration status
        const trelloResponse = await fetch('/api/trello-integration');
        const trelloData = await trelloResponse.json();
        updateTrelloStatus(trelloData);

        // Load Twilio integration status
        const twilioResponse = await fetch('/api/twilio-integration');
        const twilioData = await twilioResponse.json();
        updateTwilioStatus(twilioData);

    } catch (error) {
        console.error('Error loading integration statuses:', error);
    }
}

function updateTrelloStatus(data) {
    const statusElement = document.getElementById('trello-status');
    const boardsElement = document.getElementById('trello-boards');
    const cardsElement = document.getElementById('trello-cards');
    
    if (!statusElement || !boardsElement || !cardsElement) return;
    
    if (data.status === 'success' && data.data.connection.status === 'connected') {
        statusElement.textContent = 'CONNECTED';
        statusElement.style.color = '#4CAF50';
        boardsElement.textContent = data.data.board_count || 0;
        cardsElement.textContent = data.data.boards.length * 10 || 0; // Estimate
    } else {
        statusElement.textContent = 'SETUP REQUIRED';
        statusElement.style.color = '#FF9800';
        boardsElement.textContent = '0';
        cardsElement.textContent = '0';
    }
}

function updateTwilioStatus(data) {
    const statusElement = document.getElementById('twilio-status');
    const messagesElement = document.getElementById('twilio-messages');
    const balanceElement = document.getElementById('twilio-balance');
    
    if (!statusElement || !messagesElement || !balanceElement) return;
    
    if (data.status === 'success' && data.data.connection.status === 'connected') {
        statusElement.textContent = 'CONNECTED';
        statusElement.style.color = '#4CAF50';
        messagesElement.textContent = data.data.message_count || 0;
        balanceElement.textContent = data.data.usage.account_balance || '$0.00';
    } else {
        statusElement.textContent = 'SETUP REQUIRED';
        statusElement.style.color = '#FF9800';
        messagesElement.textContent = '0';
        balanceElement.textContent = '$0.00';
    }
}

function openTrelloIntegration() {
    showIntegrationModal('trello');
}

function openTwilioIntegration() {
    showIntegrationModal('twilio');
}

function showIntegrationModal(type) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    if (type === 'trello') {
        modal.innerHTML = createTrelloModalContent();
    } else if (type === 'twilio') {
        modal.innerHTML = createTwilioModalContent();
    }
    
    modal.onclick = function(e) {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    };
    
    document.body.appendChild(modal);
}

function createTrelloModalContent() {
    return `
        <div style="background: white; border-radius: 8px; padding: 30px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto;">
            <h2 style="margin: 0 0 20px 0; color: #333;">Trello Project Management Integration</h2>
            
            <div style="margin-bottom: 20px;">
                <h3>Fleet Management Boards</h3>
                <p>Organize your fleet assets, maintenance schedules, and projects using Trello boards.</p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <button onclick="createTrelloBoard()" style="background: #0079bf; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-right: 10px;">
                    Create Fleet Board
                </button>
                <button onclick="syncAssetsToTrello()" style="background: #61bd4f; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
                    Sync Assets to Trello
                </button>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h4>Quick Actions:</h4>
                <ul>
                    <li>Track asset maintenance schedules</li>
                    <li>Manage project timelines</li>
                    <li>Collaborate with team members</li>
                    <li>Monitor fleet status updates</li>
                </ul>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
                <strong>Setup Required:</strong> Configure your Trello API credentials to enable full functionality.
                <br><small>Contact your administrator for API key setup.</small>
            </div>
            
            <button onclick="this.parentElement.parentElement.remove()" style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                Close
            </button>
        </div>
    `;
}

function createTwilioModalContent() {
    return `
        <div style="background: white; border-radius: 8px; padding: 30px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto;">
            <h2 style="margin: 0 0 20px 0; color: #333;">Twilio SMS Integration</h2>
            
            <div style="margin-bottom: 20px;">
                <h3>Fleet Communication & Alerts</h3>
                <p>Send SMS alerts to drivers, maintenance teams, and management for fleet operations.</p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <div style="margin-bottom: 10px;">
                    <label>Phone Number:</label>
                    <input type="tel" id="sms-phone" placeholder="+1234567890" style="width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ddd; border-radius: 4px;">
                </div>
                <div style="margin-bottom: 10px;">
                    <label>Message:</label>
                    <textarea id="sms-message" placeholder="Enter fleet alert message" style="width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ddd; border-radius: 4px; height: 80px;"></textarea>
                </div>
                <button onclick="sendFleetAlert()" style="background: #f22f46; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
                    Send Fleet Alert
                </button>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h4>Alert Types Available:</h4>
                <ul>
                    <li>Emergency notifications</li>
                    <li>Maintenance reminders</li>
                    <li>Route updates</li>
                    <li>Fleet status alerts</li>
                </ul>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
                <strong>Setup Required:</strong> Configure your Twilio credentials to enable SMS functionality.
                <br><small>Contact your administrator for account setup.</small>
            </div>
            
            <button onclick="this.parentElement.parentElement.remove()" style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                Close
            </button>
        </div>
    `;
}

async function createTrelloBoard() {
    try {
        const response = await fetch('/api/create-trello-board', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: 'TRAXOVO Fleet Management ' + new Date().toLocaleDateString()
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Trello board created successfully! URL: ' + result.board.url);
            loadIntegrationStatuses(); // Refresh status
        } else {
            alert('Setup required: ' + (result.error || 'Please configure Trello API credentials'));
        }
    } catch (error) {
        console.error('Error creating Trello board:', error);
        alert('Setup required: Please configure Trello API credentials');
    }
}

async function syncAssetsToTrello() {
    const boardId = prompt('Enter Trello Board ID (from board URL):');
    if (!boardId) return;
    
    try {
        const response = await fetch('/api/sync-assets-to-trello', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                board_id: boardId
            })
        });
        
        const result = await response.json();
        
        if (result.cards_created > 0) {
            alert(`Successfully synced ${result.cards_created} assets to Trello!`);
            loadIntegrationStatuses(); // Refresh status
        } else {
            alert('Setup required: ' + (result.error || 'Please configure Trello API credentials'));
        }
    } catch (error) {
        console.error('Error syncing assets:', error);
        alert('Setup required: Please configure Trello API credentials');
    }
}

async function sendFleetAlert() {
    const phone = document.getElementById('sms-phone').value;
    const message = document.getElementById('sms-message').value;
    
    if (!phone || !message) {
        alert('Please enter both phone number and message');
        return;
    }
    
    try {
        const response = await fetch('/api/send-fleet-alert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                phone: phone,
                message: message,
                type: 'fleet_alert'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Fleet alert sent successfully!');
            document.getElementById('sms-phone').value = '';
            document.getElementById('sms-message').value = '';
            loadIntegrationStatuses(); // Refresh status
        } else {
            alert('Setup required: ' + (result.error || 'Please configure Twilio credentials'));
        }
    } catch (error) {
        console.error('Error sending SMS:', error);
        alert('Setup required: Please configure Twilio credentials');
    }
}

// Add CSS for integration cards
const integrationStyles = document.createElement('style');
integrationStyles.textContent = `
    .trello-integration-card {
        border-left: 4px solid #0079bf !important;
        background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%) !important;
    }
    
    .twilio-integration-card {
        border-left: 4px solid #f22f46 !important;
        background: linear-gradient(135deg, #fff8f8 0%, #ffffff 100%) !important;
    }
    
    .integration-quick-stats {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 15px;
    }
    
    .integration-quick-stats .stat-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 8px;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 4px;
    }
    
    .integration-quick-stats .stat-label {
        font-size: 0.8em;
        color: #666;
        margin-bottom: 4px;
    }
    
    .integration-quick-stats .stat-value {
        font-weight: bold;
        font-size: 1.1em;
        color: #333;
    }
`;
document.head.appendChild(integrationStyles);