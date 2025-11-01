#!/usr/bin/env python3
"""
Test script to verify HANA epoch timestamp conversion
"""

from datetime import datetime, timedelta, timezone

def convert_epoch_to_utc(epoch_value):
    """
    Convert HANA epoch timestamp (seconds since 1900-01-01) to UTC datetime
    """
    if epoch_value is None:
        return None
    try:
        # Handle edge case where epoch_value might be 0 or empty
        epoch_int = int(epoch_value) if epoch_value else 0
        # HANA epoch = seconds since 1900-01-01
        sap_epoch = datetime(1900, 1, 1, tzinfo=timezone.utc)
        return sap_epoch + timedelta(seconds=epoch_int)
    except (ValueError, TypeError) as e:
        print(f"Error converting epoch {epoch_value}: {str(e)}")
        return None

def test_epoch_conversion():
    """Test the epoch conversion with sample values"""
    
    # Test cases with known epoch values
    test_cases = [
        104750,    # Example from your description
        144849,    # Another example from your description
        0,         # Should be 1900-01-01 00:00:00
        86400,     # Should be 1900-01-02 00:00:00 (1 day)
        31536000,  # Should be 1901-01-01 00:00:00 (1 year)
    ]
    
    print("Testing HANA Epoch to UTC Conversion")
    print("=" * 50)
    
    for epoch in test_cases:
        converted = convert_epoch_to_utc(epoch)
        if converted:
            print(f"Epoch: {epoch:>8} -> {converted.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        else:
            print(f"Epoch: {epoch:>8} -> FAILED")
    
    print("\n" + "=" * 50)
    print("Conversion test completed!")

if __name__ == "__main__":
    test_epoch_conversion()