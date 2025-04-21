import json
import os
from datetime import datetime
import pandas as pd
import yfinance as yf
import streamlit as st
from database import (
    get_favorite_stocks, 
    get_portfolio_holdings, 
    get_search_history,
    add_achievement,
    get_achievements,
    get_user_stats,
    update_user_stats
)

# Define achievement types
ACHIEVEMENTS = {
    "starter": {
        "id": "starter",
        "name": "Portfolio Pioneer",
        "description": "Added your first stock to favorites",
        "icon": "🏁",
        "category": "basics",
        "points": 10
    },
    "diversified": {
        "id": "diversified",
        "name": "Sector Strategist",
        "description": "Added stocks from at least 3 different sectors",
        "icon": "🌈",
        "category": "portfolio",
        "points": 25
    },
    "bull_catcher": {
        "id": "bull_catcher",
        "name": "Bull Catcher",
        "description": "Added a stock with over 80% bullish sentiment",
        "icon": "🐂",
        "category": "sentiment",
        "points": 15
    },
    "bear_tamer": {
        "id": "bear_tamer",
        "name": "Bear Tamer",
        "description": "Added a stock with over 60% bearish sentiment",
        "icon": "🐻",
        "category": "sentiment",
        "points": 20
    },
    "dividend_hunter": {
        "id": "dividend_hunter",
        "name": "Dividend Hunter",
        "description": "Added 3 stocks with dividend yields over 3%",
        "icon": "💰",
        "category": "income",
        "points": 30
    },
    "tech_enthusiast": {
        "id": "tech_enthusiast",
        "name": "Tech Enthusiast",
        "description": "Added 5 technology stocks to your portfolio",
        "icon": "💻",
        "category": "sectors",
        "points": 20
    },
    "value_investor": {
        "id": "value_investor",
        "name": "Value Investor",
        "description": "Added 3 stocks with P/E ratio below market average",
        "icon": "🧮",
        "category": "strategy",
        "points": 25
    },
    "globetrotter": {
        "id": "globetrotter",
        "name": "Investment Globetrotter",
        "description": "Added stocks from 3 different countries",
        "icon": "🌎",
        "category": "global",
        "points": 30
    },
    "night_owl": {
        "id": "night_owl",
        "name": "Night Owl Trader",
        "description": "Used the app after 10 PM",
        "icon": "🦉",
        "category": "usage",
        "points": 10
    },
    "early_bird": {
        "id": "early_bird",
        "name": "Early Bird Investor",
        "description": "Used the app before 7 AM",
        "icon": "🐦",
        "category": "usage",
        "points": 10
    },
    "ai_explorer": {
        "id": "ai_explorer",
        "name": "AI Explorer",
        "description": "Used the AI Screener 5 times",
        "icon": "🤖",
        "category": "tools",
        "points": 20
    },
    "sentiment_analyst": {
        "id": "sentiment_analyst",
        "name": "Sentiment Analyst",
        "description": "Checked sentiment for 10 different stocks",
        "icon": "📊",
        "category": "tools",
        "points": 25
    },
    "portfolio_master": {
        "id": "portfolio_master",
        "name": "Portfolio Master",
        "description": "Added 10 stocks to your portfolio",
        "icon": "🏆",
        "category": "portfolio",
        "points": 30
    },
    "consecutive_login": {
        "id": "consecutive_login",
        "name": "Market Regular",
        "description": "Used the app for 3 consecutive days",
        "icon": "📆",
        "category": "usage",
        "points": 15
    },
    "market_crusher": {
        "id": "market_crusher",
        "name": "Market Crusher",
        "description": "Your portfolio outperformed the S&P 500",
        "icon": "💪",
        "category": "performance",
        "points": 50
    }
}

def initialize_user_stats():
    """Initialize user statistics if not already present"""
    if 'user_stats' not in st.session_state:
        # Try to load from the database first
        db_stats = get_user_stats()
        
        if db_stats:
            st.session_state['user_stats'] = db_stats
        else:
            # Set default stats
            st.session_state['user_stats'] = {
                "total_points": 0,
                "achievements": [],
                "stocks_analyzed": 0,
                "sentiment_checks": 0,
                "ai_screener_uses": 0,
                "stocks_favorited": 0,
                "portfolio_additions": 0,
                "app_opens": 0,
                "consecutive_days": 0,
                "last_visit_date": datetime.now().strftime("%Y-%m-%d"),
                "sectors_in_portfolio": [],
                "highest_sentiment_score": 0,
                "lowest_sentiment_score": 0,
                "search_history_count": 0
            }
            
            # Save to database
            update_user_stats(st.session_state['user_stats'])

def increment_stat(stat_name, increment=1):
    """Increment a user statistic"""
    initialize_user_stats()
    
    if stat_name in st.session_state['user_stats']:
        st.session_state['user_stats'][stat_name] += increment
    
    # Save to database
    update_user_stats(st.session_state['user_stats'])

def set_stat(stat_name, value):
    """Set a user statistic to a specific value"""
    initialize_user_stats()
    
    st.session_state['user_stats'][stat_name] = value
    
    # Save to database
    update_user_stats(st.session_state['user_stats'])

def update_visit_streak():
    """Update the consecutive days visit streak"""
    initialize_user_stats()
    
    # Get the last visit date
    last_visit = st.session_state['user_stats']['last_visit_date']
    today = datetime.now().strftime("%Y-%m-%d")
    
    # If it's a different day than the last visit
    if last_visit != today:
        last_date = datetime.strptime(last_visit, "%Y-%m-%d")
        current_date = datetime.strptime(today, "%Y-%m-%d")
        
        # Calculate the difference in days
        day_diff = (current_date - last_date).days
        
        # If consecutive (1 day difference)
        if day_diff == 1:
            st.session_state['user_stats']['consecutive_days'] += 1
        # If more than 1 day, reset streak
        elif day_diff > 1:
            st.session_state['user_stats']['consecutive_days'] = 1
        
        # Update last visit date
        st.session_state['user_stats']['last_visit_date'] = today
        
        # Increment app opens
        st.session_state['user_stats']['app_opens'] += 1
        
        # Save to database
        update_user_stats(st.session_state['user_stats'])

def check_achievements():
    """Check for achievements that should be awarded"""
    initialize_user_stats()
    
    # Get current stats
    stats = st.session_state['user_stats']
    
    # Get current achievements
    current_achievements = stats.get('achievements', [])
    
    # Track if any new achievements were earned
    new_achievements = []
    
    # Check for each achievement
    # Starter achievement
    if stats['stocks_favorited'] > 0 and "starter" not in current_achievements:
        new_achievements.append("starter")
    
    # AI Explorer achievement
    if stats['ai_screener_uses'] >= 5 and "ai_explorer" not in current_achievements:
        new_achievements.append("ai_explorer")
    
    # Sentiment Analyst achievement
    if stats['sentiment_checks'] >= 10 and "sentiment_analyst" not in current_achievements:
        new_achievements.append("sentiment_analyst")
    
    # Portfolio Master achievement
    if stats['portfolio_additions'] >= 10 and "portfolio_master" not in current_achievements:
        new_achievements.append("portfolio_master")
    
    # Consecutive Login achievement
    if stats['consecutive_days'] >= 3 and "consecutive_login" not in current_achievements:
        new_achievements.append("consecutive_login")
    
    # Night Owl achievement
    current_hour = datetime.now().hour
    if current_hour >= 22 and "night_owl" not in current_achievements:
        new_achievements.append("night_owl")
    
    # Early Bird achievement
    if current_hour < 7 and "early_bird" not in current_achievements:
        new_achievements.append("early_bird")
    
    # Add achievements to user stats
    for achievement_id in new_achievements:
        # Add to stats
        stats['achievements'].append(achievement_id)
        
        # Add points
        stats['total_points'] += ACHIEVEMENTS[achievement_id]['points']
        
        # Add to database
        add_achievement(achievement_id)
    
    # Save updated stats
    if new_achievements:
        update_user_stats(stats)
    
    return new_achievements

def check_sector_achievements():
    """Check for sector-based achievements"""
    initialize_user_stats()
    
    # Get current stats
    stats = st.session_state['user_stats']
    
    # Get current achievements
    current_achievements = stats.get('achievements', [])
    
    # Get portfolio holdings
    holdings = get_portfolio_holdings()
    
    if not holdings:
        return []
    
    # Track sectors
    sectors = set()
    
    # Track stock attributes for achievements
    tech_stocks = 0
    dividend_stocks = 0
    low_pe_stocks = 0
    countries = set()
    
    # Process each holding
    for holding in holdings:
        # Extract sector
        sector = holding.get('sector', '').strip()
        if sector and sector != 'Unknown':
            sectors.add(sector)
            
            # Check for tech sector
            if sector.lower() in ['technology', 'information technology', 'tech']:
                tech_stocks += 1
        
        # Get additional info from yfinance
        try:
            ticker = holding.get('ticker')
            if ticker:
                stock_info = yf.Ticker(ticker).info
                
                # Check dividend yield
                dividend_yield = stock_info.get('dividendYield', 0)
                if dividend_yield and dividend_yield > 0.03:  # Over 3%
                    dividend_stocks += 1
                
                # Check P/E ratio
                pe_ratio = stock_info.get('trailingPE', 0)
                if pe_ratio and pe_ratio < 15:  # Below market average
                    low_pe_stocks += 1
                
                # Check country
                country = stock_info.get('country', '')
                if country.strip():
                    countries.add(country)
        except:
            continue
    
    # Update sectors in stats
    stats['sectors_in_portfolio'] = list(sectors)
    
    # Track new achievements
    new_achievements = []
    
    # Check for sector diversification
    if len(sectors) >= 3 and "diversified" not in current_achievements:
        new_achievements.append("diversified")
    
    # Check for tech enthusiast
    if tech_stocks >= 5 and "tech_enthusiast" not in current_achievements:
        new_achievements.append("tech_enthusiast")
    
    # Check for dividend hunter
    if dividend_stocks >= 3 and "dividend_hunter" not in current_achievements:
        new_achievements.append("dividend_hunter")
    
    # Check for value investor
    if low_pe_stocks >= 3 and "value_investor" not in current_achievements:
        new_achievements.append("value_investor")
    
    # Check for globetrotter
    if len(countries) >= 3 and "globetrotter" not in current_achievements:
        new_achievements.append("globetrotter")
    
    # Add achievements to user stats
    for achievement_id in new_achievements:
        # Add to stats
        stats['achievements'].append(achievement_id)
        
        # Add points
        stats['total_points'] += ACHIEVEMENTS[achievement_id]['points']
        
        # Add to database
        add_achievement(achievement_id)
    
    # Save updated stats
    if new_achievements:
        update_user_stats(stats)
    
    return new_achievements

def check_sentiment_achievements(sentiment_score, sentiment_type):
    """Check for sentiment-based achievements"""
    initialize_user_stats()
    
    # Get current stats
    stats = st.session_state['user_stats']
    
    # Get current achievements
    current_achievements = stats.get('achievements', [])
    
    # Track new achievements
    new_achievements = []
    
    # Update highest/lowest sentiment scores
    sentiment_value = float(sentiment_score)
    if sentiment_value > stats['highest_sentiment_score']:
        stats['highest_sentiment_score'] = sentiment_value
    
    if stats['lowest_sentiment_score'] == 0 or sentiment_value < stats['lowest_sentiment_score']:
        stats['lowest_sentiment_score'] = sentiment_value
    
    # Bull Catcher achievement
    if sentiment_type == 'bullish' and sentiment_value >= 0.8 and "bull_catcher" not in current_achievements:
        new_achievements.append("bull_catcher")
    
    # Bear Tamer achievement
    if sentiment_type == 'bearish' and sentiment_value <= 0.4 and "bear_tamer" not in current_achievements:
        new_achievements.append("bear_tamer")
    
    # Add achievements to user stats
    for achievement_id in new_achievements:
        # Add to stats
        stats['achievements'].append(achievement_id)
        
        # Add points
        stats['total_points'] += ACHIEVEMENTS[achievement_id]['points']
        
        # Add to database
        add_achievement(achievement_id)
    
    # Save updated stats
    if new_achievements:
        update_user_stats(stats)
    
    return new_achievements

def check_portfolio_performance():
    """Check if portfolio outperforms the S&P 500"""
    initialize_user_stats()
    
    # Get current stats
    stats = st.session_state['user_stats']
    
    # Get current achievements
    current_achievements = stats.get('achievements', [])
    
    # Get portfolio holdings
    holdings = get_portfolio_holdings()
    
    if not holdings:
        return []
    
    # Get portfolio returns
    portfolio_return = calculate_portfolio_return(holdings)
    
    # Get S&P 500 returns over same period (past month)
    spy_return = calculate_spy_return()
    
    # Check if portfolio outperformed
    if portfolio_return > spy_return and portfolio_return > 0 and "market_crusher" not in current_achievements:
        # Add achievement
        stats['achievements'].append("market_crusher")
        
        # Add points
        stats['total_points'] += ACHIEVEMENTS["market_crusher"]['points']
        
        # Add to database
        add_achievement("market_crusher")
        
        # Save updated stats
        update_user_stats(stats)
        
        return ["market_crusher"]
    
    return []

def calculate_portfolio_return(holdings):
    """Calculate the overall return of the portfolio"""
    if not holdings:
        return 0
    
    total_value = 0
    total_cost = 0
    
    for holding in holdings:
        shares = holding.get('shares', 0)
        current_price = holding.get('current_price', 0)
        purchase_price = holding.get('purchase_price', 0)
        
        if shares and current_price and purchase_price:
            total_value += shares * current_price
            total_cost += shares * purchase_price
    
    if total_cost == 0:
        return 0
    
    return (total_value - total_cost) / total_cost * 100

def calculate_spy_return():
    """Calculate the return of S&P 500 over past month"""
    try:
        # Get SPY data
        spy = yf.Ticker("SPY")
        hist = spy.history(period="1mo")
        
        if hist.empty:
            return 0
        
        # Calculate return
        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        
        return (end_price - start_price) / start_price * 100
    except:
        return 0

def track_stock_analysis(ticker):
    """Track when a stock is analyzed"""
    increment_stat('stocks_analyzed')
    
    # Check for achievements
    check_achievements()

def track_sentiment_check(ticker):
    """Track when sentiment is checked for a stock"""
    increment_stat('sentiment_checks')
    
    # Check for achievements
    check_achievements()

def track_ai_screener_use():
    """Track when the AI screener is used"""
    increment_stat('ai_screener_uses')
    
    # Check for achievements
    check_achievements()

def track_favorite_added():
    """Track when a stock is added to favorites"""
    increment_stat('stocks_favorited')
    
    # Check for achievements
    check_achievements()

def track_portfolio_addition():
    """Track when a stock is added to portfolio"""
    increment_stat('portfolio_additions')
    
    # Check for sector achievements
    check_sector_achievements()
    
    # Check for achievements
    check_achievements()

def get_leaderboard():
    """
    In a more advanced version with multiple users, this would return 
    the top users by points. For now, we'll just return the current user.
    """
    initialize_user_stats()
    
    # Get current stats
    stats = st.session_state['user_stats']
    
    # Create a leaderboard entry for the current user
    leaderboard = [{
        "rank": 1,
        "username": "You",
        "points": stats['total_points'],
        "achievements": len(stats['achievements']),
        "is_current_user": True
    }]
    
    # In a multi-user system, we would add more entries here
    
    return leaderboard

def display_achievements_section():
    """Display the achievements section in the app"""
    st.subheader("🏆 Your Achievements")
    
    # Initialize stats if needed
    initialize_user_stats()
    
    # Get current stats
    stats = st.session_state['user_stats']
    
    # Get earned achievements
    earned_achievements = stats.get('achievements', [])
    
    # Display points
    st.markdown(f"### Total Score: {stats['total_points']} points")
    
    # Show user stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Stocks Analyzed", stats['stocks_analyzed'])
        st.metric("AI Screener Uses", stats['ai_screener_uses'])
    
    with col2:
        st.metric("Sentiment Checks", stats['sentiment_checks'])
        st.metric("Stocks in Portfolio", stats['portfolio_additions'])
    
    with col3:
        st.metric("Consecutive Days", stats['consecutive_days'])
        st.metric("Achievements Earned", len(earned_achievements))
    
    # Display earned achievements
    st.write("### Earned Badges")
    
    if not earned_achievements:
        st.info("You haven't earned any achievements yet. Keep using the app to unlock badges!")
    else:
        # Create a grid of achievements
        achievement_cols = st.columns(3)
        
        for i, achievement_id in enumerate(earned_achievements):
            achievement = ACHIEVEMENTS.get(achievement_id)
            if achievement:
                with achievement_cols[i % 3]:
                    st.markdown(f"""
                    <div style="
                        background-color: #f0f2f6;
                        border-radius: 10px;
                        padding: 10px;
                        margin-bottom: 10px;
                        text-align: center;
                    ">
                        <h1 style="font-size: 2em; margin: 0;">{achievement['icon']}</h1>
                        <h3>{achievement['name']}</h3>
                        <p>{achievement['description']}</p>
                        <p><strong>+{achievement['points']} points</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Display available achievements
    with st.expander("Available Achievements"):
        # Create a grid of achievements
        available_cols = st.columns(3)
        
        i = 0
        for achievement_id, achievement in ACHIEVEMENTS.items():
            if achievement_id not in earned_achievements:
                with available_cols[i % 3]:
                    st.markdown(f"""
                    <div style="
                        background-color: #e6e6e6;
                        border-radius: 10px;
                        padding: 10px;
                        margin-bottom: 10px;
                        text-align: center;
                        opacity: 0.7;
                    ">
                        <h1 style="font-size: 2em; margin: 0;">{achievement['icon']}</h1>
                        <h3 style="color: #666;">{achievement['name']}</h3>
                        <p>{achievement['description']}</p>
                        <p><strong>+{achievement['points']} points</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                    i += 1

def display_leaderboard():
    """Display the leaderboard"""
    st.subheader("🥇 Leaderboard")
    
    leaderboard = get_leaderboard()
    
    # Create a DataFrame for the leaderboard
    leaderboard_df = pd.DataFrame(leaderboard)
    
    # Format for display
    formatted_df = leaderboard_df.copy()
    formatted_df['rank'] = formatted_df['rank'].astype(str)
    formatted_df.columns = ['Rank', 'Username', 'Points', 'Achievements', 'Is You']
    
    # Display the leaderboard
    st.dataframe(formatted_df[['Rank', 'Username', 'Points', 'Achievements']], use_container_width=True)
    
    st.info("Earn more points by using the app features and earning achievements!")

def show_achievement_notification(achievement_ids):
    """Show a notification for new achievements"""
    if not achievement_ids:
        return
    
    # Create notification for each achievement
    for achievement_id in achievement_ids:
        achievement = ACHIEVEMENTS.get(achievement_id)
        if achievement:
            st.balloons()
            st.success(f"""
            ## 🎉 New Achievement Unlocked! 
            
            {achievement['icon']} **{achievement['name']}**  
            {achievement['description']}
            
            **+{achievement['points']} points!**
            """)

def initialize_gamification():
    """Initialize the gamification system when the app starts"""
    # Initialize user stats
    initialize_user_stats()
    
    # Update visit streak
    update_visit_streak()
    
    # Check for achievements
    check_achievements()