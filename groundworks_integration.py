"""
TRAXOVO Groundworks Integration
Maps authentic Groundworks project locations to GAUGE API asset zones
"""

import json
from datetime import datetime
from typing import Dict, List, Any

class GroundworksLocationMapper:
    """Maps Groundworks project cities to GAUGE API asset zones"""
    
    def __init__(self):
        self.zone_mapping = {
            # Dallas/Fort Worth Metro - Zone 580
            'Dallas': 'zone_580',
            'Fort Worth': 'zone_580', 
            'Plano': 'zone_580',
            'North Richland': 'zone_580',
            '320 E Jefferson Blvd': 'zone_580',
            
            # Houston Metro - Zone 581
            'Houston': 'zone_581',
            'Baytown': 'zone_581',
            
            # Austin/Central Texas - Zone 582
            'Austin': 'zone_582',
            
            # Other Texas locations distributed
            'Vincennes': 'zone_580',  # Indiana projects
            'Evansville': 'zone_581',
            'Chandler': 'zone_582'
        }
        
        self.authentic_projects = [
            {
                'project_id': '2019-044',
                'description': 'E. Long Avenue',
                'division': 'Dallas Heavy Highway',
                'contract_amount': 6950939.61,
                'city': 'Fort Worth',
                'state': 'TX',
                'status': 'Active',
                'zone': 'zone_580'
            },
            {
                'project_id': '2021-017',
                'description': 'Plano Collin Creek Culvert Imp',
                'division': 'Dallas Heavy Highway',
                'contract_amount': 22480670.86,
                'city': 'Plano',
                'state': 'TX',
                'status': 'Active',
                'zone': 'zone_580'
            },
            {
                'project_id': '2022-023',
                'description': 'Dallas Riverfront & Cadiz Bridge',
                'division': 'Dallas Heavy Highway',
                'contract_amount': 22718717.84,
                'city': 'Dallas',
                'state': 'TX',
                'status': 'Active',
                'zone': 'zone_580'
            },
            {
                'project_id': '2024-036',
                'description': 'Terminal F Civil Utility Package',
                'division': 'Dallas Heavy Highway',
                'contract_amount': 125643362.00,
                'city': 'Dallas',
                'state': 'TX',
                'status': 'Active',
                'zone': 'zone_580'
            },
            {
                'project_id': '2025-008',
                'description': 'NTTA CTP Southbound Mainlanes',
                'division': 'Dallas Heavy Highway',
                'contract_amount': 96881137.21,
                'city': 'Plano',
                'state': 'TX',
                'status': 'Active',
                'zone': 'zone_580'
            },
            {
                'project_id': '2024-030',
                'description': 'Matagorda SH 35 Bridge Replace',
                'division': 'Houston Heavy Highway',
                'contract_amount': 30981397.22,
                'city': 'Austin',
                'state': 'TX',
                'status': 'Active',
                'zone': 'zone_582'
            },
            {
                'project_id': '2024-025',
                'description': 'Liberty FM 787 EMC Bridge',
                'division': 'Houston Heavy Highway',
                'contract_amount': 11985429.90,
                'city': 'Austin',
                'state': 'TX',
                'status': 'Active',
                'zone': 'zone_582'
            }
        ]

    def get_zone_projects(self, zone: str) -> List[Dict[str, Any]]:
        """Get all projects for a specific zone"""
        return [p for p in self.authentic_projects if p['zone'] == zone]
    
    def get_zone_contract_total(self, zone: str) -> float:
        """Get total contract value for a zone"""
        zone_projects = self.get_zone_projects(zone)
        return sum(p['contract_amount'] for p in zone_projects)
    
    def get_location_intelligence(self) -> Dict[str, Any]:
        """Generate location intelligence for Canvas dashboard"""
        
        zone_summary = {}
        total_contract_value = 0
        
        for zone in ['zone_580', 'zone_581', 'zone_582']:
            projects = self.get_zone_projects(zone)
            contract_total = self.get_zone_contract_total(zone)
            total_contract_value += contract_total
            
            zone_summary[zone] = {
                'project_count': len(projects),
                'contract_value': contract_total,
                'major_projects': [
                    {
                        'id': p['project_id'],
                        'description': p['description'],
                        'value': p['contract_amount']
                    } for p in sorted(projects, key=lambda x: x['contract_amount'], reverse=True)[:3]
                ],
                'cities': list(set(p['city'] for p in projects if p['city'])),
                'division_breakdown': self._get_division_breakdown(projects)
            }
        
        return {
            'total_projects': len(self.authentic_projects),
            'total_contract_value': total_contract_value,
            'zone_breakdown': zone_summary,
            'active_divisions': [
                'Dallas Heavy Highway',
                'Houston Heavy Highway', 
                'West Texas'
            ],
            'data_source': 'GROUNDWORKS_AUTHENTIC',
            'last_updated': datetime.now().isoformat(),
            'location_mapping': {
                'zone_580': 'Dallas/Fort Worth Metro',
                'zone_581': 'Houston Metro', 
                'zone_582': 'Austin/Central Texas'
            }
        }
    
    def _get_division_breakdown(self, projects: List[Dict]) -> Dict[str, int]:
        """Get breakdown of projects by division"""
        breakdown = {}
        for project in projects:
            division = project['division']
            breakdown[division] = breakdown.get(division, 0) + 1
        return breakdown

def get_groundworks_location_data():
    """Main function to get Groundworks location intelligence"""
    mapper = GroundworksLocationMapper()
    return mapper.get_location_intelligence()

def map_city_to_zone(city: str) -> str:
    """Map a city to its corresponding asset zone"""
    mapper = GroundworksLocationMapper()
    return mapper.zone_mapping.get(city, 'zone_580')  # Default to zone_580

if __name__ == "__main__":
    # Test the integration
    data = get_groundworks_location_data()
    print(json.dumps(data, indent=2))