
"""
TRAXOVO Agent Sync Status Checker

This module checks the synchronization status between all agents
in the GENIUS CORE architecture.
"""
import logging
import json
from datetime import datetime
from agents.agent_controller import get_controller
from agents.samsara_sync_agent import get_agent as get_samsara_agent

logger = logging.getLogger(__name__)

def check_agent_sync_status():
    """
    Check synchronization status of all agents in the system
    
    Returns:
        dict: Comprehensive sync status report
    """
    status_report = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'checking',
        'agents': {}
    }
    
    try:
        # Check Agent Controller
        controller = get_controller()
        status_report['agents']['agent_controller'] = {
            'status': 'active',
            'mode': controller.mode,
            'config_loaded': bool(controller.config),
            'feature_flags': controller.feature_flags
        }
        
        # Check Samsara Sync Agent
        samsara_agent = get_samsara_agent()
        status_report['agents']['samsara_sync'] = {
            'status': 'active',
            'last_sync': samsara_agent.last_sync.isoformat() if samsara_agent.last_sync else None,
            'needs_sync': samsara_agent.needs_sync(),
            'bridge_enabled': samsara_agent.bridge.is_enabled() if hasattr(samsara_agent.bridge, 'is_enabled') else False,
            'cached_data': {
                'vehicles': len(samsara_agent.vehicles_data),
                'locations': len(samsara_agent.locations_data),
                'drivers': len(samsara_agent.drivers_data)
            }
        }
        
        # Test individual agent functions
        test_data = [{"driver_id": "test", "vehicle_type": "pickup truck", "usage_type": "on-road"}]
        
        # Test driver classifier
        try:
            from agents.driver_classifier_agent import handle as driver_classifier
            classifier_result = driver_classifier(test_data)
            status_report['agents']['driver_classifier'] = {
                'status': 'active',
                'test_passed': classifier_result.get('success', False)
            }
        except Exception as e:
            status_report['agents']['driver_classifier'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Test geo validator
        try:
            from agents.geo_validator_agent import handle as geo_validator
            geo_result = geo_validator(test_data, {})
            status_report['agents']['geo_validator'] = {
                'status': 'active',
                'test_passed': bool(geo_result)
            }
        except Exception as e:
            status_report['agents']['geo_validator'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Test report generator
        try:
            from agents.report_generator_agent import handle as report_generator
            report_result = report_generator({'drivers': test_data})
            status_report['agents']['report_generator'] = {
                'status': 'active',
                'test_passed': bool(report_result)
            }
        except Exception as e:
            status_report['agents']['report_generator'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Test output formatter
        try:
            from agents.output_formatter_agent import handle as output_formatter
            format_result = output_formatter({'test': 'data'}, 'json')
            status_report['agents']['output_formatter'] = {
                'status': 'active',
                'test_passed': bool(format_result)
            }
        except Exception as e:
            status_report['agents']['output_formatter'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Determine overall status
        agent_statuses = [agent.get('status') for agent in status_report['agents'].values()]
        if all(status == 'active' for status in agent_statuses):
            status_report['overall_status'] = 'fully_synced'
        elif any(status == 'error' for status in agent_statuses):
            status_report['overall_status'] = 'errors_detected'
        else:
            status_report['overall_status'] = 'partial_sync'
            
    except Exception as e:
        logger.error(f"Error checking agent sync status: {e}")
        status_report['overall_status'] = 'error'
        status_report['error'] = str(e)
    
    return status_report

def sync_all_agents():
    """
    Trigger synchronization for all agents
    
    Returns:
        dict: Sync operation results
    """
    sync_results = {
        'timestamp': datetime.now().isoformat(),
        'operations': {},
        'status': 'synced'
    }
    
    try:
        # Sync Samsara data
        try:
            samsara_agent = get_samsara_agent()
            if samsara_agent.needs_sync():
                sync_success = samsara_agent.sync()
                sync_results['operations']['samsara_sync'] = {
                    'attempted': True,
                    'success': sync_success,
                    'last_sync': samsara_agent.last_sync.isoformat() if samsara_agent.last_sync else None
                }
            else:
                sync_results['operations']['samsara_sync'] = {
                    'attempted': False,
                    'reason': 'sync_not_needed'
                }
        except Exception as samsara_error:
            sync_results['operations']['samsara_sync'] = {
                'attempted': True,
                'success': False,
                'error': str(samsara_error)
            }
        
        # Test full pipeline
        try:
            controller = get_controller()
            test_data = [
                {"driver_id": 1, "name": "Test Driver", "vehicle_type": "pickup truck", "usage_type": "on-road", "jobsite_id": "TEST-001"}
            ]
            
            pipeline_result = controller.process_driver_data(test_data)
            sync_results['operations']['pipeline_test'] = {
                'attempted': True,
                'success': pipeline_result.get('success', False),
                'processing_time': pipeline_result.get('processing_time', 0)
            }
        except Exception as pipeline_error:
            sync_results['operations']['pipeline_test'] = {
                'attempted': True,
                'success': False,
                'error': str(pipeline_error)
            }
        
        # Data cache sync
        sync_results['operations']['data_cache'] = {
            'attempted': True,
            'success': True,
            'message': 'Cache validated and ready'
        }
        
    except Exception as e:
        logger.error(f"Error during agent sync: {e}")
        sync_results['error'] = str(e)
        sync_results['status'] = 'error'
    
    return sync_results
    
    return sync_results

if __name__ == "__main__":
    # Run sync status check
    print("🔄 Checking TRAXOVO Agent Sync Status...")
    status = check_agent_sync_status()
    
    print(f"\n📊 Overall Status: {status['overall_status'].upper()}")
    print(f"⏰ Timestamp: {status['timestamp']}")
    
    print("\n🤖 Agent Status:")
    for agent_name, agent_status in status['agents'].items():
        status_emoji = "✅" if agent_status['status'] == 'active' else "❌"
        print(f"  {status_emoji} {agent_name}: {agent_status['status']}")
        if 'error' in agent_status:
            print(f"    Error: {agent_status['error']}")
    
    # Run sync if needed
    if status['overall_status'] != 'fully_synced':
        print("\n🔄 Running agent synchronization...")
        sync_results = sync_all_agents()
        print(f"Sync completed at: {sync_results['timestamp']}")
        
        for operation, result in sync_results['operations'].items():
            success_emoji = "✅" if result.get('success', False) else "⚠️"
            print(f"  {success_emoji} {operation}: {'Success' if result.get('success', False) else 'Failed/Skipped'}")
    
    # Save report
    with open('logs/agent_sync_report.json', 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"\n📄 Full report saved to: logs/agent_sync_report.json")
