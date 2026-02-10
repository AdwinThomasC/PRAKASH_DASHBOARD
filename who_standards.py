
# WHO Child Growth Standards (0-5 years) and Reference 2007 (5-19 years)
# BMI-for-age LMS Parameters
# L = Power in the Box-Cox transformation
# M = Median
# S = Generalized coefficient of variation

# Data Sources:
# 0-5 years: WHO Child Growth Standards
# 5-19 years: WHO Reference 2007

# NOTE: This file represents a subset of the full WHO tables. 
# For clinical precision, replace these dictionaries with the full monthly data tables.

WHO_BMI_LMS = {
    'girls': {
        # 0-5 Years (Months 0-60) - WHO Standards
        0: {'L': -0.0631, 'M': 13.3363, 'S': 0.09272},
        6: {'L': -0.1429, 'M': 16.9083, 'S': 0.09036},
        12: {'L': -0.3667, 'M': 16.3568, 'S': 0.08797},
        18: {'L': -0.5017, 'M': 15.7263, 'S': 0.08650},
        24: {'L': -0.5684, 'M': 15.6881, 'S': 0.08454},
        36: {'L': -0.5684, 'M': 15.4225, 'S': 0.08779},
        48: {'L': -0.5684, 'M': 15.2602, 'S': 0.09168},
        60: {'L': -0.5684, 'M': 15.2747, 'S': 0.09789},
        
        # 5-19 Years (Months 61-228) - WHO Reference 2007
        # Note: 60 months data is from 0-5 standards, 61+ from 2007 ref.
        # We use linear interpolation between these key points.
        120: {'L': -0.9995, 'M': 17.0016, 'S': 0.12574}, # 10 years
        180: {'L': -0.7303, 'M': 19.3496, 'S': 0.13401}, # 15 years
        228: {'L': -0.5898, 'M': 21.0315, 'S': 0.13993}, # 19 years
    },
    'boys': {
        # 0-5 Years (Months 0-60)
        # PLACEHOLDER: Using approximate values derived from charts/comparisons due to unavailable raw text.
        # User should replace these with exact WHO Boys 0-5 table.
        # 5 years (60mo) is accurate.
        0: {'L': 0.2836, 'M': 13.4, 'S': 0.1}, # Approximate Birth
        60: {'L': -0.6892, 'M': 15.1916, 'S': 0.08700},

        # 5-19 Years (Months 61-228)
        # Using 5y and 19y endpoints plus interpolated intermediate points
        # 19y: +1SD=25.4, +2SD=29.7. Median ~22.
        228: {'L': -0.5, 'M': 22.0, 'S': 0.14}, # Approximate 19y
    }
}

def get_lms(gender, age_in_months):
    """
    Returns interpolated L, M, S values for a given gender and age (in months).
    """
    gender_data = WHO_BMI_LMS.get(gender.lower(), WHO_BMI_LMS['girls']) # Default to girls if unknown
    
    # Sort keys to find range
    ages = sorted(gender_data.keys())
    
    # Handle out of bounds
    if age_in_months <= ages[0]:
        return gender_data[ages[0]]
    if age_in_months >= ages[-1]:
        return gender_data[ages[-1]]
        
    # Find interpolation bounds
    lower_age = ages[0]
    upper_age = ages[-1]
    
    for age in ages:
        if age <= age_in_months:
            lower_age = age
        if age >= age_in_months:
            upper_age = age
            break
            
    if lower_age == upper_age:
        return gender_data[lower_age]
        
    # Linear Interpolation
    fraction = (age_in_months - lower_age) / (upper_age - lower_age)
    
    l_lower = gender_data[lower_age]['L']
    m_lower = gender_data[lower_age]['M']
    s_lower = gender_data[lower_age]['S']
    
    l_upper = gender_data[upper_age]['L']
    m_upper = gender_data[upper_age]['M']
    s_upper = gender_data[upper_age]['S']
    
    l_curr = l_lower + fraction * (l_upper - l_lower)
    m_curr = m_lower + fraction * (m_upper - m_lower)
    s_curr = s_lower + fraction * (s_upper - s_lower)
    
    return {'L': l_curr, 'M': m_curr, 'S': s_curr}

def calculate_bmi_z_score(bmi, gender, age_in_months):
    """
    Calculates the BMI-for-age Z-score using the LMS method.
    Formula: Z = ((BMI / M)^L - 1) / (L * S)  if L != 0
             Z = ln(BMI / M) / S              if L == 0
    """
    if bmi is None or age_in_months is None:
        return None
        
    lms = get_lms(gender, age_in_months)
    L = lms['L']
    M = lms['M']
    S = lms['S']
    
    if L == 0:
        import math
        z = math.log(bmi / M) / S
    else:
        z = ((bmi / M)**L - 1) / (L * S)
        
    return z

def classify_who_z_score(z_score, age_in_months):
    """
    Classifies Z-score based on WHO cutoffs.
    
    0-5 Years:
    > 3 SD: Obese
    > 2 SD: Overweight
    > 1 SD: Risk of overweight (treated as visible overweight often)
    -2 to +2: Normal (broadly)
    < -2 SD: Wasted
    < -3 SD: Severely Wasted
    
    5-19 Years:
    > 2 SD: Obese
    > 1 SD: Overweight
    -2 to +1: Normal
    < -2 SD: Thinness
    < -3 SD: Severe Thinness
    """
    if z_score is None:
        return "Unknown"
        
    if age_in_months < 61: # 0-5 Years
        if z_score > 3:
            return "Obese"
        elif z_score > 2:
            return "Overweight"
        elif z_score < -3:
            return "Severely Wasted"
        elif z_score < -2:
            return "Wasted"
        else:
            return "Normal"
    else: # 5-19 Years
        if z_score > 2:
            return "Obese"
        elif z_score > 1:
            return "Overweight"
        elif z_score < -3:
            return "Severe Thinness"
        elif z_score < -2:
            return "Thinness"
        else:
            return "Normal"
