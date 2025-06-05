# Patch for strict_mode and API sync stub in kaizen_gpt.py

# Add this in KaizenGPT.__init__:
self.strict_mode = True  # or load from config

# Add this to enforce strict mode at top of generation:
def validate_output(self, output):
    if self.strict_mode:
        if not isinstance(output, dict):
            raise ValueError("Output must be a dictionary.")
        if "result" not in output or "prompt" not in output:
            raise ValueError("Missing required output fields.")
    return True

# Add API sync stub:
def sync_to_api(self, endpoint, data):
    import requests
    try:
        response = requests.post(endpoint, json=data)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e)}
