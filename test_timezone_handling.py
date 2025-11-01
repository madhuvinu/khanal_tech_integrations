#!/usr/bin/env python3
"""
Test script to verify timezone handling in HANA sync
"""

from datetime import datetime, timezone, timedelta

def normalize_datetime_to_utc(dt):
    """
    Normalize a datetime object to UTC timezone for comparison
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # If naive datetime, assume it's already UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # If timezone-aware, convert to UTC
        return dt.astimezone(timezone.utc)

def test_timezone_handling():
    """Test timezone handling with different scenarios"""
    
    print("Testing Timezone Handling")
    print("=" * 50)
    
    # Test case 1: Naive datetime (assumed UTC)
    naive_dt = datetime(2025, 10, 23, 15, 49, 6)
    normalized_naive = normalize_datetime_to_utc(naive_dt)
    print(f"Naive datetime: {naive_dt} -> {normalized_naive}")
    
    # Test case 2: Simulate Asia/Kolkata timezone (UTC+5:30)
    kolkata_offset = timezone(timedelta(hours=5, minutes=30))
    kolkata_dt = datetime(2025, 10, 23, 15, 49, 6, tzinfo=kolkata_offset)
    normalized_kolkata = normalize_datetime_to_utc(kolkata_dt)
    print(f"Kolkata datetime: {kolkata_dt} -> {normalized_kolkata}")
    
    # Test case 3: UTC timezone
    utc_dt = datetime(2025, 10, 23, 10, 19, 6, tzinfo=timezone.utc)
    normalized_utc = normalize_datetime_to_utc(utc_dt)
    print(f"UTC datetime: {utc_dt} -> {normalized_utc}")
    
    print("\n" + "=" * 50)
    print("Timezone handling test completed!")

if __name__ == "__main__":
    test_timezone_handling()
