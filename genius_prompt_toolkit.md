
# GENIUS PROMPT TOOLKIT
_A Kaizen GPT module for recursive diagnostics, self-evolving prompts, and structural integrity across Replit dashboards._

---

## SECTION: ARCHITECTURE + BLUEPRINT CONTROL

### PROMPT: Blueprint Manifest + Consolidation

```plaintext
Replit, scan all current blueprints, templates, and routes.

1. Detect:
   - Overlapping route paths
   - Duplicate handler logic
   - Fragmented naming (e.g., job_module vs jobmgmt)

2. Output:
   - module_registry.json with:
     - blueprint name
     - file
     - routes exposed
     - templates used
     - fingerprint/goal if exists

3. Suggest merge ops or route cleanup.
```

---

### PROMPT: Module Drift Linter

```plaintext
Kaizen, compare every blueprint in app.py to templates/ directory and route list.

• Flag:
   - Any blueprint not rendering a real template
   - Orphaned templates not linked to a route
   - Duplicate template names (e.g. dashboard.html x3)

Output to: blueprint_health.json
```

---

## SECTION: PROMPT SELF-ANALYSIS

### PROMPT: Reflection on My Dev Philosophy

```plaintext
Based on my last 10 prompts, what style patterns define my workflow?
- Do I lean modular or rapid iterative?
- Am I reinforcing test coverage?
- Where do I reinforce or bypass validations?
- What should I double down on vs rethink?

Respond with: 1) strengths, 2) gaps, 3) style tags
```

---

### PROMPT: Prompt Rewriter (Given → When → Then)

```plaintext
Kaizen, review my last 5 prompts and refactor them to follow:

• Given (context)
• When (trigger/action)
• Then (expected output)

Also:
- Reduce step count per prompt
- Add fingerprint ID
- Enforce clear goal tag

Log refactored prompts to prompt_rewrites.json
```

---

## SECTION: VALIDATION + TESTING

### PROMPT: System Route Validator

```plaintext
Scan all routes in flask routes and validate:
- 200 OK
- Proper template render
- No stale endpoints (404/redirect)

Update route_validation_tests.py and rerun on every app.py or blueprint file change.
```

---

### PROMPT: Simulated Module Lifecycle

```plaintext
Kaizen, simulate the end-to-end lifecycle of:

Module: Driver Attendance
- File Upload
- Parse/Store
- Report generation

Log coverage and trigger points. Suggest what tests are missing or failing coverage.
```

---

## SECTION: INTELLIGENCE + RECURSION TRIGGERS

### PROMPT: Agent Awareness Loop

```plaintext
Replit, summarize how your recent responses have evolved:
- Are you increasing architectural depth?
- Are you reusing fingerprint data?
- Have your fixes reinforced test coverage?

If not, reboot your next response loop with structural awareness enabled.
```
