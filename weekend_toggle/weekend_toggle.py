"""
Weekend Toggle Module for TRAXOVO
Provides persistent weekend column visibility control
"""

def generate_weekend_toggle_script():
    return """
    function toggleWeekends() {
        const showWeekends = document.getElementById('show-weekends').checked;
        const weekendCols = document.querySelectorAll('.weekend-col');
        
        weekendCols.forEach(col => {
            col.style.display = showWeekends ? '' : 'none';
        });
        
        // Save preference to localStorage for persistence
        localStorage.setItem('traxovo_show_weekends', showWeekends);
        console.log('Weekend columns:', showWeekends ? 'shown' : 'hidden');
    }

    // Restore weekend toggle state on page load
    document.addEventListener('DOMContentLoaded', function() {
        const savedPreference = localStorage.getItem('traxovo_show_weekends');
        if (savedPreference !== null) {
            const checkbox = document.getElementById('show-weekends');
            if (checkbox) {
                checkbox.checked = savedPreference === 'true';
                toggleWeekends();
            }
        }
    });
    """

def get_weekend_toggle_html():
    return """
    <div class="form-check ms-3">
        <input class="form-check-input" type="checkbox" id="show-weekends" checked onchange="toggleWeekends()">
        <label class="form-check-label" for="show-weekends">
            <small>Show Weekends</small>
        </label>
    </div>
    """
