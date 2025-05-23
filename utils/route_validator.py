from flask import current_app

def validate_routes(expected_routes):
    existing_routes = [rule.rule for rule in current_app.url_map.iter_rules()]
    missing_routes = [route for route in expected_routes if route not in existing_routes]
    if missing_routes:
        print(f"Missing routes detected: {missing_routes}")