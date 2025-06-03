# 🧪 TRAXORA Integration Test: Ingestion + Driver Classifier

from enhanced_data_ingestion import load_data
from agents import driver_classifier_agent

# Path to test data (adjust if running live)
TEST_FILE = "uploads/driver_reports/AssetsTimeOnSite (7).csv"

# Load using enhanced ingestion (auto handles CSV/Excel, fluff, time formats)
data = load_data(TEST_FILE, file_type="csv", skip_fluff_rows=5)

# Run classification
if data is not None:
    result = driver_classifier_agent.handle(data.to_dict(orient="records"))
    print("\n✅ Drivers Meeting Criteria:")
    for r in result.get("classified_drivers", []):
        print("-", r)

    print("\n❌ Drivers Skipped:")
    for s in result.get("skipped", []):
        print("-", s)

    print(f"\n🔢 Total Passed: {result.get('count', 0)}")
else:
    print("Failed to load data for classification.")
