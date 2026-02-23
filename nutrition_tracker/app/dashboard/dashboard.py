import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px

# --- CONFIGURATION ---
API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Bespoke Nutrition Tracker", page_icon="🥗", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_mode=True)

# --- SIDEBAR: User Selection ---
st.sidebar.title("👤 User Profile")
# In a real app, we'd fetch users from the DB. 
# For "exactly 2 users", we can input their Telegram IDs or Names.
user_name = st.sidebar.selectbox("Select User", ["User 1", "User 2"])
# Map names to Telegram IDs (placeholders - replace with your actual IDs)
user_map = {"User 1": 123456789, "User 2": 987654321}
telegram_id = user_map[user_name]

range_type = st.sidebar.radio("Time Range", ["daily", "weekly"])

st.title(f"🥗 {user_name}'s Nutrition Dashboard")

# --- DATA FETCHING ---
try:
    response = requests.get(f"{API_BASE_URL}/analytics", params={"telegram_id": telegram_id, "range_type": range_type})
    data = response.json()
except Exception as e:
    st.error(f"Could not connect to API: {e}")
    st.stop()

if "error" in data:
    st.warning(f"No data found for {user_name}. Start logging via Telegram!")
    st.stop()

# --- METRICS SECTION ---
col1, col2, col3, col4 = st.columns(4)

totals = data["totals"]
goals = data["goals"]

with col1:
    st.metric("Calories", f"{totals['calories']:.0f} kcal", f"{goals['calories'] - totals['calories']:.0f} remaining", delta_color="inverse")
with col2:
    st.metric("Protein", f"{totals['protein']:.1f}g", f"Goal: {goals['protein']}g")
with col3:
    st.metric("Carbs", f"{totals['carbs']:.1f}g")
with col4:
    st.metric("Fat", f"{totals['fat']:.1f}g")

# --- PROGRESS BARS ---
st.subheader("🎯 Goal Progress")
progress = data["progress"]["calories"]
st.progress(min(progress, 1.0), text=f"Calorie Intake: {progress*100:.1f}% of daily goal")

# --- VISUALIZATIONS ---
st.divider()
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📊 Macro Distribution")
    macro_df = pd.DataFrame({
        "Macro": ["Protein", "Carbs", "Fat"],
        "Grams": [totals['protein'], totals['carbs'], totals['fat']]
    })
    fig = px.pie(macro_df, values='Grams', names='Macro', color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("💡 Insights")
    if totals['protein'] < (goals['protein'] * 0.5):
        st.info("Try to add some lean protein to your next meal! 🍗")
    elif totals['calories'] > goals['calories']:
        st.warning("You've exceeded your calorie goal for today. 🚶‍♂️")
    else:
        st.success("You're right on track! Keep it up. 🌟")

# --- FOOTER ---
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
