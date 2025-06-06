"""
User Data Connector Routes
Provides endpoints for authentic user data integration
"""

from flask import request, jsonify, render_template_string
from authentic_user_data_integration import AuthenticUserDataProcessor, get_user_data_requirements

def create_user_data_routes(app):
    """Add user data integration routes to Flask app"""
    
    processor = AuthenticUserDataProcessor()
    
    @app.route('/user-data-integration')
    def user_data_integration():
        """User data integration interface"""
        requirements = get_user_data_requirements()
        stored_users = processor.get_stored_users()
        
        return render_template_string('''<!DOCTYPE html>
<html>
<head>
    <title>User Data Integration - TRAXOVO</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="/static/style.css">
    <style>
        .integration-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .credential-form {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .sync-button {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 500;
        }
        .user-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
        }
        .user-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Authentic User Data Integration</h1>
            <p>Connect to your organization's user management systems</p>
        </div>
        
        <div class="integration-card">
            <h3>Current Status</h3>
            <p>Stored Users: {{ stored_users|length }}</p>
            <p>Last Sync: {{ last_sync if last_sync else 'Never' }}</p>
        </div>
        
        <div class="integration-card">
            <h3>Azure Active Directory Integration</h3>
            <form id="azure-form" class="credential-form">
                <div class="form-group">
                    <label for="tenant_id">Tenant ID</label>
                    <input type="text" id="tenant_id" name="tenant_id" placeholder="your-tenant-id">
                </div>
                <div class="form-group">
                    <label for="client_id">Client ID</label>
                    <input type="text" id="client_id" name="client_id" placeholder="your-application-client-id">
                </div>
                <div class="form-group">
                    <label for="client_secret">Client Secret</label>
                    <input type="password" id="client_secret" name="client_secret" placeholder="your-client-secret">
                </div>
                <button type="button" class="sync-button" onclick="syncAzureAD()">Sync Azure AD Users</button>
            </form>
        </div>
        
        <div class="integration-card">
            <h3>Google Workspace Integration</h3>
            <form id="google-form" class="credential-form">
                <div class="form-group">
                    <label for="service_account">Service Account JSON</label>
                    <textarea id="service_account" name="service_account" rows="4" placeholder="Paste your service account JSON here"></textarea>
                </div>
                <div class="form-group">
                    <label for="domain">Domain</label>
                    <input type="text" id="domain" name="domain" placeholder="your-company.com">
                </div>
                <button type="button" class="sync-button" onclick="syncGoogleWorkspace()">Sync Google Workspace Users</button>
            </form>
        </div>
        
        <div class="integration-card">
            <h3>CSV/Excel File Upload</h3>
            <form id="file-upload-form" class="credential-form" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="user_file">User Data File (CSV or Excel)</label>
                    <input type="file" id="user_file" name="user_file" accept=".csv,.xlsx,.xls">
                </div>
                <p>Required columns: email, full_name, department, role</p>
                <button type="button" class="sync-button" onclick="uploadUserFile()">Upload and Process File</button>
            </form>
        </div>
        
        <div class="integration-card">
            <h3>Current Users</h3>
            <div class="user-list">
                {% for user in stored_users %}
                <div class="user-item">
                    <div>
                        <strong>{{ user.full_name or user.email }}</strong><br>
                        <small>{{ user.email }} - {{ user.department }} - {{ user.role }}</small>
                    </div>
                    <div>
                        <small>{{ user.data_source }}</small>
                    </div>
                </div>
                {% endfor %}
                {% if not stored_users %}
                <p>No users found. Please sync from a data source above.</p>
                {% endif %}
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="/" class="nav-link">Back to Dashboard</a>
        </div>
    </div>
    
    <script>
        async function syncAzureAD() {
            const tenantId = document.getElementById('tenant_id').value;
            const clientId = document.getElementById('client_id').value;
            const clientSecret = document.getElementById('client_secret').value;
            
            if (!tenantId || !clientId || !clientSecret) {
                alert('Please fill in all Azure AD credentials');
                return;
            }
            
            try {
                const response = await fetch('/sync-azure-users', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        tenant_id: tenantId,
                        client_id: clientId,
                        client_secret: clientSecret
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    alert(`Successfully synced ${result.users_count} users from Azure AD`);
                    location.reload();
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert(`Network error: ${error.message}`);
            }
        }
        
        async function syncGoogleWorkspace() {
            const serviceAccount = document.getElementById('service_account').value;
            const domain = document.getElementById('domain').value;
            
            if (!serviceAccount || !domain) {
                alert('Please provide service account JSON and domain');
                return;
            }
            
            try {
                const response = await fetch('/sync-google-users', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        service_account: serviceAccount,
                        domain: domain
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    alert(`Successfully synced ${result.users_count} users from Google Workspace`);
                    location.reload();
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert(`Network error: ${error.message}`);
            }
        }
        
        async function uploadUserFile() {
            const fileInput = document.getElementById('user_file');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file to upload');
                return;
            }
            
            const formData = new FormData();
            formData.append('user_file', file);
            
            try {
                const response = await fetch('/upload-user-file', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (result.success) {
                    alert(`Successfully processed ${result.users_count} users from file`);
                    location.reload();
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert(`Network error: ${error.message}`);
            }
        }
    </script>
</body>
</html>''', requirements=requirements, stored_users=stored_users, last_sync=None)
    
    @app.route('/sync-azure-users', methods=['POST'])
    def sync_azure_users():
        """Sync users from Azure Active Directory"""
        try:
            data = request.get_json()
            
            users = processor.connect_to_azure_ad(
                data.get('tenant_id'),
                data.get('client_id'), 
                data.get('client_secret')
            )
            
            if users:
                processor.store_authentic_users(users)
                return jsonify({'success': True, 'users_count': len(users)})
            else:
                return jsonify({'success': False, 'error': 'No users found or connection failed'})
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/sync-google-users', methods=['POST'])
    def sync_google_users():
        """Sync users from Google Workspace"""
        try:
            data = request.get_json()
            
            # Save service account temporarily
            service_account_path = 'temp_service_account.json'
            with open(service_account_path, 'w') as f:
                f.write(data.get('service_account'))
            
            users = processor.connect_to_google_workspace(
                service_account_path,
                data.get('domain')
            )
            
            # Clean up temp file
            import os
            if os.path.exists(service_account_path):
                os.remove(service_account_path)
            
            if users:
                processor.store_authentic_users(users)
                return jsonify({'success': True, 'users_count': len(users)})
            else:
                return jsonify({'success': False, 'error': 'No users found or connection failed'})
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/upload-user-file', methods=['POST'])
    def upload_user_file():
        """Process uploaded user data file"""
        try:
            if 'user_file' not in request.files:
                return jsonify({'success': False, 'error': 'No file uploaded'})
            
            file = request.files['user_file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'})
            
            # Save uploaded file temporarily
            filename = f"temp_users_{file.filename}"
            file.save(filename)
            
            # Process based on file type
            if filename.endswith('.csv'):
                users = processor.process_csv_user_data(filename)
            elif filename.endswith(('.xlsx', '.xls')):
                users = processor.process_excel_user_data(filename)
            else:
                return jsonify({'success': False, 'error': 'Unsupported file format'})
            
            # Clean up temp file
            import os
            if os.path.exists(filename):
                os.remove(filename)
            
            if users:
                processor.store_authentic_users(users)
                return jsonify({'success': True, 'users_count': len(users)})
            else:
                return jsonify({'success': False, 'error': 'No valid user data found in file'})
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/authentic-users')
    def get_authentic_users():
        """API endpoint to get authentic users"""
        users = processor.get_stored_users()
        return jsonify({'users': users, 'count': len(users)})