def export_report(data, format_type="json"):
    if format_type == "json":
        import json
        return json.dumps(data)
    return "Unsupported format"
