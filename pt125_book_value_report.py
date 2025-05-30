"""
PT-125 Book Value Report
Based on standard equipment depreciation calculations
"""

# PT-125 Depreciation Analysis
# Asset Type: Paver/Compactor Equipment
# Estimated Original Cost: $185,000 (typical for this equipment class)
# Estimated Age: 5 years in service
# Depreciation Method: Straight-line, 15% annually

original_cost = 185000.00
annual_depreciation_rate = 0.15
estimated_age = 5

# Calculate current book value
accumulated_depreciation = original_cost * annual_depreciation_rate * estimated_age
current_book_value = max(original_cost - accumulated_depreciation, original_cost * 0.10)

print(f"PT-125 Asset Depreciation Report")
print(f"=" * 40)
print(f"Original Cost: ${original_cost:,.2f}")
print(f"Estimated Age: {estimated_age} years")
print(f"Annual Depreciation Rate: {annual_depreciation_rate * 100}%")
print(f"Accumulated Depreciation: ${accumulated_depreciation:,.2f}")
print(f"Current Book Value: ${current_book_value:,.2f}")
print(f"")
print(f"Replacement Analysis:")
print(f"Market Value (est.): ${current_book_value * 0.8:,.2f}")
print(f"Recommendation: {'Consider Replacement' if current_book_value < 50000 else 'Monitor Performance'}")