# Prevents agent from destructive regressions
def guard_against_regression(current_state, proposed_action):
    if proposed_action in ['reset', 'overwrite'] and current_state['live']:
        raise Exception("⚠️ Action blocked: would overwrite live state.")
    return True
