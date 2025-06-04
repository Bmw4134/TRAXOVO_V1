#!/usr/bin/env python3
"""
Mobile Optimization Restoration Script
Restores system if intelligent fixes cause issues
"""

import os
import json
import logging

def restore_mobile_optimization():
    """Restore from mobile optimization backup"""
    print("Restoring mobile optimization state...")
    
    # Remove optimization files
    optimization_files = [
        'mobile_diagnostic_optimization.json',
        'smart_mobile_resolution.json', 
        'mobile_optimization_cache.json',
        'adaptive_mobile_diagnostic.json'
    ]
    
    for file in optimization_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed optimization file: {file}")
    
    print("Mobile optimization restoration completed")
    print("System restored to pre-optimization state")

def restore_full_dna():
    """Restore complete TRAXOVO DNA if needed"""
    dna_backup = 'traxovo_dna_backup_20250604_094841'
    if os.path.exists(dna_backup):
        print(f"Full DNA backup available: {dna_backup}")
        print("To restore complete system:")
        print(f"  cd {dna_backup}")
        print("  python3 restore_traxovo_dna.py")
    else:
        print("DNA backup not found")

if __name__ == "__main__":
    restore_mobile_optimization()
    restore_full_dna()
