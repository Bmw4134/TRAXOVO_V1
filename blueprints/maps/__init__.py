
```python
from flask import Blueprint

maps_bp = Blueprint('maps', __name__)

@maps_bp.route('/map')
def map_view():
    return "Map Dashboard"
```
