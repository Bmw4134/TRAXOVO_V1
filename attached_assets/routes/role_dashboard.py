
def get_dashboard_view(user):
    if user.get("role") == "Admin":
        return "admin_overview.html"
    elif user.get("role") == "PM":
        return "pm_dashboard.html"
    else:
        return "driver_card.html"
