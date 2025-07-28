#!/usr/bin/env python3

import json
import os
from lib.machine.storage import Storage

def test_storage_detection():
    """Test storage detection and print results"""
    print("Testing storage detection...")
    print("=" * 50)
    
    # Test the storage detection
    result = Storage.get_usage()
    
    print("Detected storage:")
    for name, info in result.items():
        total_gb = info['total'] / (1024**3)
        available_gb = info['available'] / (1024**3)
        used_gb = total_gb - available_gb
        
        print(f"  {name}:")
        print(f"    Icon: {info['icon']}")
        print(f"    Total: {total_gb:.2f} GB")
        print(f"    Used: {used_gb:.2f} GB")
        print(f"    Available: {available_gb:.2f} GB")
        print()
    
    # Check if expected mount points exist
    expected_mounts = ['/mnt/ssd', '/mnt']
    print("Mount point status:")
    for mount in expected_mounts:
        exists = os.path.exists(mount)
        print(f"  {mount}: {'✓' if exists else '✗'}")
    
    return result

if __name__ == "__main__":
    test_storage_detection()