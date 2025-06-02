# Dashboard Catalog

## Available Modules

### asi_executive_dashboard.py
**Type**: ASI_Module
**Description**: ASI Executive Dashboard
**Features**: Object-Oriented Design, Flask Blueprint, Authentic Data Integration, AI Intelligence Layer
**API Endpoints**:
- @asi_executive_bp.route('/dashboard')
- @asi_executive_bp.route('/api/kpis')
- @asi_executive_bp.route('/api/recommendations')

---

### agi_asset_lifecycle_management.py
**Type**: AGI_Module
**Description**: AGI-Enhanced Asset Lifecycle Management System
**Features**: Object-Oriented Design, Flask Blueprint, Authentic Data Integration, AI Intelligence Layer
**API Endpoints**:
- @agi_asset_bp.route('/lifecycle-dashboard')
- @agi_asset_bp.route('/api/asset-metrics/<asset_id>')
- @agi_asset_bp.route('/api/fleet-optimization')

---

### agi_analytics_engine.py
**Type**: AGI_Module
**Description**: TRAXOVO AGI Analytics Engine
**Features**: Object-Oriented Design, Flask Blueprint, Authentic Data Integration, AI Intelligence Layer
**API Endpoints**:
- @agi_analytics_bp.route('/agi-analytics')
- @agi_analytics_bp.route('/api/agi-analytics-data')

---

### agi_workflow_automation.py
**Type**: AGI_Module
**Description**: TRAXOVO AGI Workflow Automation System
**Features**: Object-Oriented Design, Authentic Data Integration, AI Intelligence Layer, Mobile Responsive

---

### agi_module_mapper_rebuilder.py
**Type**: AGI_Module
**Description**: AGI Module Mapper and Rebuilder
**Features**: Object-Oriented Design, Flask Blueprint, Authentic Data Integration, AI Intelligence Layer, Mobile Responsive
**API Endpoints**:
- @equipment_dispatch_bp.route('/')
- @equipment_dispatch_bp.route('/api/optimal-dispatch', methods=['POST'])
- @driver_dispatch_bp.route('/')

---

### agi_quantum_deployment_sweep.py
**Type**: AGI_Module
**Description**: TRAXOVO AGI Quantum Deployment Sweep
**Features**: Object-Oriented Design, Flask Blueprint, AI Intelligence Layer, Mobile Responsive
**API Endpoints**:
- @agi_quantum_bp.route('/quantum-deployment')
- @agi_quantum_bp.route('/api/quantum-sweep', methods=['POST'])

---

### agi_enhanced_login.py
**Type**: AGI_Module
**Description**: AGI-Enhanced Login System with Smart Landing Page and KPI Previews
**Features**: Object-Oriented Design, Flask Blueprint, AI Intelligence Layer
**API Endpoints**:
- @agi_login_bp.route('/')
- @agi_login_bp.route('/login')
- @agi_login_bp.route('/login', methods=['POST'])

---

### comprehensive_asset_module.py
**Type**: General_Module
**Description**: Comprehensive Asset Management Module
**Features**: Object-Oriented Design, Flask Blueprint, Authentic Data Integration
**API Endpoints**:
- @asset_module_bp.route('/assets')
- @asset_module_bp.route('/api/assets')
- @asset_module_bp.route('/assets/<asset_number>')

---

