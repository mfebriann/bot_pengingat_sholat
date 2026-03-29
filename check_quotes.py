import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.prayer import get_random_quote

print("--- Testing Prayer Specific Quotes ---")

# Test Fajr
print("\nTesting for Fajr:")
for _ in range(5):
    q = get_random_quote("Fajr")
    if q:
        print(f"[{q.prayer_time}] {q.content[:50]}...")
    else:
        print("No quote found.")

# Test Asr
print("\nTesting for Asr:")
for _ in range(5):
    q = get_random_quote("Asr")
    if q:
        print(f"[{q.prayer_time}] {q.content[:50]}...")
    else:
        print("No quote found.")

# Test Maghrib (should only get general ones)
print("\nTesting for Maghrib (should be general):")
for _ in range(5):
    q = get_random_quote("Maghrib")
    if q:
        print(f"[{q.prayer_time}] {q.content[:50]}...")
    else:
        print("No quote found.")
