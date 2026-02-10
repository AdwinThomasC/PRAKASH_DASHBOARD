
import sys
import os

try:
    from who_standards import calculate_bmi_z_score, classify_who_z_score
    print("Import successful.")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_who_logic():
    test_cases = [
        # (BMI, Gender, Age_Months, Expected_Desc)
        (15.3, "girls", 60, "Normal (Median)"),
        (12.0, "girls", 60, "Thinness/Wasted"),
        (20.0, "girls", 60, "Overweight"),
        (25.0, "boys", 228, "Overweight (19y)"),
        (13.4, "boys", 0, "Normal (Birth)"),
        (None, "girls", 60, "None Input"),
        (15.0, "unknown", 60, "Unknown Gender"),
    ]

    print("\nRunning Test Cases:")
    for bmi, gender, age, desc in test_cases:
        try:
            z = calculate_bmi_z_score(bmi, gender, age)
            cat = classify_who_z_score(z, age) if z is not None else "Unknown"
            print(f"Case: {desc} | BMI: {bmi}, Age: {age}m, Sex: {gender} -> Z: {z}, Cat: {cat}")
        except Exception as e:
            print(f"Case: {desc} FAILED with error: {e}")

if __name__ == "__main__":
    test_who_logic()
