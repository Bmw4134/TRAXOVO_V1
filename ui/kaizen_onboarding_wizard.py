# kaizen_onboarding_wizard.py
def run_onboarding():
    steps = [
        "📂 Upload your CSVs: DrivingHistory, GroundWorks, AssetsTimeOnSite",
        "🧠 Let kaizen_live_parser.py validate them",
        "📊 Click 'Dashboard' from the top bar to view metrics",
        "🧾 Go to 'Purchase Orders' to auto-create rental blocks",
        "🔁 Refresh the browser to see updated reports and summaries"
    ]
    for step in steps:
        print(step)
    print("✅ Onboarding complete — welcome to TRAXOVO dashboard control.")

if __name__ == "__main__":
    run_onboarding()
