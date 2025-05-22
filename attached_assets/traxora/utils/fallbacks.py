def fallback_to_placeholder(data, placeholder):
    try:
        if not data:
            return placeholder
        return data
    except Exception:
        return placeholder
