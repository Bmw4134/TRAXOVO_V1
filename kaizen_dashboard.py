import os

def run():
    print("\n[KAIZEN EXEC DASHBOARD V2]")
    print("1. Dev Mode")
    print("2. Bundle for Deploy")
    print("3. Compress All AI Modules")
    print("4. Restore All AI Modules")
    print("5. Compress Reports")
    print("6. Restore Reports")
    print("7. Compress Meta Configs")
    print("8. Restore Meta Configs")
    print("9. Full Restore Stack")
    choice = input("Choose an option (1-9): ")
    scripts = {
        "1": "bash dev_run.sh",
        "2": "bash make_prod_bundle.sh",
        "3": "bash compress_core_ai.sh",
        "4": "bash restore_core_ai.sh",
        "5": "bash compress_reports.sh",
        "6": "bash restore_reports.sh",
        "7": "bash compress_meta.sh",
        "8": "bash restore_meta.sh",
        "9": "bash restore_full_stack.sh"
    }
    os.system(scripts.get(choice, "echo Invalid selection"))

if __name__ == "__main__":
    run()
