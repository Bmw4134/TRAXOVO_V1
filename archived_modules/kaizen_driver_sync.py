import os
import zipfile

def sync_driver_reports():
    src_dirs = ["GroundWorks", "DrivingHistory", "AssetsTimeOnSite", "ActivityDetail"]
    with zipfile.ZipFile("driver_reports.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for folder in src_dirs:
            if os.path.exists(folder):
                for root, _, files in os.walk(folder):
                    for file in files:
                        full_path = os.path.join(root, file)
                        archive.write(full_path, os.path.relpath(full_path, folder))
    print("[Kaizen] Driver reports synced to driver_reports.zip")

if __name__ == "__main__":
    sync_driver_reports()
