# Run this to check where login logic is handled
import os
os.system("grep -r 'login' . > /tmp/login_diff_log.txt")
print("🔍 Login usage diff written to /tmp/login_diff_log.txt")
