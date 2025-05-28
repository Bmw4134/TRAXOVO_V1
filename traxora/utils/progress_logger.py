import sys
import time

def log_progress(current, total, label="Processing"):
    percent = 100 * (current / float(total))
    bar = '█' * int(percent / 4) + '-' * (25 - int(percent / 4))
    sys.stdout.write(f'\r{label}: |{bar}| {percent:.2f}% Complete')
    sys.stdout.flush()
    if current == total:
        print()
