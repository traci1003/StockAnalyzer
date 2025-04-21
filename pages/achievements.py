import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime
import json
import os

# Import local modules
from database import get_user_stats, get_achievements
from gamification import (
    display_achievements_section, 
    display_leaderboard,
    initialize_user_stats,
    update_visit_streak,
    check_achievements
)

# Configure page
st.set_page_config(
    page_title="Investment Achievements",
    page_icon="🏆",
    layout="wide"
)

def main():
    st.title("🏆 Investment Journey Achievements")
    
    # Initialize gamification on page load
    initialize_user_stats()
    update_visit_streak()
    new_achievements = check_achievements()
    
    # Display tabs
    tab1, tab2 = st.tabs(["My Achievements", "Leaderboard"])
    
    with tab1:
        # Stats summary
        stats = st.session_state.get('user_stats', {})
        
        # Create a progress summary at the top
        st.subheader("Your Investment Progress")
        
        # Progress metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Score", f"{stats.get('total_points', 0)} pts")
            
        with col2:
            streak = stats.get('consecutive_days', 0)
            streak_text = f"{streak} day{'s' if streak != 1 else ''}"
            st.metric("Visit Streak", streak_text)
            
        with col3:
            achievements_count = len(stats.get('achievements', []))
            st.metric("Achievements Unlocked", f"{achievements_count}/15")
        
        # Progress bar
        progress = min(1.0, achievements_count / 15)
        st.progress(progress)
        
        # Achievement badges
        display_achievements_section()
        
        # Activity history
        st.subheader("Recent Activity")
        
        # Create sample activity data
        activities = []
        
        # Add activities based on stats
        if stats.get('stocks_analyzed', 0) > 0:
            activities.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "activity": f"Analyzed {stats.get('stocks_analyzed', 0)} stocks",
                "points": stats.get('stocks_analyzed', 0) * 2
            })
        
        if stats.get('sentiment_checks', 0) > 0:
            activities.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "activity": f"Checked sentiment {stats.get('sentiment_checks', 0)} times",
                "points": stats.get('sentiment_checks', 0) * 3
            })
        
        if stats.get('ai_screener_uses', 0) > 0:
            activities.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "activity": f"Used AI Screener {stats.get('ai_screener_uses', 0)} times",
                "points": stats.get('ai_screener_uses', 0) * 5
            })
            
        if activities:
            activities_df = pd.DataFrame(activities)
            st.dataframe(activities_df, use_container_width=True, hide_index=True)
        else:
            st.info("No recent activities to display. Start using the app features to earn points!")
        
        # Tips for earning more achievements
        st.subheader("Tips for Earning More Achievements")
        tips = [
            "💰 Add stocks with high dividend yields to earn the Dividend Hunter badge",
            "🔍 Use the AI Stock Screener to discover new investment opportunities",
            "📊 Check sentiment for different stocks to track market opinions",
            "🌎 Add stocks from different countries to earn the Globetrotter badge",
            "📱 Visit the app for 3 consecutive days to earn the Market Regular badge"
        ]
        
        for tip in tips:
            st.markdown(f"- {tip}")
    
    with tab2:
        display_leaderboard()
        
        # Future features
        st.subheader("Coming Soon")
        st.info("""
        💫 **Future Features:**
        - Compare your portfolio performance with other investors
        - Share your achievements on social media
        - Earn special badges for exceptional investment strategies
        - Weekly and monthly investment challenges
        """)

if __name__ == "__main__":
    main()