import dash
from dash import dcc, html, dash_table, no_update, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import json
import re
import urllib.parse
from datetime import datetime
import threading



import flask
import os
from who_standards import calculate_bmi_z_score, classify_who_z_score

# =========================
# GLOBAL CONSTANTS
# =========================
BENEFICIARY_MAP = {
    2: "Pregnant Women",
    3: "Children 5-59 Months",
    4: "Children Aged 5-9 Years",
    5: "Adolescent Girls 10-19 Years",
    6: "Adolescent Boys 10-19 Years",
    7: "Women Of Reproductive Age"
}
anemia_list = ["normal", "mild", "moderate", "severe", "incomplete"]

# =========================
# DASH INIT
# =========================
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
                ], 
                suppress_callback_exceptions=True,
                eager_loading=True)
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True
server = app.server

@server.route('/<filename>')
def serve_assets(filename):
    if filename in ['images.png', 'main_logo.svg', 'government-of-karnataka.webp']:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        return flask.send_from_directory(root_dir, filename)
    return flask.abort(404)

# =========================
# EMBEDDED CSS
# =========================
CSS_STYLES = """
:root {
    --font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
    --primary-color: #4f46e5;
    --primary-hover: #4338ca;
    --teal-glow: #00f2fe;
    --bg-light: #f8fafc;
    --sidebar-bg: #ffffff;
    --card-bg: #ffffff;
    --text-main: #0f172a;
    --text-muted: #64748b;
    --border-color: #e2e8f0;
    --sidebar-width: 280px;
    --top-bar-height: 120px;
    --sidebar-mobile-width: 100%;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

body {
    margin: 0;
    padding: 0;
    font-family: var(--font-family);
    background-color: var(--bg-light);
    color: var(--text-main);
    overflow-x: hidden;
}

.top-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: var(--top-bar-height);
    background-color: #ffffff;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 40px;
    z-index: 1200;
    box-shadow: 0 1px 12px rgba(0, 0, 0, 0.05);
}

.top-bar-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 12px;
}

.glowing-badge {
    background: #0d9488;
    color: white !important;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 6px;
    box-shadow: 0 0 15px rgba(13, 148, 136, 0.5);
    text-shadow: 0 0 5px rgba(255, 255, 255, 0.4);
    margin-left: 8px;
    border: 1px solid #14b8a6;
    letter-spacing: 0.02em;
}

/* Sidebar Styling */
.sidebar {
    position: fixed;
    left: 0;
    top: var(--top-bar-height);
    bottom: 0;
    width: var(--sidebar-width);
    background-color: var(--sidebar-bg);
    border-right: 1px solid var(--border-color);
    z-index: 1100;
    padding: 32px 24px;
    display: flex;
    flex-direction: column;
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.01);
    overflow-y: auto;
    overflow-x: visible !important;
    transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-logo {
    margin-bottom: 40px;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
}

.logo-icon-container {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #4f46e5, #818cf8);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.4rem;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
}

.logo-text {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.logo-text-top {
    font-weight: 800;
    font-size: 1.25rem;
    color: #1e293b;
    line-height: 1;
    letter-spacing: -0.02em;
}

.logo-text-bottom {
    font-weight: 600;
    font-size: 0.7rem;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    line-height: 1.2;
}

.sidebar-label {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.filter-group {
    margin-bottom: 24px;
    overflow: visible !important;
}

/* Main Content Styling */
.main-content {
    margin-left: var(--sidebar-width);
    margin-top: var(--top-bar-height);
    padding: 40px;
    min-height: calc(100vh - var(--top-bar-height));
    transition: margin-left 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.main-content.full-width {
    margin-left: 0;
}

.filter-section-title {
    font-size: 0.75rem;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 20px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--primary-color);
    display: inline-block;
}

.accordion-button:not(.collapsed) {
    background-color: #f1f5f9 !important;
    color: var(--primary-color) !important;
    box-shadow: none !important;
}

.accordion-item {
    border: none !important;
    border-bottom: 1px solid #f1f5f9 !important;
}

.accordion-button {
    padding: 12px 0 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: var(--text-muted) !important;
    box-shadow: none !important;
}

.accordion-body {
    padding: 10px 0 20px 0 !important;
}

.top-header {
    background: #f8fafc; /* Distinct light gray section */
    padding: 32px;
    border-radius: 20px;
    border: 1px solid #e2e8f0;
    margin-bottom: 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.title-container {
    background: #ffffff;
    padding: 16px 28px;
    border-radius: 14px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.08); /* Projected effect */
    display: inline-flex;
    flex-direction: column;
}

.dashboard-title {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.03em;
    display: flex;
    align-items: center;
    color: #0f172a;
}

.title-primary { color: #0f172a; }
.title-separator { width: 1.5px; height: 30px; background-color: #cbd5e1; margin: 0 16px; }
.title-secondary { font-weight: 400; font-size: 1.4rem; color: #64748b; letter-spacing: 0.05em; }

.dashboard-footer {
    padding: 20px 0;
    margin-top: auto;
}

.status-badge {
    padding: 6px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: #dcfce7;
    color: #166534;
    display: flex;
    align-items: center;
    gap: 6px;
}

.status-dot {
    width: 8px;
    height: 8px;
    background: #22c55e;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% {
        opacity: 1;
        transform: scale(1);
    }

    50% {
        opacity: 0.5;
        transform: scale(1.2);
    }

    100% {
        opacity: 1;
        transform: scale(1);
    }
}

/* KPI Scorecards */
.kpi-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    transition: var(--transition);
    height: 100%;
}

.kpi-card:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    border-color: var(--primary-color);
}

.kpi-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}

.kpi-icon {
    font-size: 1.1rem;
    flex-shrink: 0;
}

.kpi-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-bottom: 0;
    font-weight: 500;
    letter-spacing: 0.025em;
    line-height: 1.2;
}

.kpi-value {
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0;
    line-height: 1;
}

/* Dashboard Grid Components */
.graph-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.graph-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
    border-color: var(--primary-color);
}

.graph-title {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 20px;
    color: var(--text-main);
}

/* Mobile Toggle UI */
.mobile-nav {
    display: none;
    align-items: center;
    padding: 15px 20px;
    background: #ffffff;
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 1001;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.toggle-button {
    background: #f8fafc !important;
    border: 1px solid var(--border-color) !important;
    color: var(--primary-color) !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
    cursor: pointer;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

/* Responsive adjustments */
@media (max-width: 992px) {
    .sidebar {
        transform: translateX(-100%);
        width: 280px;
    }

    .sidebar.sidebar-visible {
        transform: translateX(0);
    }

    .top-bar {
        display: none !important;
    }

    .mobile-nav {
        display: flex;
        z-index: 1300; /* Higher than sidebar at 1100 and top-bar at 1200 */
    }

    .main-content {
        margin-left: 0 !important;
        margin-top: 0 !important; /* Mobile nav is sticky, not fixed covering space */
        padding: 20px;
    }

    .top-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}

/* Dropdown styling */
.Select-control {
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    background-color: #f1f5f9 !important;
    height: auto !important;
    min-height: 38px !important;
}

.is-focused .Select-control {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
}

.Select-menu-outer {
    z-index: 2000 !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
    margin-top: 4px !important;
    background-color: #ffffff !important;
}

.nav-buttons {
    display: flex;
    gap: 12px;
}

.nav-btn {
    padding: 8px 20px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    transition: var(--transition);
    text-decoration: none !important;
    border: 1px solid transparent;
}

.nav-btn-test { color: #4f46e5; border-color: #e2e8f0; background: #ffffff; }
.nav-btn-treat { color: #0d9488; border-color: #ccfbf1; background: #f0fdfa; }
.nav-btn-track { color: #ffffff; background: #4f46e5; }

.nav-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.nav-btn-track:hover { background: #4338ca; }

/* Urgent Alerts Styling */
.urgent-list {
    max-height: 200px;
    overflow-y: auto;
    margin-top: 10px;
}

.urgent-item {
    background: #fef2f2;
    border-left: 4px solid #ef4444;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 8px;
    font-size: 0.75rem;
    transition: var(--transition);
}

.urgent-item:hover {
    background: #fee2e2;
    transform: translateX(2px);
}
"""

app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>Prakash Dashboard</title>
        {{%favicon%}}
        {{%css%}}
        <style>
            {CSS_STYLES}
        </style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
'''

# =========================
# LOAD DATA (URL or CSV)
# =========================
DATA_SOURCE_URL = "https://script.google.com/macros/s/AKfycbzazlpEvo3qo2pVhp0fvcpUrlcyR9QRE2SYED5fu-5Og5oVBHZ-EIbaOR-VNCwEIC6JdQ/exec" 
# Paste your deployed Google Apps Script Web App URL here to enable write-back
EXCEL_WRITE_URL = "https://script.google.com/macros/s/AKfycbyfwRVnmXLB8qQt31kIGBmC1NxZ_atYNnM4h-M0sREFpIJJ5au8X9uu8Olwch80XRNpqQ/exec" 
LAST_SYNC_CACHE = {} 
CACHE_FILE = "sync_cache.json"

def load_sync_cache():
    global LAST_SYNC_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                LAST_SYNC_CACHE = json.load(f)
            # print(f"DEBUG: Loaded {len(LAST_SYNC_CACHE)} records from sync cache.")
        except Exception as e:
            print(f"DEBUG: Failed to load sync cache: {e}")
            LAST_SYNC_CACHE = {}
    else:
        LAST_SYNC_CACHE = {}

def save_sync_cache():
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(LAST_SYNC_CACHE, f)
    except Exception as e:
        print(f"DEBUG: Failed to save sync cache: {e}")

# Initial load
load_sync_cache()

# BENEFICIARY_MAP moved to GLOBAL CONSTANTS at top of file

def parse_age(age_val):
    if pd.isna(age_val) or age_val == "":
        return None
    
    # Handle already numeric values
    if isinstance(age_val, (int, float)):
        return age_val if age_val < 150 else None
        
    if hasattr(age_val, 'year') and hasattr(age_val, 'month'):
        # If it's a date, we probably can't infer age without a reference date, 
        # but let's assume it's not an age.
        return None

    age_str = str(age_val).lower().strip()
    
    # 1. If it's just a simple number string (e.g. "21" or "21.5")
    clean_num = age_str.replace('yr', '').replace('yrs', '').replace('yr.', '').strip()
    try:
        val = float(clean_num)
        return val if val < 150 else None
    except:
        pass

    # 2. Rule out strings that look like full dates (e.g., "2021-06-01" or "21/06/19")
    if re.search(r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}', age_str):
        return None

    years = 0.0
    months = 0.0
    
    # 3. Explicit search for suffixes (Highest priority)
    y_match = re.search(r'(\d+(\.\d+)?)\s*(y|yr|year)', age_str)
    m_match = re.search(r'(\d+(\.\d+)?)\s*(m|mo|month)', age_str)
    
    if y_match or m_match:
        if y_match: years = float(y_match.group(1))
        if m_match: months = float(m_match.group(1))
        # If years looks like a birth year, disregard it
        if years > 1900: years = 0
    else:
        # 4. Fallback: No suffixes, look for "Number Number"
        nums = re.findall(r'(\d+(\.\d+)?)', age_str)
        if len(nums) >= 1:
            val1 = float(nums[0][0])
            if val1 > 1900: # First number is a year
                if len(nums) >= 2: years = float(nums[1][0])
                if len(nums) >= 3: months = float(nums[2][0])
            else:
                years = val1
                if len(nums) >= 2: months = float(nums[1][0])
    
    res = round(years + (months / 12), 2)
    return res if 0 < res < 150 else None

def classify_anemia_who(hgb, age, gender, beneficiary):
    """
    Classify anemia based on WHO guidelines.
    
    Parameters:
    - hgb: Hemoglobin level in g/dL (REQUIRED)
    - age: Age in years (Optional if beneficiary type is specific)
    - gender: Gender (Male/Female)
    - beneficiary: Beneficiary category
    
    Returns: 'normal', 'mild', 'moderate', 'severe', or 'incomplete' if data is insufficient
    """
    # Handle missing HGB - REQUIRED
    if pd.isna(hgb) or hgb is None:
        return "incomplete"
    
    # Convert HGB to float
    try:
        hgb = float(hgb)
    except:
        return "incomplete"

    # Handle Age (Optional, but convert if present)
    try:
        if age is not None and not pd.isna(age) and str(age).strip() != "":
            age = float(age)
        else:
            age = None
    except:
        age = None
    
    # Normalize inputs
    gender_str = str(gender).lower().strip() if not pd.isna(gender) else ""
    beneficiary_str = str(beneficiary).lower().strip() if not pd.isna(beneficiary) else ""
    
    # Determine classification based on beneficiary type OR age
    
    # Pregnant Women
    if "pregnant" in beneficiary_str:
        if hgb >= 11.0:
            return "normal"
        elif hgb >= 10.0:
            return "mild"
        elif hgb >= 7.0:
            return "moderate"
        else:
            return "severe"
    
    # Children 5-59 Months (6-59 months WHO category)
    elif "5-59 months" in beneficiary_str or "children 5-59 months" in beneficiary_str:
        if hgb >= 11.0:
            return "normal"
        elif hgb >= 10.0:
            return "mild"
        elif hgb >= 7.0:
            return "moderate"
        else:
            return "severe"
    
    # Children Aged 5-9 Years
    elif "5-9 years" in beneficiary_str:
        if hgb >= 11.5:
            return "normal"
        elif hgb >= 11.0:
            return "mild"
        elif hgb >= 8.0:
            return "moderate"
        else:
            return "severe"
    
    # Adolescent Girls 10-19 Years
    elif "adolescent girls" in beneficiary_str or ("adolescent" in beneficiary_str and "female" in gender_str):
        if hgb >= 12.0:
            return "normal"
        elif hgb >= 11.0:
            return "mild"
        elif hgb >= 8.0:
            return "moderate"
        else:
            return "severe"
    
    # Adolescent Boys 10-19 Years
    elif "adolescent boys" in beneficiary_str or ("adolescent" in beneficiary_str and "male" in gender_str):
        if hgb >= 12.0:
            return "normal"
        elif hgb >= 11.0:
            return "mild"
        elif hgb >= 8.0:
            return "moderate"
        else:
            return "severe"
    
    # Women Of Reproductive Age (non-pregnant)
    elif "women of reproductive age" in beneficiary_str or "reproductive age" in beneficiary_str:
        if hgb >= 12.0:
            return "normal"
        elif hgb >= 11.0:
            return "mild"
        elif hgb >= 8.0:
            return "moderate"
        else:
            return "severe"
    
    # Fallback: Use age and gender if beneficiary type doesn't match
    elif age is not None:
        # Children under 5 years
        if age < 5:
            if hgb >= 11.0:
                return "normal"
            elif hgb >= 10.0:
                return "mild"
            elif hgb >= 7.0:
                return "moderate"
            else:
                return "severe"
        
        # Children 5-11 years
        elif age < 12:
            if hgb >= 11.5:
                return "normal"
            elif hgb >= 11.0:
                return "mild"
            elif hgb >= 8.0:
                return "moderate"
            else:
                return "severe"
        
        # Adolescents and Adults (12+ years)
        else:
            # Female thresholds
            if "female" in gender_str or "f" == gender_str:
                if hgb >= 12.0:
                    return "normal"
                elif hgb >= 11.0:
                    return "mild"
                elif hgb >= 8.0:
                    return "moderate"
                else:
                    return "severe"
            # Male thresholds
            elif "male" in gender_str or "m" == gender_str:
                if hgb >= 13.0:
                    return "normal"
                elif hgb >= 11.0:
                    return "mild"
                elif hgb >= 8.0:
                    return "moderate"
                else:
                    return "severe"
            # Missing gender - use female thresholds (more conservative)
            else:
                if hgb >= 12.0:
                    return "normal"
                elif hgb >= 11.0:
                    return "mild"
                elif hgb >= 8.0:
                    return "moderate"
                else:
                    return "severe"
    # If we can't determine (missing/unclear beneficiary AND missing age), return incomplete
    return "incomplete"

def sync_data_to_sheets(df):
    """
    Sends computed data (Anemia Status, Corrected Age) back to Google Sheets.
    Only syncs rows that are new or have changed since the last session.
    """
    global LAST_SYNC_CACHE
    if not EXCEL_WRITE_URL or "PASTE_SCRIPT_URL_HERE" in EXCEL_WRITE_URL:
        return
    
    if df.empty:
        return

    sync_cols = [
        "SL.NO", "ID", "enrollment_date", "Area COde", "PSU Name", 
        "Name", "Gender", "Benificiery", "HGB", "anemia_category",
        "Length", "Height", "Weight", "Age", "whatsapp",
        "Diet 1", "Diet 2", "field_investigator", "Asha_Worker", "data_operator",
        "Sample Collected Date", "bmi_category", "BMI", "Email", "Status"
    ]
    
    # Identify which columns actually exist in the current dataframe
    cols_to_use = [c for c in sync_cols if c in df.columns]
    
    # --- Row-Level Diffing ---
    diff_rows = []
    temp_cache = LAST_SYNC_CACHE.copy()
    
    for _, row in df.iterrows():
        p_id = str(row.get("ID", "")).strip()
        if not p_id or p_id.lower() == "nan": continue
        
        # Create a unique signature for this row based on its values
        row_values = [str(row.get(c, "")).strip() for c in cols_to_use]
        row_sig = "|".join(row_values)
        
        # If ID is new OR the data has changed, mark for sync
        if p_id not in LAST_SYNC_CACHE or LAST_SYNC_CACHE[p_id] != row_sig:
            diff_rows.append(row)
            temp_cache[p_id] = row_sig
            
    if not diff_rows:
        # print("DEBUG: No changes detected at row level. Skipping background sync.")
        return
    
    # Update cache locally (we'll commit to file if the request succeeds)
    # Actually, it's safer to update internal cache only after success, but we prepared temp_cache
    # temp_cache already has the updates.

    
    print(f"DEBUG: Found {len(diff_rows)} new/updated records to sync to Sheets.")

    try:
        import requests
        # Prepare data for sync
        sync_df = pd.DataFrame(diff_rows)
        
        # Convert types for JSON compatibility
        for col in sync_df.columns:
            if pd.api.types.is_datetime64_any_dtype(sync_df[col]):
                sync_df[col] = sync_df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Critical: Replace NaN with None so they become null in JSON
        payload = sync_df.replace({pd.NA: None, float('nan'): None}).to_dict("records")
        
        # Syncing...
        r = requests.post(EXCEL_WRITE_URL, json=payload, timeout=120, allow_redirects=True)
        if r.status_code != 200:
            print(f"DEBUG: Data sync failed with status {r.status_code}: {r.text[:200]}")
        else:
            print(f"DEBUG: Data sync successful: {r.json().get('message') if r.text.startswith('{') else 'OK'}")
            # Update cache only after successful delivery
            LAST_SYNC_CACHE = temp_cache
            save_sync_cache()
    except Exception as e:
        import traceback
        print(f"DEBUG: Data sync exception trace: {traceback.format_exc()}")

def load_data():
    """
    Fetches data from Google Apps Script. 
    Returns: (df, status_message, is_error)
    """
    status_msg = "Live"
    is_error = False
    try:
        import requests
        # Increased timeout to 20s to prevent 'Server did not respond' errors on slower links
        r = requests.get(DATA_SOURCE_URL, timeout=20)
        r.raise_for_status()
        
        try:
            data_json = r.json()
            # Debug: Print a snippet of the JSON to the console
            print("DEBUG: Fetched JSON Data (snippet):", str(data_json)[:500] + "...")
            
            if isinstance(data_json, dict) and 'data' in data_json:
                df = pd.DataFrame(data_json['data'])
            else:
                df = pd.DataFrame(data_json)
        except:
            from io import StringIO
            df = pd.read_csv(StringIO(r.text))
            
        if df.empty:
            return pd.DataFrame(), "No Data in Script", True

        df.columns = df.columns.str.strip()
        
        required_cols = [
            "SL.NO", "ID", "enrollment_date", "Area COde", "PSU Name",
            "Name", "Household Name", "Gender", "Benificiery", "DOB", "Age",
            "sample_status", "Sample Collected Date", "Collected By",
            "HGB", "anemia_category", "field_investigator", "Diet", "Diet1", "Diet2", "data_operator",
            "Asha_Worker", "Aasha_Contact", "Length", "Height", "Weight", "Email", "Status"
        ]
        df = df[[c for c in required_cols if c in df.columns]]

        date_cols = ["DATE_F", "enrollment_date", "DOB", "Sample Collected Date"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        if "HGB" in df.columns:
            df["HGB"] = pd.to_numeric(df["HGB"], errors="coerce")

        # Numeric conversion for anthropometric data
        for col in ["Length", "Height", "Weight"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                
        # Rename Diet columns for clarity: Diet -> Diet 1, Diet1 -> Diet 2
        diet_rename = {}
        if "Diet" in df.columns: diet_rename["Diet"] = "Diet 1"
        if "Diet1" in df.columns: diet_rename["Diet1"] = "Diet 2"
        if "Diet2" in df.columns: diet_rename["Diet2"] = "Diet 3"
        if diet_rename:
            df = df.rename(columns=diet_rename)

        # Calculate BMI: Weight(kg) / [Height(m)]²
        # Row-level fallback: Use Height if available, otherwise use Length
        if "Weight" in df.columns:
            h_vals = df["Height"] if "Height" in df.columns else (df["Length"] if "Length" in df.columns else pd.Series([None] * len(df)))
            if "Height" in df.columns and "Length" in df.columns:
                h_vals = df["Height"].fillna(df["Length"])
            
            # height in meters, ensure not zero
            valid_mask = (df["Weight"] > 0) & (h_vals > 0)
            df["BMI"] = None
            df.loc[valid_mask, "BMI"] = (df.loc[valid_mask, "Weight"] / ((h_vals.loc[valid_mask] / 100.0) ** 2)).round(1)
        else:
            df["BMI"] = None

        def classify_nutritional_status(row):
            bmi = row.get("BMI")
            age_y = row.get("Age")
            beneficiary = str(row.get("Benificiery", "")).lower()
            gender_raw = str(row.get("Gender", "")).lower().strip()
            
            # Exemption: If pregnant and BMI >= 30, classify as Obese (pre-pregnancy proxy)
            if "pregnant" in beneficiary or "(pw)" in beneficiary:
                if not pd.isna(bmi) and bmi >= 30.0:
                    return "Obese"
                return "Pregnancy"
                
            if pd.isna(bmi) or bmi is None: return "Missing"
            
            try:
                val = float(bmi)
            except:
                return "Missing"

            # Map Gender to WHO 'boys'/'girls'
            gender_who = None
            if gender_raw in ["male", "m", "boy", "boys"]:
                gender_who = "boys"
            elif gender_raw in ["female", "f", "girl", "girls"]:
                gender_who = "girls"

            # Use WHO Z-scores for children < 19 if gender is known
            if age_y is not None and not pd.isna(age_y) and gender_who:
                try:
                    age_val = float(age_y)
                    if age_val < 19:
                        age_m = age_val * 12.0
                        # Try/Except inside loop to prevent single row failure from crashing everything
                        try:
                            z = calculate_bmi_z_score(val, gender_who, age_m)
                            if z is not None:
                                return classify_who_z_score(z, age_m)
                        except Exception as z_err:
                            print(f"DEBUG: Z-score calculation failed for row: {z_err}")
                except Exception as e:
                    # Fallback to adult logic on error
                    pass

            # Adult Fallback (>= 19 or unknown gender/age)
            if val < 18.5: return "Underweight"
            if val < 25.0: return "Normal"
            if val < 30.0: return "Overweight"
            return "Obese"
        
        # We need Age to be parsed BEFORE classification
        # Parse Age with special logic FIRST
        if "Age" in df.columns:
            df["Age"] = df["Age"].apply(parse_age)
        else:
            df["Age"] = None
            
        # Cross-calculate Age from DOB if missing
        if "DOB" in df.columns:
            # Use enrollment_date as reference, fallback to today
            ref_date = df["enrollment_date"].fillna(pd.Timestamp.now())
            
            # Mask for missing Ages where DOB exists
            mask = df["Age"].isna() & df["DOB"].notna()
            
            if mask.any():
                # Ensure compatibility by removing timezones (tz-naive)
                try:
                    # Fix: Ensure ref_date is also timezone-naive to match localized(None) DOB
                    ref_dt_naive = pd.to_datetime(ref_date[mask]).dt.tz_localize(None)
                    dob_dt_naive = pd.to_datetime(df.loc[mask, "DOB"]).dt.tz_localize(None)
                    diff = (ref_dt_naive - dob_dt_naive).dt.days
                    calculated_ages = (diff / 365.25).round(2)
                    # Only apply if result is sane
                    df.loc[mask, "Age"] = calculated_ages.apply(lambda x: x if 0 <= x < 150 else None)
                except Exception as age_err:
                    print(f"DEBUG: Age calculation fallback failed: {age_err}")

        # Now apply classification using the populated Age
        df["bmi_category"] = df.apply(classify_nutritional_status, axis=1)
        
        if "Area COde" in df.columns:
            df["Area COde"] = df["Area COde"].astype(str).str.zfill(3)

        if "PSU Name" in df.columns and "Area COde" in df.columns:
            df["Location"] = df["PSU Name"].astype(str) + " (" + df["Area COde"].astype(str) + ")"
        elif "PSU Name" in df.columns:
            df["Location"] = df["PSU Name"].astype(str)
        else:
            df["Location"] = "Missing"

        if "anemia_category" in df.columns:
            df["anemia_category"] = df["anemia_category"].astype(str).str.strip()
            cat_map = {"Normal": "normal", "Mild anemia": "mild", "Moderate anemia": "moderate", "Severe anemia": "severe"}
            df["anemia_category"] = df["anemia_category"].map(cat_map).fillna(df["anemia_category"].str.lower())

        if "Benificiery" in df.columns:
            df["Benificiery"] = pd.to_numeric(df["Benificiery"], errors='coerce')
            df["Benificiery"] = df["Benificiery"].map(BENEFICIARY_MAP).fillna(df["Benificiery"])
            df["Benificiery"] = df["Benificiery"].astype(str).str.title()

        if "Name" in df.columns:
            df["Name"] = df["Name"].astype(str).str.title()
            
        if "Asha_Worker" in df.columns:
            df["Asha_Worker"] = df["Asha_Worker"].astype(str).str.title()
            
        if "Aasha_Contact" in df.columns:
            # Clean phone numbers (remove non-digits)
            df["Aasha_Contact"] = df["Aasha_Contact"].astype(str).str.replace(r'\D', '', regex=True)
            # Add country code if missing (assumed India +91)
            def fix_phone(p):
                if not p or p == "" or p == "nan": return ""
                if len(p) == 10: return "91" + p
                return p
            df["Aasha_Contact"] = df["Aasha_Contact"].apply(fix_phone)

        # Apply WHO-based automatic anemia classification
        if "HGB" in df.columns:
            df["anemia_category"] = df.apply(
                lambda row: classify_anemia_who(
                    row.get("HGB"),
                    row.get("Age"),
                    row.get("Gender"),
                    row.get("Benificiery")
                ),
                axis=1
            )
        else:
            df["anemia_category"] = None

        # FILTER: Keep rows where either Age OR Beneficiary is present
        # Check for valid Age (not None/NaN)
        has_age = df["Age"].notna()
        
        # Check for valid Beneficiary (not None/NaN/empty/"Nan")
        # Since we converted to string title case earlier, check against "Nan" and "None" strings
        has_beneficiary = (
            df["Benificiery"].notna() & 
            (df["Benificiery"] != "") & 
            (df["Benificiery"].str.lower() != "nan") & 
            (df["Benificiery"].str.lower() != "none")
        )
        
        df = df[has_age | has_beneficiary]

        return df, "Live", False
        
    except requests.exceptions.ConnectionError:
        return pd.DataFrame(), "Connection Error (Check DNS/Network)", True
    except requests.exceptions.Timeout:
        return pd.DataFrame(), "Request Timeout", True
    except Exception as e:
        return pd.DataFrame(), f"Script Error: {str(e)}", True

psu_list = []
area_list = []
anemia_list = ["normal", "mild", "moderate", "severe", "incomplete"]

def area_coordinates():
    return {
        'Kunikera': {'lat': 15.2832, 'lon': 76.2142},
        'Ojanahalli': {'lat': 15.3856, 'lon': 76.1472},
        'Bannikoppa': {'lat': 15.3877, 'lon': 75.9420},
        'Tadkal': {'lat': 15.3688, 'lon': 75.9812},
        'Hulegudda': {'lat': 15.6235, 'lon': 76.1146},
        'Konasagara': {'lat': 15.6916, 'lon': 76.1030},
        'Kawalbodur': {'lat': 15.8318, 'lon': 76.1871},
        'Balutagi': {'lat': 15.87338865573784, 'lon': 76.25665534853232},
        'HireGonnagar': {'lat': 15.8092, 'lon': 75.9539},
        'Anegundi': {'lat': 15.3507, 'lon': 76.4925},
        'Kilarhatti': {'lat': 15.8411, 'lon': 76.4359},
        'Challur': {'lat': 15.6014, 'lon': 76.5943},
        'Marlanahalli': {'lat': 15.5771, 'lon': 76.6490},
        'Gouripur': {'lat': 15.6187547, 'lon': 76.35504569999999},
        'Hatti': {'lat': 15.2117, 'lon': 75.9350},
        'Komalapur': {'lat': 15.3405, 'lon':76.0215},
        'Chikwankal Kunta': {'lat': 15.629761351168723, 'lon':76.23304865792784},
        'Hire Wankal Kunta': {'lat': 15.646960083050104, 'lon':76.238318366376871},
        'Talkere': {'lat': 15.645466597713694, 'lon': 76.26477078258641},
        'Ningalbandi': {'lat': 15.671063605028287, 'lon': 76.13794513593994},
        'Badimnhal': {'lat': 15.839823262484467, 'lon': 75.95503149946924},
        'Venkatapur': {'lat': 15.858511392991407, 'lon': 75.97308023163832},
        'Garjanhal': {'lat': 15.833697603912572, 'lon': 76.41468762354576},
        'Teggihal': {'lat': 15.849556310249351, 'lon': 76.27912911541603},
        'Mallapur': {'lat': 15.3933, 'lon': 76.4867},
        'Rampura': {'lat': 15.3822, 'lon': 76.4816},
        'Hagedal': {'lat': 15.590418925207551,  'lon':76.59839346965396},
        'Basrihal': {'lat': 15.595505073968516, 'lon':76.38104641401482},
        'Chikka Madinal': {'lat': 15.523496092485985, 'lon': 76.3778821765826},
        'Wadganhal': {'lat': 15.349168758650613, 'lon': 76.0804548913306},
        'Hirebommanahal': {'lat': 15.597423828789088 , 'lon': 76.2735258247831},
        'Hiresulikeri': {'lat': 15.52797030965004,'lon':  76.26075289964011 },
        'Jinnapur': {'lat': 15.490613192523476,'lon':  76.25717388261322},
        'Belgatti': {'lat': 15.213735760897155, 'lon': 75.9243389399449 },
        'Kawaloor': {'lat': 15.296976608396339, 'lon': 75.93461733961688},
        'Kesoor': {'lat': 15.872788521335098, 'lon': 76.19874347785046 },
        'Gangawati (CMC+OG) WARD No- 0005': {'lat': 15.424340577107621, 'lon': 76.53100417165172},
        'Gangawati (CMC+OG) WARD No- 0009': {'lat': 15.4280, 'lon': 76.5250},
        'Gangawati (CMC+OG) WARD No- 0015': {'lat': 15.4330, 'lon': 76.5350},
        'Koppal (CMC) WARD No-0008': {'lat': 15.3530, 'lon': 76.1580},
        'Koppal (CMC) WARD No-0021': {'lat': 15.3480, 'lon': 76.1520},
        'Koppal (CMC) WARD No-0001': {'lat': 15.3550, 'lon': 76.1500}
    }

def create_map(df):
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="No data available", showarrow=False)
        return fig
    coords = area_coordinates()
    df = df.copy()
    if "PSU Name" in df.columns:
        df["lat"] = df["PSU Name"].astype(str).str.strip().map(lambda x: coords.get(x, {}).get("lat"))
        df["lon"] = df["PSU Name"].astype(str).str.strip().map(lambda x: coords.get(x, {}).get("lon"))
    else:
        df["lat"] = None
        df["lon"] = None
    map_df = df.dropna(subset=["lat", "lon"])
    
    # Calculate counts per PSU and Beneficiary
    psu_counts = map_df.groupby("PSU Name").size().to_dict() if not map_df.empty else {}
    benif_breakdown = map_df.groupby(["PSU Name", "Benificiery"]).size().unstack(fill_value=0).to_dict('index') if not map_df.empty else {}
    
    # All defined villages with their count (default 0)
    village_status = []
    for v_name, v_coord in coords.items():
        count = psu_counts.get(v_name, 0)
        breakdown_dict = benif_breakdown.get(v_name, {})
        # Create a formatted string for the tooltip
        breakdown_str = "<br>".join([f"• {k}: {v}" for k, v in breakdown_dict.items() if v > 0])
        if not breakdown_str:
            breakdown_str = "No data"
            
        status = "No Data" if count == 0 else ("In Progress" if count < 48 else "Complete")
        color = "#922b21" if count == 0 else ("#e67e22" if count < 48 else "#27ae60")
        village_status.append({
            "name": v_name, "lat": v_coord["lat"], "lon": v_coord["lon"],
            "count": count, "status": status, "color": color, "breakdown": breakdown_str
        })
    status_df = pd.DataFrame(village_status)

    # Always try to draw the boundary
    try:
        with open("koppal_district_official.geojson", "r") as f:
            geojson_data = json.load(f)
        fig.add_trace(go.Choroplethmap(
            geojson=geojson_data, locations=["Koppal"], featureidkey="properties.district",
            z=[1], colorscale=[[0, "rgba(52, 152, 219, 0.1)"], [1, "rgba(52, 152, 219, 0.1)"]],
            marker_line_width=2, marker_line_color="#2980b9", marker_opacity=0.5,
            showscale=False, name="Study Area Boundary", hoverinfo="name"
        ))
    except Exception as e:
        print(f"DEBUG: Could not load GeoJSON boundary: {e}")

    # Heatmap commented out as requested
    """
    # Add Heatmap for Anemia Cases (Combined Moderate + Severe)
    heat_df = map_df[map_df["anemia_category"].str.lower().isin(["moderate", "severe"])].copy()
    if not heat_df.empty:
        # Weight Severe cases higher (2) than Moderate (1)
        heat_df["weight"] = heat_df["anemia_category"].str.lower().map({"severe": 2, "moderate": 1})
        # Group by location for cleaner intensity
        heat_grouped = heat_df.groupby(["lat", "lon"])["weight"].sum().reset_index()
        
        fig.add_trace(go.Densitymap(
            lat=heat_grouped["lat"], lon=heat_grouped["lon"],
            z=heat_grouped["weight"], 
            radius=40,
            colorscale='Reds', # Using a standard, highly visible colorscale
            showscale=False,
            name="Anemia Hotspots",
            hoverinfo='skip',
            opacity=0.7
        ))
    """

    # Add Progress-based Markers (Three Groups)
    categories = [
        {"name": "No Data Collected", "color": "#922b21", "filter": status_df["count"] == 0},
        {"name": "In Progress (1-47)", "color": "#e67e22", "filter": (status_df["count"] > 0) & (status_df["count"] < 48)},
        {"name": "Complete (48+ Samples)", "color": "#27ae60", "filter": status_df["count"] >= 48}
    ]
    
    for cat in categories:
        d_cat = status_df[cat["filter"]]
        if not d_cat.empty:
            fig.add_trace(go.Scattermap(
                lat=d_cat["lat"], lon=d_cat["lon"], mode="markers+text",
                marker=dict(size=14, color=cat["color"], opacity=0.9),
                name=cat["name"],
                text=d_cat["name"],
                textfont=dict(size=10, color="#2c3e50", family="-apple-system, BlinkMacSystemFont, sans-serif"),
                textposition="top center",
                hovertemplate='<b>%{text}</b><br>Total Samples: %{customdata[0]}<br>Status: %{customdata[1]}<br><br><b>Beneficiary Breakdown:</b><br>%{customdata[2]}<extra></extra>',
                customdata=d_cat[["count", "status", "breakdown"]].values
            ))
    
    fig.update_layout(
        map_style="open-street-map", map_center={"lat": 15.6, "lon": 76.15},
        map_zoom=8.3, margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255, 255, 255, 0.7)"),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="-apple-system, BlinkMacSystemFont, sans-serif"),
        uirevision=True # Preserve zoom and pan state
    )
    return fig

def create_treat_map(df):
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="No data available", showarrow=False)
        return fig
        
    coords = area_coordinates()
    df = df.copy()
    if "PSU Name" in df.columns:
        df["lat"] = df["PSU Name"].astype(str).str.strip().map(lambda x: coords.get(x, {}).get("lat"))
        df["lon"] = df["PSU Name"].astype(str).str.strip().map(lambda x: coords.get(x, {}).get("lon"))
    
    map_df = df.dropna(subset=["lat", "lon"])
    
    # Calculate counts per PSU for treatment focus
    # We need: Asha Worker names, and Anemic counts (Mild, Moderate, Severe)
    treat_data = []
    
    # PSU-wise aggregates
    for psu_name, psu_group in map_df.groupby("PSU Name"):
        ashas = ", ".join(psu_group["Asha_Worker"].dropna().unique()) if "Asha_Worker" in psu_group.columns else "Missing"
        
        # Anemia breakdown
        counts = psu_group["anemia_category"].str.lower().value_counts()
        mild = counts.get("mild", 0)
        moderate = counts.get("moderate", 0)
        severe = counts.get("severe", 0)
        total_anemic = mild + moderate + severe
        
        if total_anemic > 0:
            color = "#ef4444" if severe > 0 else ("#f97316" if moderate > 0 else "#f59e0b")
            status = f"<b>{total_anemic}</b> Anemic"
        else:
            color = "#10b981"
            status = "No Anemia"
            
        hover_text = (
            f"<b>{psu_name}</b><br><br>"
            f"Asha Worker: <b>{ashas}</b><br><br>"
            f"<b>Anemia Breakdown:</b><br>"
            f"• Severe: <b>{severe}</b><br>"
            f"• Moderate: <b>{moderate}</b><br>"
            f"• Mild: <b>{mild}</b><br>"
            f"• Normal: <b>{counts.get('normal', 0)}</b>"
        )
        
        v_coord = coords.get(psu_name, {})
        if v_coord:
            treat_data.append({
                "name": psu_name, "lat": v_coord["lat"], "lon": v_coord["lon"],
                "color": color, "hover": hover_text, "size": 12 + (total_anemic * 0.5)
            })

    if treat_data:
        t_df = pd.DataFrame(treat_data)
        fig.add_trace(go.Scattermap(
            lat=t_df["lat"], lon=t_df["lon"], mode="markers",
            marker=dict(size=t_df["size"], color=t_df["color"], opacity=0.8),
            name="Urgent PSUs",
            text=t_df["name"],
            hovertemplate="%{customdata}<extra></extra>",
            customdata=t_df["hover"]
        ))

    # Add Geospatial boundary
    try:
        with open("koppal_district_official.geojson", "r") as f:
            geojson_data = json.load(f)
        fig.add_trace(go.Choroplethmap(
            geojson=geojson_data, locations=["Koppal"], featureidkey="properties.district",
            z=[1], colorscale=[[0, "rgba(52, 152, 219, 0.05)"], [1, "rgba(52, 152, 219, 0.05)"]],
            marker_line_width=1, marker_line_color="#2980b9", marker_opacity=0.3,
            showscale=False, name="Boundary", hoverinfo="skip"
        ))
    except: pass

    fig.update_layout(
        map_style="open-street-map", map_center={"lat": 15.6, "lon": 76.15},
        map_zoom=8.3, margin=dict(l=0, r=0, t=0, b=0),
        uirevision=True
    )
    return fig

def get_treat_layout():
    return html.Div([
        # Sidebar with Filters (Same as Dashboard for consistency)
        html.Div([
            html.Div([
                html.P("Treatment & Follow-up Dashboard", 
                       style={"fontSize": "0.75rem", "fontWeight": "700", "color": "#000000", "margin": "0", "letterSpacing": "0.05em", "textTransform": "uppercase"}),
                html.P("Koppal, Karnataka", 
                       style={"fontSize": "0.7rem", "color": "#000000", "margin": "2px 0 0 0"})
            ], style={"padding": "0 0 20px 0", "marginBottom": "10px", "borderBottom": "1px solid #f1f5f9"}),
            
            html.Div([
                html.Div([
                    html.Label("Locality", className="sidebar-label"),
                    dcc.Dropdown(id="location-dropdown", options=[], multi=True, value=[], placeholder="All Locations"),
                ], className="filter-group"),
                
                html.Div([
                    html.Label("Beneficiary Type", className="sidebar-label"),
                    dcc.Dropdown(id="benificiery-dropdown", options=[], multi=True, value=[], placeholder="All Beneficiaries"),
                ], className="filter-group"),

                html.Div([
                    html.Label("Anemia Filter", className="sidebar-label"),
                    dcc.Dropdown(id="anemia-dropdown", options=[{"label": x.capitalize(), "value": x} for x in anemia_list], multi=True, value=[], placeholder="All Categories"),
                ], className="filter-group"),

                dbc.Button("Clear All Filters", id="btn-clear", color="secondary", outline=True, size="sm", className="w-100 mb-4"),

                html.Div([
                    html.Label("Urgent Follow-up Subjects", className="sidebar-label", style={"color": "#ef4444"}),
                    html.Div(id="urgent-alerts-list", className="urgent-list"),
                ], className="filter-group", id="urgent-section"),
            ], style={"flex": "1"}),
        ], id="sidebar", className="sidebar"),

        # Main Content
        html.Div([
            # Phase Marker
            html.Div([
                html.Span([html.I(className="fas fa-tag me-2"), "Baseline 1"], className="glowing-badge", style={"fontSize": "0.75rem", "padding": "4px 12px"})
            ], style={"textAlign": "left", "marginBottom": "10px"}),

            # KPI Row for Treat Page (Moved to Top)
            dbc.Row([
                # KPI Section (Styled to match Test page)
                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-users kpi-icon"), html.P("Total Enrollment", className="kpi-label")], className="kpi-header"),
                    html.H3(id="total", className="kpi-value")
                ], className="kpi-card"), xs=12, sm=6, md=4, lg=True),

                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-exclamation-triangle kpi-icon", style={"color": "#ef4444"}), html.P("Severe Anemia", className="kpi-label")], className="kpi-header"),
                    html.H3(id="severe-count", className="kpi-value")
                ], className="kpi-card"), xs=6, sm=4, md=True),
                
                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-exclamation-circle kpi-icon", style={"color": "#f97316"}), html.P("Moderate Anemia", className="kpi-label")], className="kpi-header"),
                    html.H3(id="moderate-count", className="kpi-value")
                ], className="kpi-card"), xs=6, sm=4, md=True),
                
                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-droplet kpi-icon", style={"color": "#991b1b"}), html.P("Avg Hb (g/dL)", className="kpi-label")], className="kpi-header"),
                    html.H3(id="avg-hgb", className="kpi-value")
                ], className="kpi-card"), xs=6, sm=4, md=True),
            ], className="mb-4 g-3"),

            html.Div([
                html.H4("Geospatial High-Risk Distribution", style={"marginBottom": "20px", "fontWeight": "700"}),
                html.P("Hover over markers to see assigned Asha Workers and patient breakdown.", style={"color": "#64748b", "fontSize": "0.9rem"}),
                dcc.Graph(id="map", config={"responsive": True}, style=MAP_CARD_STYLE),
            ], className="graph-card", style={"padding": "30px", "marginBottom": "24px"}),
            
            # Secondary charts (Hidden to simplify page as requested)
            html.Div([
                dcc.Graph(id="anemia-pie", style={"display": "none"}),
                dcc.Graph(id="benificiery-bar", style={"display": "none"}),
                html.Div(id="prevalence-val", style={"display": "none"}),
                html.Div(id="normal-count", style={"display": "none"}),
                html.Div(id="mild-count", style={"display": "none"}),
                html.Div(id="diet-count", style={"display": "none"}),
            ], style={"display": "none"}),

            # Other required charts
            dbc.Row([
                dbc.Col(dcc.Graph(id="bmi-bar", style={"display": "none"}), width=4),
                dbc.Col(dcc.Graph(id="hgb-stats-bar", style={"display": "none"}), width=4),
                dbc.Col(dcc.Graph(id="anemia-village-bar", style={"display": "none"}), width=4),
            ]),

            html.Div([
                html.H5("Detailed Records", className="graph-title"),
                dash_table.DataTable(id="table", style_header={"display": "none"})
            ], style={"display": "none"}),
            
            get_footer()
        ], id="main-content", className="main-content")
    ])

def get_footer():
    return html.Footer([
        html.Hr(style={"margin": "40px 0 20px 0", "opacity": "0.1"}),
        html.Div([
            html.P("Copyright © 2026 ICMR CAR MEDTECH LAB | St Johns's Research Institute, Bangalore",
                   style={"fontSize": "0.75rem", "color": "#64748b", "textAlign": "center", "marginBottom": "20px"})
        ], className="footer-content")
    ], className="dashboard-footer")

# Custom styles for the layout
CARD_STYLE = {"height": "350px"}
MAP_CARD_STYLE = {"height": "645px"}

def get_dashboard_layout():
    return html.Div([
        html.Div([
            # Sidebar Header (Context Label)
            html.Div([
                html.P("Real-time Anaemia Monitoring Dashboard", 
                       style={"fontSize": "0.75rem", "fontWeight": "700", "color": "#000000", "margin": "0", "letterSpacing": "0.05em", "textTransform": "uppercase"}),
                html.P("Koppal, Karnataka", 
                       style={"fontSize": "0.7rem", "color": "#000000", "margin": "2px 0 0 0"})
            ], style={"padding": "0 0 20px 0", "marginBottom": "10px", "borderBottom": "1px solid #f1f5f9"}),
            
            html.Div([
                # Location Selection (Always Visible)
                html.Div([
                    html.Label("Location Selection", className="sidebar-label"),
                    dcc.Dropdown(id="location-dropdown", options=[], multi=True, value=[], placeholder="All Locations"),
                ], className="filter-group"),
                
                # Filter Groups (Reverted to flat layout)
                html.Div([
                    html.Label("Beneficiary Type", className="sidebar-label"),
                    dcc.Dropdown(id="benificiery-dropdown", options=[], multi=True, value=[], placeholder="All Beneficiaries"),
                ], className="filter-group"),
                
                html.Div([
                    html.Label("Anemia Status", className="sidebar-label"),
                    dcc.Dropdown(id="anemia-dropdown", options=[{"label": x.capitalize(), "value": x} for x in anemia_list], multi=True, value=[], placeholder="All Categories"),
                ], className="filter-group"),

                dbc.Button("Clear All Filters", 
                           id="btn-clear", color="secondary", outline=True, size="sm", 
                           className="w-100 mb-4", style={"fontSize": "0.75rem", "borderRadius": "8px"}),

                html.Div([
                    html.Label("Management Tools", className="sidebar-label"),
                    dbc.ButtonGroup([
                        dbc.Button([html.I(className="fas fa-file-excel me-2"), "Excel"], id="btn-excel", color="success", outline=True, size="sm", style={"fontSize": "0.7rem"}),
                        dbc.Button([html.I(className="fas fa-file-csv me-2"), "CSV"], id="btn-csv", color="primary", outline=True, size="sm", style={"fontSize": "0.7rem"}),
                    ], className="w-100"),
                ], className="filter-group"),

                # Placeholder for urgent alerts to satisfy callback output in multi-page environment
                html.Div(id="urgent-alerts-list", style={"display": "none"}),
            ], style={"flex": "1"}),
            
            html.Div([
                html.Div([
                    html.Div(className="status-dot"),
                    html.Span("Live Data Connection")
                ], className="status-badge")
            ], style={"marginTop": "auto", "padding": "10px 0"})
        ], id="sidebar", className="sidebar"),
        
        # Main Content
        html.Div([
            # Phase Marker
            html.Div([
                html.Span([html.I(className="fas fa-tag me-2"), "Baseline 1"], className="glowing-badge", style={"fontSize": "0.75rem", "padding": "4px 12px"})
            ], style={"textAlign": "left", "marginBottom": "10px"}),

            # Main Dashboard Grid
            dbc.Row([
                # KPI Section (Moved up to top row since branding is now in fixed top bar)
                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-users kpi-icon"), html.P("Total Enrolled", className="kpi-label")], className="kpi-header"),
                    html.H3(id="total", className="kpi-value")
                ], className="kpi-card"), xs=12, sm=6, md=4, lg=True),

                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-chart-line kpi-icon", style={"color": "#6366f1"}), html.P("Prevalence of Anemia", className="kpi-label")], className="kpi-header"),
                    html.H3(id="prevalence-val", className="kpi-value")
                ], className="kpi-card"), xs=6, sm=4, md=True),
                
                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-check-circle kpi-icon", style={"color": "#10b981"}), html.P("Normal", className="kpi-label")], className="kpi-header"),
                    html.H3(id="normal-count", className="kpi-value")
                ], className="kpi-card"), xs=6, sm=4, md=True),
                
                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-info-circle kpi-icon", style={"color": "#f59e0b"}), html.P("Mild", className="kpi-label")], className="kpi-header"),
                    html.H3(id="mild-count", className="kpi-value")
                ], className="kpi-card"), xs=6, sm=4, md=True),
                
                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-exclamation-circle kpi-icon", style={"color": "#f97316"}), html.P("Moderate", className="kpi-label")], className="kpi-header"),
                    html.H3(id="moderate-count", className="kpi-value")
                ], className="kpi-card"), xs=6, sm=4, md=True),
                
                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-exclamation-triangle kpi-icon", style={"color": "#ef4444"}), html.P("Severe", className="kpi-label")], className="kpi-header"),
                    html.H3(id="severe-count", className="kpi-value")
                ], className="kpi-card"), xs=6, sm=4, md=True),
                
                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-droplet kpi-icon", style={"color": "#991b1b"}), html.P("Avg Hb (g/dL)", className="kpi-label")], className="kpi-header"),
                    html.H3(id="avg-hgb", className="kpi-value")
                ], className="kpi-card"), xs=6, sm=4, md=True),
                
                dbc.Col(html.Div([
                    html.Div([html.I(className="fas fa-utensils kpi-icon", style={"color": "#8b5cf6"}), html.P("Dietary", className="kpi-label")], className="kpi-header"),
                    html.H3(id="diet-count", className="kpi-value")
                ], className="kpi-card"), xs=6, sm=4, md=True),
            ], className="mb-4 g-3"),
            
            # Grid Section
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5("Geospatial Distribution", className="graph-title"),
                        dcc.Graph(id="map", config={"responsive": True, "displayModeBar": False}, style=MAP_CARD_STYLE),
                    ], className="graph-card")
                ], xs=12, xl=8),
                
                dbc.Col([
                    html.Div([
                        html.H5("Case Classification", className="graph-title"),
                        dcc.Graph(id="anemia-pie", config={"responsive": True, "displayModeBar": False}, style={"height": "265px"}),
                    ], className="graph-card", style={"marginBottom": "24px"}),
                    
                    html.Div([
                        html.H5("Beneficiary Distribution", className="graph-title"),
                        dcc.Graph(id="benificiery-bar", config={"responsive": True, "displayModeBar": False}, style={"height": "265px"}),
                    ], className="graph-card")
                ], xs=12, xl=4)
            ], className="mb-4 g-3"),
            
            # Comparison Row
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5("Nutritional Status Analysis (BMI Distribution)", className="graph-title"),
                        dcc.Graph(id="bmi-bar", config={"responsive": True, "displayModeBar": False}, style={"height": "450px"}),
                    ], className="graph-card")
                ], xs=12, lg=6),
                
                dbc.Col([
                    html.Div([
                        html.H5("PSU-wise Hemoglobin Analysis (Mean & SD)", className="graph-title"),
                        dcc.Graph(id="hgb-stats-bar", config={"responsive": True, "displayModeBar": False}, style={"height": "450px"}),
                    ], className="graph-card")
                ], xs=12, lg=6),
            ], className="mb-4 g-3"),
            
            # Geospatial/Demographic Row (Renamed for clarity as Anemia Village is here now)
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5("PSU-wise Anemia Classification", className="graph-title"),
                        dcc.Graph(id="anemia-village-bar", config={"responsive": True, "displayModeBar": False}, style={"height": "450px"}),
                    ], className="graph-card")
                ], xs=12),
            ], className="mb-4 g-3"),

            # Table Section
            html.Div([
                html.H5("Detailed Beneficiary Records", className="graph-title"),
                dash_table.DataTable(
                    id="table", page_size=15, filter_action="native", sort_action="native",
                    style_table={"overflowX": "auto", "minWidth": "100%"}, 
                    style_cell={"padding": "12px", "textAlign": "left", "fontFamily": "-apple-system, BlinkMacSystemFont, sans-serif", "fontSize": "0.875rem", "minWidth": "150px"},
                    style_header={"fontWeight": "600", "backgroundColor": "#f8fafc", "color": "#475569", "borderBottom": "2px solid #e2e8f0"},
                    fixed_rows={'headers': True},
                    style_data_conditional=[
                        {'if': {'filter_query': '{anemia_category} = "Normal"'}, 'backgroundColor': '#f0fdf4', 'color': '#166534'},
                        {'if': {'filter_query': '{anemia_category} = "Mild"'}, 'backgroundColor': '#fffbeb', 'color': '#92400e'},
                        {'if': {'filter_query': '{anemia_category} = "Moderate"'}, 'backgroundColor': '#fff7ed', 'color': '#9a3412'},
                        {'if': {'filter_query': '{anemia_category} = "Severe"'}, 'backgroundColor': '#fef2f2', 'color': '#991b1b'},
                        {'if': {'filter_query': '{anemia_category} = "Incomplete"'}, 'backgroundColor': '#f8fafc', 'color': '#475569'},
                    ]
                )
            ], className="graph-card"),
            
            get_footer()
        ], id="main-content", className="main-content")
    ])


app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Interval(id="interval", interval=60_000, n_intervals=0),
    dcc.Store(id="stored-data"),
    dcc.Download(id="download-data"),
    
    # Fixed Top Bar
    html.Nav([
        html.Div([
            html.Div([
                html.Img(src="/main_logo.svg", style={"height": "40px", "marginRight": "15px"}),
                html.Div([
                    html.Span("PRAKASH", style={"fontWeight": "800", "fontSize": "1.75rem", "marginRight": "10px"}),
                    html.Span("AMB 2.0 T³", className="glowing-badge", style={"fontSize": "0.9rem"})
                ], style={"display": "flex", "alignItems": "center"}),
            ], className="top-bar-title", style={"display": "flex", "alignItems": "center"}),
            
            # Sub-header Buttons
            html.Div([
                dcc.Link("Test", href="/", className="nav-btn nav-btn-track"),
                dcc.Link("Treat", href="/treat", className="nav-btn nav-btn-treat"),
                dcc.Link("Track", href="/track", className="nav-btn nav-btn-test")
            ], className="nav-buttons", style={"marginTop": "5px"})
        ], style={"display": "flex", "flexDirection": "column"}),
        
        html.Div([
            html.Img(src="/images.png", style={"height": "70px", "mixBlendMode": "multiply"}),
            html.Img(src="/government-of-karnataka.webp", style={"height": "70px", "marginLeft": "-20px"})
        ], style={"display": "flex", "alignItems": "center"})
    ], className="top-bar", style={"height": "120px"}), # Increased height to accommodate buttons

    # Mobile Header (Only visible on mobile)
    html.Div([
        dbc.Button(html.I(className="fas fa-bars"), id="btn-toggle", className="toggle-button"),
        html.Img(src="/main_logo.svg", style={"height": "30px", "marginLeft": "10px"}),
        html.Div([
            html.Span("PRAKASH", style={"fontWeight": "800", "fontSize": "1.1rem", "marginRight": "5px"}),
            html.Span("AMB 2.0 T³", className="glowing-badge", style={"fontSize": "0.65rem", "padding": "1px 6px"})
        ], style={"display": "flex", "alignItems": "center", "marginLeft": "10px", "flex": "1"}),
        html.Div([
            html.Img(src="/images.png", style={"height": "40px", "mixBlendMode": "multiply"}),
            html.Img(src="/government-of-karnataka.webp", style={"height": "40px", "marginLeft": "-10px"})
        ], style={"display": "flex", "alignItems": "center", "marginLeft": "auto"})
    ], className="mobile-nav"),

    # Page Content Container
    html.Div(id="page-content")
], id="main-container")

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/track":
        return html.Div([
            # Phase Marker
            html.Div([
                html.Span([html.I(className="fas fa-tag me-2"), "Baseline 1"], className="glowing-badge", style={"fontSize": "0.75rem", "padding": "4px 12px"})
            ], style={"textAlign": "left", "marginBottom": "10px"}),
            html.H1("Track Page", style={"textAlign": "center", "marginTop": "200px"}),
            html.P("This page is under development and will be available soon", style={"textAlign": "center"}),
            get_footer()
        ], style={"padding": "40px"})
    elif pathname == "/treat":
        return get_treat_layout()
    else:
        # Default to the Main Dashboard (Now under 'Test' branding in Nav)
        return get_dashboard_layout()

@app.callback(
    [Output("sidebar", "className"), Output("main-content", "className")],
    [Input("btn-toggle", "n_clicks")],
    [State("sidebar", "className")]
)
def toggle_sidebar(n, current_class):
    if not n:
        return "sidebar", "main-content"
    
    if "sidebar-visible" in current_class:
        return "sidebar", "main-content"
    else:
        return "sidebar sidebar-visible", "main-content full-width"

@app.callback(Output("stored-data", "data"), Input("interval", "n_intervals"))
def refresh_data(_):
    df, msg, is_err = load_data()
    
    # Automatically sync to sheets in a BACKGROUND THREAD to prevent blocking the UI
    if not is_err and not df.empty:
        threading.Thread(target=sync_data_to_sheets, args=(df,), daemon=True).start()
        
    return {
        "records": df.to_dict("records"),
        "status": msg,
        "is_error": is_err,
        "last_updated": datetime.now().strftime("%H:%M:%S")
    }

@app.callback(
    [
        Output("total", "children"), Output("normal-count", "children"),
        Output("moderate-count", "children"), Output("severe-count", "children"),
        Output("mild-count", "children"), Output("avg-hgb", "children"),
        Output("diet-count", "children"),
        Output("prevalence-val", "children"),
        Output("map", "figure"), Output("benificiery-bar", "figure"),
        Output("anemia-pie", "figure"), Output("anemia-village-bar", "figure"),
        Output("hgb-stats-bar", "figure"),
        Output("bmi-bar", "figure"),
        Output("table", "data"), Output("table", "columns"),
        Output("location-dropdown", "options"),
        Output("benificiery-dropdown", "options"), Output("anemia-dropdown", "options"),
        Output("location-dropdown", "value"),
        Output("benificiery-dropdown", "value"), Output("anemia-dropdown", "value"),
        Output("urgent-alerts-list", "children"),
    ],
    [
        Input("stored-data", "data"), Input("location-dropdown", "value"),
        Input("benificiery-dropdown", "value"),
        Input("anemia-dropdown", "value"), Input("interval", "n_intervals"),
        Input("map", "clickData"), Input("anemia-pie", "clickData"),
        Input("benificiery-bar", "clickData"), Input("btn-clear", "n_clicks"),
        Input("url", "pathname")
    ]
)
def update_dashboard(stored_dict, location, benificiery, anemia, n_intervals, map_click, pie_click, bar_click, n_clear, pathname):
    try:
        return internal_update_dashboard(stored_dict, location, benificiery, anemia, n_intervals, map_click, pie_click, bar_click, n_clear, pathname)
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in update_dashboard: {str(e)}")
        print(traceback.format_exc())
        return [0]*8 + [go.Figure()]*6 + [[]]*9

def internal_update_dashboard(stored_dict, location, benificiery, anemia, n_intervals, map_click, pie_click, bar_click, n_clear, pathname):
    if not stored_dict or "records" not in stored_dict:
        # Return 22 elements to match the number of outputs
        return [0]*8 + [go.Figure()]*6 + [[]]*9
    
    records = stored_dict["records"]
    status_msg = stored_dict["status"]
    is_error = stored_dict["is_error"]
    last_upd = stored_dict.get("last_updated", "")

    if not records and is_error:
        # Return 22 elements
        return [0]*8 + [go.Figure()]*6 + [[]]*9

    df_full = pd.DataFrame(records)
    
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    # EXTREME LOGGING: INPUTS
    print(f"\n>>> CALLBACK START: {triggered_id}")
    print(f">>> INPUT LOCATION: {location}")
    print(f">>> INPUT BENIF: {benificiery}")
    print(f">>> INPUT ANEMIA: {anemia}")
    
    # FORCED TYPE ENFORCEMENT
    location = [location] if isinstance(location, str) else (location or [])
    benificiery = [benificiery] if isinstance(benificiery, str) else (benificiery or [])
    anemia = [anemia] if isinstance(anemia, str) else (anemia or [])
    
    # TRACE LOGGING
    print(f"DEBUG: Trigger: {triggered_id} | In Location: {location} | Map Click: {'Present' if map_click else 'None'}")

    # Handle Chart Interactions (Cross-Filtering)
    if triggered_id == "btn-clear":
        print("DEBUG: Clearing all filters via button.")
        location, benificiery, anemia = [], [], []
        
    elif triggered_id == "map" and map_click:
        village_clicked = map_click["points"][0].get("text")
        print(f"DEBUG: Map clicked on: {village_clicked}")
        if village_clicked and village_clicked in df_full["PSU Name"].values:
            # Find the full location string for this PSU
            loc_val = df_full[df_full["PSU Name"] == village_clicked]["Location"].iloc[0]
            if not location or loc_val not in location:
                location = [loc_val] 
                print(f"DEBUG: Location updated from map to: {location}")
            else:
                print("DEBUG: Location already contains this village, no change.")
            
    elif triggered_id == "anemia-pie" and pie_click:
        cat_clicked = pie_click["points"][0].get("label").lower()
        if cat_clicked:
            anemia = [cat_clicked]
            print(f"DEBUG: Anemia filter updated to: {anemia}")

    elif triggered_id == "benificiery-bar" and bar_click:
        benif_clicked = bar_click["points"][0].get("x")
        if benif_clicked:
            benificiery = [benif_clicked]
            print(f"DEBUG: Beneficiary filter updated to: {benificiery}")

    driver_triggers = ["stored-data", "interval"]
    # We will always update the dashboard components to ensure they stay in sync with filters
    is_full_update = True 

    # Dynamic Options (Cascading Filters)
    # 1. Location options: Filtered by Benificiery, Anemia
    df_loc = df_full.copy()
    if benificiery: df_loc = df_loc[df_loc["Benificiery"].isin(benificiery)]
    if anemia: df_loc = df_loc[df_loc["anemia_category"].isin(anemia)]
    loc_opts = [{"label": x, "value": x} for x in sorted(df_loc["Location"].dropna().unique())]

    # Clean up Location selection if not in new options
    if location:
        valid_locs = [o["value"] for o in loc_opts]
        location = [l for l in location if l in valid_locs]

    # 2. Benificiery options: Filtered by Location, Anemia
    df_benif = df_full.copy()
    if location: df_benif = df_benif[df_benif["Location"].isin(location)]
    if anemia: df_benif = df_benif[df_benif["anemia_category"].isin(anemia)]
    benif_opts = [{"label": x, "value": x} for x in sorted(df_benif["Benificiery"].dropna().unique())]

    # 3. Anemia options: Filtered by Location, Benificiery (Logic added for dynamic cascading)
    df_anemia_opts = df_full.copy()
    if location: df_anemia_opts = df_anemia_opts[df_anemia_opts["Location"].isin(location)]
    if benificiery: df_anemia_opts = df_anemia_opts[df_anemia_opts["Benificiery"].isin(benificiery)]
    # Normalize anemia categories to capitalize for label
    anemia_opts_raw = sorted(df_anemia_opts["anemia_category"].dropna().unique())
    anemia_opts = [{"label": x.capitalize(), "value": x} for x in anemia_opts_raw]

    # Apply all final filters to the main df for stats/charts
    df = df_full.copy()
    if location: df = df[df["Location"].isin(location)]
    if benificiery: df = df[df["Benificiery"].isin(benificiery)]
    if anemia: 
        # Ensure case-insensitive matching for anemia category
        df = df[df["anemia_category"].str.lower().isin([x.lower() for x in anemia])]

    total = len(df)
    normal = (df["anemia_category"] == "normal").sum()
    mild = (df["anemia_category"] == "mild").sum()
    moderate = (df["anemia_category"] == "moderate").sum()
    severe = (df["anemia_category"] == "severe").sum()
    # Diet analytics: Track Diet 1 and Diet 2 (KPI specifically uses Diet 2/Diet1 as per requirement)
    # Check specifically for "yes" (case-insensitive)
    # Blank/NaN values are considered "no"
    if "Diet 2" in df.columns:
        diet_yes = (df["Diet 2"].astype(str).str.strip().str.lower() == "yes").sum()
    elif "Diet 1" in df.columns:
        diet_yes = (df["Diet 1"].astype(str).str.strip().str.lower() == "yes").sum()
    else:
        diet_yes = 0
    avg_hgb = round(df["HGB"].mean(), 2) if not df.empty else 0
    prevalence = round(((mild + moderate + severe) / total * 100), 1) if total > 0 else 0
    prevalence_str = f"{prevalence}%"

    # Formatting KPIs with percentages (Percentage not bold)
    def get_kpi_str(count, total):
        pct = round((count / total * 100), 1) if total > 0 else 0
        return [
            str(count), 
            html.Span(f" ({pct}%)", style={"fontWeight": "400", "fontSize": "0.85em", "color": "#64748b", "marginLeft": "2px"})
        ]

    normal_kpi = get_kpi_str(normal, total)
    mild_kpi = get_kpi_str(mild, total)
    moderate_kpi = get_kpi_str(moderate, total)
    severe_kpi = get_kpi_str(severe, total)

    color_map = {"normal": "#10b981", "mild": "#f59e0b", "moderate": "#f97316", "severe": "#ef4444", "incomplete": "#94a3b8"}

    table_order = [
        "SL.NO", "ID", "enrollment_date", "Area COde", "PSU Name",
        "Name", "Household Name", "Gender", "Benificiery", "Age",
        "Length", "Height", "Weight", "BMI", "bmi_category",
        "sample_status", "Sample Collected Date", "Collected By",
        "HGB", "anemia_category", "Asha_Worker", "whatsapp", "field_investigator", "Diet", "data_operator"
    ]
    available_cols = [c for c in table_order if c in df.columns or c == "whatsapp"]
    df_table = df.copy()

    # Pre-calculate grouped WhatsApp messages for each Asha Worker
    asha_summaries = {}
    high_risk_df = df[df["anemia_category"].str.lower().isin(["moderate", "severe"])]
    if not high_risk_df.empty and "Asha_Worker" in df.columns:
        for asha, group in high_risk_df.groupby("Asha_Worker"):
            summary_parts = []
            # Group by category for a cleaner message
            for cat in ["Severe", "Moderate"]:
                cat_group = group[group["anemia_category"].str.capitalize() == cat]
                if not cat_group.empty:
                    # Each ID on a new line with a bullet
                    id_list = "\n- ".join(cat_group["ID"].astype(str).unique().tolist())
                    summary_parts.append(f"*{cat}*:\n- {id_list}")
            
            summary_text = "\n\n".join(summary_parts)
            asha_summaries[asha] = f"Hello {asha}, here is the combined list of anemic subjects for follow-up:\n\n{summary_text}\n\nPlease check on them today."

    # Generate WhatsApp Links for table [Grouped Version]
    def generate_wa_link(row):
        asha_name = row.get("Asha_Worker")
        contact = str(row.get("Aasha_Contact", ""))
        cat = str(row.get("anemia_category", "")).lower()
        
        if cat in ["moderate", "severe"] and contact != "" and contact != "nan" and asha_name in asha_summaries:
            msg = asha_summaries[asha_name]
            encoded_msg = urllib.parse.quote(msg)
            link = f"https://wa.me/{contact}?text={encoded_msg}"
            return f"[![WA](https://img.shields.io/badge/Notify-WhatsApp-25D366?style=flat-square&logo=whatsapp)]({link})"
        return ""

    df_table["whatsapp"] = df_table.apply(generate_wa_link, axis=1)
    df_table = df_table[available_cols].copy()
    date_cols_to_format = ["enrollment_date", "Sample Collected Date"]
    for col in date_cols_to_format:
        if col in df_table.columns:
            df_table[col] = pd.to_datetime(df_table[col], errors='coerce').dt.strftime('%d/%m/%Y').fillna("")

    for col in df_table.columns:
        if df_table[col].dtype == 'object':
            df_table[col] = df_table[col].astype(str).str.title()

    # Removed is_full_update check to ensure dashboard always reflects current filter state

    if pathname == "/treat":
        map_fig = create_treat_map(df)
    else:
        map_fig = create_map(df)
    
    # Age-wise breakdown for Benificiery Hover
    def get_age_bucket(age):
        if pd.isna(age): return "Missing"
        if age < 1: return f"{int(round(age*12))} Months"
        if age < 5: return "1-4 Years"
        if age <=9: return "5-9 Years"
        if age < 18: return "10-17 Years"
        if age < 30: return "18-29 Years"
        if age < 40: return "30-39 Years"
        if age < 50: return "40-49 Years"
        return "50+ Years"

    # Inverse map to get codes from names
    NAME_TO_CODE = {v: k for k, v in BENEFICIARY_MAP.items()}

    benif_counts = df["Benificiery"].value_counts().sort_index()
    age_hover_data = []
    labels_with_codes = []
    
    for b_group in benif_counts.index:
        # Get numeric code
        b_code = NAME_TO_CODE.get(b_group, b_group)
        labels_with_codes.append(str(b_code))
        
        # Get age breakdown for hover
        sub = df[df["Benificiery"] == b_group]
        buckets = sub["Age"].apply(get_age_bucket).value_counts()
        b_str = "<br>".join([f"• {b}: {c}" for b, c in buckets.items()])
        
        # Build the full hover text
        hover_label = f"<span style='font-size:14px; color:#1e293b'><b>{b_code}: {b_group}</b></span><br>"
        age_hover_data.append(hover_label + f"Total: <b>{len(sub)}</b><br><br><b>Age Breakdown:</b><br>" + b_str)

    # Beneficiary Distribution (Vertical Bar with Codes)
    benif_bar = go.Figure(go.Bar(
        x=labels_with_codes,
        y=benif_counts.values,
        marker=dict(
            color="#6366f1",
            line=dict(color="#312e81", width=2)
        ),
        customdata=age_hover_data,
        hovertemplate="%{customdata}<extra></extra>",
        opacity=0.9
    ))
    benif_bar.update_layout(
        margin=dict(t=40, b=110, l=40, r=20),
        xaxis=dict(
            title=dict(text="Beneficiary Code", standoff=0), 
            automargin=True, 
            showgrid=False, 
            tickfont=dict(size=12, color="#64748b")
        ),
        yaxis=dict(title="Count", automargin=True, showgrid=True, gridcolor="#f1f5f9", tickfont=dict(color="#64748b")),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="-apple-system, BlinkMacSystemFont, sans-serif", font_color="#0f172a", bordercolor="#cbd5e1"),
        height=360,
        uirevision=True # Preserve selection/zoom state
    )

    # Anemia pie
    anemia_counts = df["anemia_category"].value_counts()
    anemia_pie = go.Figure(go.Pie(
        labels=[str(l).capitalize() for l in anemia_counts.index],
        values=anemia_counts.values,
        hole=0.6,
        marker=dict(colors=[color_map.get(str(l).lower(), "#cbd5e1") for l in anemia_counts.index],
                    line=dict(color='white', width=3)), # Wider border for pie focus
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>Count: <b>%{value}</b> (%{percent})<extra></extra>",
        opacity=0.95
    ))
    anemia_pie.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5, font=dict(size=10, color="#64748b")),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="-apple-system, BlinkMacSystemFont, sans-serif", font_color="#0f172a", bordercolor="#cbd5e1"),
        height=250,
        uirevision=True # Preserve slice selection state
    )
    # Give the pie more room
    anemia_pie.update_traces(domain=dict(y=[0.2, 1.0]))

    # Village-wise Anemia Classification (Stacked Bar with Area Codes)
    psu_to_code = df.set_index("PSU Name")["Area COde"].to_dict() if not df.empty else {}
    
    village_anemia = df.groupby(["PSU Name", "anemia_category"]).size().unstack(fill_value=0)
    village_area_codes = [str(psu_to_code.get(psu, psu)) for psu in village_anemia.index]
    
    # Pre-calculate a "dialogue box" summary for each PSU
    psu_summaries = []
    for psu in village_anemia.index:
        counts = village_anemia.loc[psu]
        summary = f"<span style='font-size:16px; color:#1e293b'><b>{psu}</b></span><br>"
        # Using Category names the user requested
        summary += f"Severe: <b>{counts.get('severe', 0)}</b><br>"
        summary += f"Moderate: <b>{counts.get('moderate', 0)}</b><br>"
        summary += f"Mild: <b>{counts.get('mild', 0)}</b><br>"
        summary += f"Normal: <b>{counts.get('normal', 0)}</b>"
        psu_summaries.append(summary)

    anemia_village_bar = go.Figure()
    for cat in ["normal", "mild", "moderate", "severe", "incomplete"]:
        if cat in village_anemia:
            anemia_village_bar.add_bar(
                name=cat.capitalize(), 
                x=village_anemia.index, # Setting X to Name for Header
                y=village_anemia[cat], 
                customdata=psu_summaries, 
                hovertemplate="%{customdata}<extra></extra>",
                marker=dict(
                    color=color_map.get(cat),
                    line=dict(color='white', width=1.5)
                ),
                opacity=0.95
            )
            
    anemia_village_bar.update_layout(
        barmode="stack", 
        hovermode="closest",
        margin=dict(t=30, b=80, l=40, r=20),
        xaxis=dict(
            title=dict(text="Area Code", standoff=0), 
            tickvals=village_anemia.index, # Map Names to Ticks
            ticktext=village_area_codes, # Show Codes on Ticks
            automargin=True, 
            showgrid=False, 
            tickfont=dict(size=11, color="#64748b"),
            showspikes=True, spikemode="across", spikesnap="cursor", showline=True, spikedash="dot", spikecolor="#94a3b8", spikethickness=1
        ),
        yaxis=dict(title="Beneficiaries", automargin=True, showgrid=True, gridcolor="#f1f5f9", tickfont=dict(color="#64748b")),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5, font=dict(size=11, color="#475569")),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="-apple-system, BlinkMacSystemFont, sans-serif", font_color="#0f172a", bordercolor="#cbd5e1"),
        height=450,
        bargap=0.2,
        uirevision=True # Preserve zoom/pan state
    )

    # --- Village-wise Bar Chart (Mean & SD STATS) ---
    hgb_data = df.dropna(subset=["HGB", "PSU Name"])
    hgb_stats_fig = go.Figure()

    if not hgb_data.empty:
        # Calculate stats per village
        stats = hgb_data.groupby("PSU Name")["HGB"].agg(["mean", "std", "count"]).reset_index().round(2)
        
        # Calculate Anemic Count (Mild + Moderate + Severe)
        anemic_df = df[df["anemia_category"].str.lower().isin(["mild", "moderate", "severe"])]
        anemic_counts = anemic_df.groupby("PSU Name").size().reset_index(name="anemic_count")
        
        # Merge to ensure alignment
        stats = pd.merge(stats, anemic_counts, on="PSU Name", how="left").fillna(0)
        stats = stats.sort_values("PSU Name")
        
        # Bar Chart with Tooltip info (Area Codes for labels)
        stats["area_code"] = stats["PSU Name"].map(psu_to_code).astype(str)
        
        hgb_stats_fig.add_trace(go.Bar(
            x=stats["PSU Name"],
            y=stats["mean"],
            error_y=dict(type='data', array=stats["std"], visible=True, color="#312e81", thickness=2, width=6),
            marker=dict(
                color="#6366f1",
                line=dict(color="#312e81", width=2),
            ),
            opacity=0.9,
            name="Mean HGB",
            text=stats["mean"],
            textposition="auto",
            textfont=dict(color="white", size=10, family="-apple-system, BlinkMacSystemFont, sans-serif"),
            customdata=stats[["PSU Name", "area_code", "std", "count", "anemic_count"]].values.tolist(),
            hovertemplate=(
                "<span style='font-size:16px; color:#1e293b'><b>%{customdata[0]}</b></span><br>" +
                "Mean HGB: <b>%{y} g/dL</b><br>" +
                "Std Dev: <b>%{customdata[2]}</b><br>" +
                "Total Samples: <b>%{customdata[3]}</b><br>" +
                "Anemic Count: <b>%{customdata[4]}</b><extra></extra>"
            )
        ))
        
        group_avg = hgb_data["HGB"].mean()
        # Add the reference line 
        hgb_stats_fig.add_hline(y=group_avg, line_dash="dash", line_color="#10b981", line_width=2)
        
        # Add legend-style annotation
        hgb_stats_fig.add_annotation(
            xref="paper", yref="paper",
            x=1.0, y=1.08,
            text=f"<span style='color:#10b981'><b>--</b></span> Dataset Average: <b>{group_avg:.2f}</b>",
            showarrow=False,
            font=dict(size=12, family="-apple-system, BlinkMacSystemFont, sans-serif", color="#475569"),
            xanchor="right", yanchor="bottom"
        )

    hgb_stats_fig.update_layout(
        margin=dict(t=50, b=80, l=50, r=20),
        hovermode="closest",
        xaxis=dict(
            title=dict(text="Area Code", standoff=0), 
            tickvals=stats["PSU Name"] if not hgb_data.empty else [],
            ticktext=stats["area_code"] if not hgb_data.empty else [],
            automargin=True, 
            showgrid=False, 
            tickfont=dict(size=11, color="#64748b"),
            showspikes=True, spikemode="across", spikesnap="cursor", showline=True, spikedash="dot", spikecolor="#94a3b8", spikethickness=1
        ),
        yaxis=dict(title="Avg Hemoglobin (g/dL)", automargin=True, showgrid=True, gridcolor="#f1f5f9", tickfont=dict(color="#64748b")),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="-apple-system, BlinkMacSystemFont, sans-serif", font_color="#0f172a", bordercolor="#cbd5e1"),
        height=450,
        showlegend=False,
        bargap=0.2,
        uirevision=True # Preserve zoom/pan state
    )
    
    # BMI Distribution Bar Chart (Stacked by Beneficiary)
    if "Benificiery" in df.columns and "bmi_category" in df.columns:
        bmi_ben_counts = df.groupby(["Benificiery", "bmi_category"]).size().unstack(fill_value=0)
    else:
        bmi_ben_counts = pd.DataFrame()

    bmi_colors = {
        "Wasted": "#ef4444",
        "Thinness": "#ef4444",
        "Underweight": "#ef4444",
        "Normal": "#10b981",
        "Overweight": "#f59e0b",
        "Obese": "#b91c1c",
        "Pregnancy": "#8b5cf6",
        "Missing": "#94a3b8"
    }
    
    # Simplified stacking order for cleaner report
    stack_order = ["Wasted", "Thinness", "Underweight", "Normal", "Overweight", "Obese", "Pregnancy", "Missing"]
            
    bmi_fig = go.Figure()
    
    if not bmi_ben_counts.empty:
        # Pre-calculate summaries for each Beneficiary
        ben_summaries = {}
        for ben in bmi_ben_counts.index:
            row = bmi_ben_counts.loc[ben]
            parts = []
            # Use stack_order for consistent ordering in tooltip
            for c in stack_order:
                if c in row and row[c] > 0:
                    parts.append(f"{c}: <b>{row[c]}</b>")
            # Also add extra categories not in stack_order
            for c in row.index:
                if c not in stack_order and row[c] > 0:
                    parts.append(f"{c}: <b>{row[c]}</b>")
            ben_summaries[ben] = "<br>".join(parts)

        # Map summaries to the x-axis order
        custom_data_list = [ben_summaries.get(b, "") for b in bmi_ben_counts.index]

        # Ensure all columns exist for consistent coloring even if count is 0
        present_cats = [c for c in stack_order if c in bmi_ben_counts.columns]
        # Also add any unexpected categories found in data
        extra_cats = [c for c in bmi_ben_counts.columns if c not in stack_order]
        final_order = present_cats + extra_cats
        
        for cat in final_order:
            if cat in bmi_ben_counts:
                bmi_fig.add_trace(go.Bar(
                    name=cat,
                    x=bmi_ben_counts.index,
                    y=bmi_ben_counts[cat],
                    marker=dict(
                        color=bmi_colors.get(cat, "#cbd5e1"),
                        line=dict(color="white", width=1)
                    ),
                    customdata=custom_data_list,
                    # Hover: Show current segment + Full Summary
                    hovertemplate="<b>%{x}</b><br>" + cat + ": <b>%{y}</b><br><br><b>Total Breakdown:</b><br>%{customdata}<extra></extra>"
                ))
    else:
        # Fallback empty chart 
        bmi_fig.add_annotation(text="No Data", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)

    bmi_fig.update_layout(
        barmode="stack",
        margin=dict(t=30, b=50, l=50, r=20),
        xaxis=dict(title="Beneficiary Type", showgrid=False, tickfont=dict(color="#64748b")),
        yaxis=dict(title="Count", showgrid=True, gridcolor="#f1f5f9", tickfont=dict(color="#64748b")),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="-apple-system, BlinkMacSystemFont, sans-serif", font_color="#0f172a", bordercolor="#cbd5e1"),
        height=450,
        bargap=0.3,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=10, color="#475569")),
        uirevision=True # Preserve zoom/pan state
    )
    # ----------------------------------------------

    # Urgent Alerts (Severe Anemia)
    urgent_df = df_full[df_full["anemia_category"] == "severe"].head(10)
    urgent_list = []
    for _, row in urgent_df.iterrows():
        # Generate WP link for sidebar [Grouped Version]
        contact = str(row.get("Aasha_Contact", ""))
        asha_name = row.get("Asha_Worker")
        p_id = str(row.get("ID", "Missing"))
        
        wa_btn = None
        if contact != "" and contact != "nan" and asha_name in asha_summaries:
            msg = asha_summaries[asha_name]
            encoded_msg = urllib.parse.quote(msg)
            link = f"https://wa.me/{contact}?text={encoded_msg}"
            wa_btn = html.A(html.I(className="fab fa-whatsapp", style={"color": "#25D366", "marginLeft": "10px", "fontSize": "1.1rem"}), 
                            href=link, target="_blank")

        urgent_list.append(html.Div([
            html.Div([
                html.Span(f"ID: {p_id}", style={"fontWeight": "600"}),
                html.Span(f" | Hb: {row.get('HGB', 'N/A')}", style={"color": "#ef4444"}),
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"}),
            html.Div([
                html.P(f"{row.get('PSU Name', 'Missing')}", style={"margin": 0, "fontSize": "0.65rem", "color": "#64748b"}),
                wa_btn if wa_btn else html.Span()
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"})
        ], className="urgent-item"))
    
    if not urgent_list:
        urgent_list = [html.P("No urgent cases found.", className="text-muted", style={"fontSize": "0.75rem"})]

    # Define display names for specific columns
    col_names = {
        "whatsapp": "Notify Asha",
        "HGB": "HGB (g/dL)",
        "Length": "Length (Age < 2 years)",
        "Height": "Height (cm)",
        "Weight": "Weight (kg)",
        "bmi_category": "Nutritional Status"
    }
    
    table_cols = [
        {
            "name": col_names.get(c, c), 
            "id": c, 
            "presentation": "markdown" if c == "whatsapp" else "input"
        } for c in available_cols
    ]

    print(f">>> RETURNING LOCATION: {location}")
    print(f">>> CALLBACK END: {triggered_id}\n")
    return (total, normal_kpi, moderate_kpi, severe_kpi, mild_kpi, avg_hgb, diet_yes, prevalence_str, map_fig, benif_bar, anemia_pie, anemia_village_bar, hgb_stats_fig, bmi_fig, df_table.to_dict("records"), table_cols, loc_opts, benif_opts, anemia_opts, location, benificiery, anemia, urgent_list)


# =========================
# EXPORT CALLBACKS
# =========================
@app.callback(
    Output("download-data", "data"),
    [Input("btn-excel", "n_clicks"), Input("btn-csv", "n_clicks")],
    [State("stored-data", "data"), State("location-dropdown", "value"),
     State("benificiery-dropdown", "value"), State("anemia-dropdown", "value")],
    prevent_initial_call=True
)
def export_data(n_excel, n_csv, stored_dict, location, benif, anemia):
    try:
        ctx = callback_context
        if not ctx.triggered:
            return no_update
            
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Robust verification: Only proceed if a button was actually clicked (n_clicks > 0)
        if trigger == "btn-excel" and (n_excel is None or n_excel == 0):
            return no_update
        if trigger == "btn-csv" and (n_csv is None or n_csv == 0):
            return no_update
            
        if not stored_dict or "records" not in stored_dict:
            return no_update
        
        df = pd.DataFrame(stored_dict["records"])
        
        # Robust Type Enforcement for Filters
        location = [location] if isinstance(location, str) else (location or [])
        benif = [benif] if isinstance(benif, str) else (benif or [])
        anemia = [anemia] if isinstance(anemia, str) else (anemia or [])
        
        # Apply filters
        if location:
            df = df[df["Location"].isin(location)]
        if benif:
            df = df[df["Benificiery"].isin(benif)]
        if anemia:
            anemia_lower = [str(x).lower() for x in anemia]
            df = df[df["anemia_category"].str.lower().isin(anemia_lower)]

        # Format dates for export (DD/MM/YYYY)
        date_cols = ["enrollment_date", "Sample Collected Date"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y').fillna("")

        print(f"DEBUG: Exporting {len(df)} records. Trigger: {trigger}")

        if trigger == "btn-csv":
            return dcc.send_data_frame(df.to_csv, "prakash_data_export.csv", index=False)
        else:
            return dcc.send_data_frame(df.to_excel, "prakash_data_export.xlsx", index=False, engine="openpyxl")
    except Exception as e:
        print(f"CRITICAL ERROR in export_data: {e}")
        return no_update

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8060)


