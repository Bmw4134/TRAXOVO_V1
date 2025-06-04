#!/usr/bin/env python3
"""
Complete Puppeteer Removal - Eliminate deployment bottleneck
Removes all puppeteer dependencies and references
"""

import os
import subprocess
import json
import shutil

def remove_puppeteer_completely():
    """Remove puppeteer completely from the system"""
    print("Removing puppeteer completely...")
    
    # 1. Force remove node_modules/puppeteer
    puppeteer_paths = [
        'node_modules/puppeteer',
        'node_modules/chromium-bidi',
        'node_modules/.puppeteer',
        '.puppeteer'
    ]
    
    for path in puppeteer_paths:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                print(f"Removed: {path}")
            except:
                print(f"Could not remove: {path}")
    
    # 2. Remove puppeteer references from TypeScript files
    ts_files = ['traxovo-unified-automation.ts']
    for ts_file in ts_files:
        if os.path.exists(ts_file):
            try:
                with open(ts_file, 'r') as f:
                    content = f.read()
                
                # Remove puppeteer imports and usage
                content = content.replace("import puppeteer from 'puppeteer';", "// puppeteer removed")
                content = content.replace("const browser = await puppeteer.launch", "// const browser = await puppeteer.launch")
                content = content.replace("await browser.newPage()", "// await browser.newPage()")
                content = content.replace("await browser.close()", "// await browser.close()")
                
                with open(ts_file, 'w') as f:
                    f.write(content)
                print(f"Cleaned puppeteer from: {ts_file}")
            except:
                print(f"Could not clean: {ts_file}")
    
    # 3. Set environment variables to disable puppeteer
    env_vars = {
        'DISABLE_PUPPETEER': '1',
        'SKIP_CHROMIUM_DOWNLOAD': '1',
        'PUPPETEER_SKIP_DOWNLOAD': '1',
        'PUPPETEER_SKIP_CHROMIUM_DOWNLOAD': '1'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"Set {key}={value}")
    
    # 4. Clean npm cache
    try:
        subprocess.run(['npm', 'cache', 'clean', '--force'], timeout=30, capture_output=True)
        print("NPM cache cleaned")
    except:
        print("Could not clean npm cache")
    
    print("Puppeteer removal completed")
    return True

if __name__ == "__main__":
    remove_puppeteer_completely()