# Parses and verifies visual logic cohesion
def analyze_click_routes(dom_model):
    inconsistencies = []
    for element in dom_model:
        if not element.get('route'):
            inconsistencies.append(element['id'])
    return inconsistencies
