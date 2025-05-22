def export_report(report_data, output_format="json"):
    if output_format == "json":
        import json
        return json.dumps(report_data, indent=2)
    elif output_format == "text":
        return "\n".join([f"{k}: {v}" for k, v in report_data.items()])
    else:
        return "Unsupported format"
