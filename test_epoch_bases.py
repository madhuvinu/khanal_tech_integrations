#!/usr/bin/env python3
"""
Test script to find the correct HANA epoch base
"""

from datetime import datetime, timedelta, timezone

def test_epoch_bases():
    """Test different epoch bases to find the correct one"""
    
    # Known values from HANA data
    epoch_value = 104923  # CreateTS from HANA
    expected_date = "2025-07-28"  # CreateDate from HANA
    
    print("Testing HANA Epoch Conversion")
    print("=" * 50)
    print(f"Epoch value: {epoch_value}")
    print(f"Expected date: {expected_date}")
    print()
    
    # Test different epoch bases
    bases = [
        ("1900-01-01", datetime(1900, 1, 1, tzinfo=timezone.utc)),
        ("1970-01-01", datetime(1970, 1, 1, tzinfo=timezone.utc)),
        ("2000-01-01", datetime(2000, 1, 1, tzinfo=timezone.utc)),
        ("2020-01-01", datetime(2020, 1, 1, tzinfo=timezone.utc)),
    ]
    
    for base_name, base_date in bases:
        result = base_date + timedelta(seconds=epoch_value)
        print(f"{base_name}: {result.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "=" * 50)
    print("If none match exactly, the epoch might be:")
    print("1. Minutes instead of seconds")
    print("2. Hours instead of seconds") 
    print("3. Days instead of seconds")
    print("4. A different format entirely")

if __name__ == "__main__":
    test_epoch_bases()



