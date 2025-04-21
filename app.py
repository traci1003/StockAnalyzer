import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from utils import calculate_moving_averages, calculate_rsi, calculate_bollinger_bands, calculate_macd
import database as db
from gamification import initialize_gamification, track_stock_analysis, track_favorite_added
from monetization import get_user_plan, PREMIUM_PLANS
import theme_manager

# Set page configuration
st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
    menu_items={
        'Get Help': 'https://www.streamlit.io/community',
        'Report a bug': None,
        'About': "A comprehensive financial dashboard for analyzing stock data and visualizing investment trends."
    }
)

# Initialize session state for price alerts
if 'last_alert_check' not in st.session_state:
    st.session_state.last_alert_check = None
if 'triggered_alerts' not in st.session_state:
    st.session_state.triggered_alerts = []

# Function to check price alerts
def check_price_alerts_background():
    # Get all pending alerts
    pending_alerts = db.get_pending_alerts()
    
    if not pending_alerts:
        return []
    
    # Get unique tickers to check
    tickers = set([alert['ticker'] for alert in pending_alerts])
    
    # Fetch current prices
    current_prices = {}
    triggered_alerts = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            current_prices[ticker] = current_price
        except Exception as e:
            # Skip this ticker on error
            continue
    
    # Check each alert against current price
    for alert in pending_alerts:
        ticker = alert['ticker']
        if ticker not in current_prices:
            continue
            
        current_price = current_prices[ticker]
        target_price = alert['target_price']
        is_above = alert['is_above'] == 1
        
        # Check if the alert is triggered
        if (is_above and current_price >= target_price) or (not is_above and current_price <= target_price):
            # Mark as triggered in the database
            db.mark_alert_triggered(alert['id'])
            
            # Add to triggered list
            alert_dict = dict(alert)
            alert_dict['current_price'] = current_price
            triggered_alerts.append(alert_dict)
    
    return triggered_alerts

# Check for triggered alerts (every 10 minutes max)
current_time = datetime.now()
if st.session_state.last_alert_check is None or \
   (current_time - st.session_state.last_alert_check).total_seconds() > 600:  # 10 minutes
    st.session_state.triggered_alerts = check_price_alerts_background()
    st.session_state.last_alert_check = current_time

# Initialize theme system
theme_manager.check_theme_preference()
theme_manager.display_custom_css()

# Initialize gamification system
initialize_gamification()

# App title and description
st.title("📊 Stock Market Dashboard")
st.markdown("A comprehensive financial dashboard for analyzing stock data and visualizing investment trends.")

# Show alert notifications if any
if st.session_state.triggered_alerts:
    with st.expander("🔔 Price Alerts Triggered!", expanded=True):
        for alert in st.session_state.triggered_alerts:
            direction = "above" if alert['is_above'] == 1 else "below"
            st.success(f"Alert: {alert['ticker']} is now ${alert['current_price']:.2f}, {direction} your target of ${alert['target_price']:.2f}")
        if st.button("Dismiss Alerts"):
            st.session_state.triggered_alerts = []

# Create navigation links to other pages
st.markdown("""
<style>
.nav-link {
    background-color: #4CAF50;
    color: white;
    padding: 10px 15px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 4px;
}
.nav-link-ai {
    background-color: #2196F3;
    color: white;
    padding: 10px 15px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 4px;
}
.nav-link-alert {
    background-color: #FF9800;
    color: white;
    padding: 10px 15px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 4px;
}
.nav-link-achievement {
    background-color: #9C27B0;
    color: white;
    padding: 10px 15px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 4px;
}
.nav-container {
    display: flex;
    gap: 10px;
}
</style>
<div class="nav-container">
    <a href="/portfolio_tracker" target="_self" class="nav-link">💼 Go to Portfolio Tracker</a>
    <a href="/ai_advisor" target="_self" class="nav-link-ai">🤖 AI Investment Advisor</a>
    <a href="/price_alerts" target="_self" class="nav-link-alert">🔔 Price Alerts</a>
    <a href="/achievements" target="_self" class="nav-link-achievement">🏆 Achievements</a>
    <a href="/premium" target="_self" style="background-color: #FFD700; color: black; padding: 10px 15px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 4px;">⭐ Premium</a>
</div>
""", unsafe_allow_html=True)

# Initialize session state for favorites if not present
if 'last_ticker' not in st.session_state:
    st.session_state.last_ticker = None

# Initialize ticker (default to Google - GOOGL)
default_ticker = "GOOGL"

# Get favorites from database
favorites = db.get_favorite_stocks()
favorite_options = [""] + [fav['ticker'] for fav in favorites]
favorite_labels = ["Select from favorites..."] + [f"{fav['company_name']} ({fav['ticker']})" for fav in favorites]

# Get search history
search_history = db.get_search_history(limit=5)
recent_searches = [""] + [hist['ticker'] for hist in search_history]
recent_searches_labels = ["Recent searches..."] + [f"{hist['ticker']} ({hist['count']} times)" for hist in search_history]

# User input section
col_search, col_fav, col_history = st.sidebar.columns([2, 1, 1])

with col_search:
    ticker = st.text_input("Enter Stock Symbol", default_ticker).upper()

# Favorites dropdown
selected_favorite = st.sidebar.selectbox(
    "Favorites", 
    options=favorite_options,
    format_func=lambda x: next((fav_label for fav_opt, fav_label in zip(favorite_options, favorite_labels) if fav_opt == x), x),
    index=0
)

if selected_favorite:
    ticker = selected_favorite
    
# Recent searches dropdown
selected_recent = st.sidebar.selectbox(
    "Recent Searches", 
    options=recent_searches,
    format_func=lambda x: next((hist_label for hist_opt, hist_label in zip(recent_searches, recent_searches_labels) if hist_opt == x), x),
    index=0
)

if selected_recent:
    ticker = selected_recent

if not ticker:
    ticker = default_ticker

# Save search to history if ticker changed
if st.session_state.last_ticker != ticker:
    db.add_search_history(ticker)
    track_stock_analysis(ticker)
    st.session_state.last_ticker = ticker

try:
    # Verify the ticker exists
    ticker_data = yf.Ticker(ticker)
    info = ticker_data.info
    company_name = info.get('shortName', ticker)
    
    # Check if the stock is in favorites
    is_favorite = db.is_favorite_stock(ticker)
    
    # Create a row with the heading and action buttons
    heading_col, fav_button_col, alert_button_col = st.columns([4, 1, 1])
    
    with heading_col:
        st.subheader(f"Currently viewing: {company_name} ({ticker})")
    
    with fav_button_col:
        if is_favorite:
            if st.button("❤️ Remove from Favorites"):
                db.remove_favorite_stock(ticker)
                st.rerun()
        else:
            if st.button("🤍 Add to Favorites"):
                db.add_favorite_stock(ticker, company_name)
                track_favorite_added()
                st.rerun()
    
    with alert_button_col:
        if st.button("🔔 Set Alert"):
            # Store ticker in session state for the price alerts page
            if 'alert_ticker' not in st.session_state:
                st.session_state.alert_ticker = ticker
                st.session_state.alert_company = company_name
            st.switch_page("pages/price_alerts.py")
except:
    st.error(f"Could not find data for ticker '{ticker}'. Defaulting to {default_ticker}.")
    ticker = default_ticker
    ticker_data = yf.Ticker(ticker)
    info = ticker_data.info
    company_name = info.get('shortName', ticker)
    
    # Check if the stock is in favorites
    is_favorite = db.is_favorite_stock(ticker)
    
    # Create a row with the heading and action buttons
    heading_col, fav_button_col, alert_button_col = st.columns([4, 1, 1])
    
    with heading_col:
        st.subheader(f"Currently viewing: {company_name} ({ticker})")
    
    with fav_button_col:
        if is_favorite:
            if st.button("❤️ Remove from Favorites", key="remove_fav_default"):
                db.remove_favorite_stock(ticker)
                st.rerun()
        else:
            if st.button("🤍 Add to Favorites", key="add_fav_default"):
                db.add_favorite_stock(ticker, company_name)
                track_favorite_added()
                st.rerun()
                
    with alert_button_col:
        if st.button("🔔 Set Alert", key="set_alert_default"):
            # Store ticker in session state for the price alerts page
            if 'alert_ticker' not in st.session_state:
                st.session_state.alert_ticker = ticker
                st.session_state.alert_company = company_name
            st.switch_page("pages/price_alerts.py")

# Main dashboard layout - using columns
col1, col2 = st.columns([1, 2])

# Sidebar for date range selection
st.sidebar.title("Dashboard Controls")

# Display Premium Status badge
current_plan = get_user_plan()
plan_info = PREMIUM_PLANS.get(current_plan, PREMIUM_PLANS["free"])

# Create premium status badge with styling based on plan color
if current_plan != "free":
    st.sidebar.markdown(f"""
    <div style="
        background-color: {plan_info['color']}; 
        color: white; 
        padding: 8px 12px; 
        border-radius: 8px;
        text-align: center;
        margin: 10px 0;
        font-weight: bold;
        position: relative;
        cursor: help;
    " title="You're a Premium {plan_info['name']} member! Enjoy exclusive features across the platform.">
        ⭐ PREMIUM {plan_info['name'].upper()}
    </div>
    <div style="text-align: right; margin-bottom: 15px;">
        <a href="/premium" style="text-decoration: none; color: {plan_info['color']}; font-size: 12px;">
            Manage Account →
        </a>
    </div>
    
    <style>
    /* Add subtle glow effect to the premium badge */
    div[title*="Premium"] {{
        box-shadow: 0 0 8px 1px {plan_info['color']}40;
        transition: box-shadow 0.3s ease;
    }}
    div[title*="Premium"]:hover {{
        box-shadow: 0 0 12px 3px {plan_info['color']}60;
    }}
    </style>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
    <div style="
        background-color: #9E9E9E; 
        color: white; 
        padding: 8px 12px; 
        border-radius: 8px;
        text-align: center;
        margin: 10px 0;
        cursor: help;
    " title="You're using a free account with limited features. Upgrade to unlock premium analytics!">
        FREE ACCOUNT
    </div>
    <div style="text-align: right; margin-bottom: 15px;">
        <a href="/premium" style="text-decoration: none; color: #FFD700; font-weight: bold; font-size: 12px;">
            ⭐ Upgrade to Premium →
        </a>
    </div>
    <div style="text-align: center; margin-bottom: 15px; font-size: 12px; color: #666;">
        <a href="/premium?trial=true" style="text-decoration: none; color: #666;">
            Try Premium free for 24 hours
        </a>
    </div>
    """, unsafe_allow_html=True)

# Theme options
theme_manager.display_theme_options()

# Set plot template based on current theme
current_theme = theme_manager.get_current_theme()
plot_template = "plotly_white" if current_theme in ["light", "premium_gold"] else "plotly_dark"

# Date range selection
end_date = datetime.now()
start_date = end_date - timedelta(days=365)  # Default to 1 year

date_options = {
    "1 Week": end_date - timedelta(days=7),
    "1 Month": end_date - timedelta(days=30),
    "3 Months": end_date - timedelta(days=90),
    "6 Months": end_date - timedelta(days=180),
    "1 Year": end_date - timedelta(days=365),
    "5 Years": end_date - timedelta(days=1825),
    "Custom": None
}

selected_range = st.sidebar.selectbox("Select Date Range", list(date_options.keys()))

if selected_range == "Custom":
    col1_date, col2_date = st.sidebar.columns(2)
    with col1_date:
        custom_start = st.date_input("Start Date", value=end_date - timedelta(days=180))
    with col2_date:
        custom_end = st.date_input("End Date", value=end_date)
    
    if custom_start >= custom_end:
        st.sidebar.error("Start date must be before end date")
        custom_start = custom_end - timedelta(days=30)
    
    start_date = custom_start
    end_date = custom_end
else:
    start_date = date_options[selected_range]

# Import additional monetization features
from monetization import is_feature_available, display_feature_teaser

# Technical indicator selection
st.sidebar.title("Technical Indicators")
show_ma = st.sidebar.checkbox("Moving Averages", value=True)
show_rsi = st.sidebar.checkbox("Relative Strength Index (RSI)", value=False)
show_bollinger = st.sidebar.checkbox("Bollinger Bands", value=False)
show_macd = st.sidebar.checkbox("MACD", value=False)

# Advanced indicators - premium feature
advanced_indicators_available = is_feature_available('advanced_technical')
if not advanced_indicators_available:
    st.sidebar.markdown("---")
    display_feature_teaser('advanced_technical')

# User preferences and history management section
st.sidebar.title("Favorites & History")
if st.sidebar.button("Clear Search History"):
    db.clear_search_history()
    st.sidebar.success("Search history cleared!")
    st.rerun()

# Display the number of favorites
favorites_count = len(db.get_favorite_stocks())
st.sidebar.markdown(f"**Saved Favorites:** {favorites_count} stocks")

# Display the number of recent searches
searches_count = len(db.get_search_history())
st.sidebar.markdown(f"**Recent Searches:** {searches_count} items")

# Get stock data
try:
    # Current stock info
    info = ticker_data.info
    
    # Historical data
    hist_data = ticker_data.history(start=start_date, end=end_date)
    
    if hist_data.empty:
        st.error(f"No data available for {ticker} in the selected date range.")
    else:
        # COLUMN 1: Financial Snapshot
        with col1:
            st.subheader("Financial Snapshot")
            
            # Current price and daily change
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            previous_close = info.get('previousClose', 0)
            price_change = current_price - previous_close
            price_change_percent = (price_change / previous_close) * 100 if previous_close else 0
            
            # Change color based on price movement
            price_color = "green" if price_change >= 0 else "red"
            change_icon = "▲" if price_change >= 0 else "▼"
            
            # Display current price with styling
            st.markdown(f"### ${current_price:.2f}")
            st.markdown(f"<span style='color:{price_color}'>{change_icon} ${abs(price_change):.2f} ({price_change_percent:.2f}%)</span>", unsafe_allow_html=True)
            
            # Create metrics table
            metrics_data = {
                "Metric": [
                    "Market Cap", "P/E Ratio", "EPS (TTM)", 
                    "52-Week High", "52-Week Low", "Dividend Yield",
                    "Volume", "Avg Volume"
                ],
                "Value": [
                    f"${info.get('marketCap', 0) / 1_000_000_000:.2f}B",
                    f"{info.get('trailingPE', 0):.2f}",
                    f"${info.get('trailingEps', 0):.2f}",
                    f"${info.get('fiftyTwoWeekHigh', 0):.2f}",
                    f"${info.get('fiftyTwoWeekLow', 0):.2f}",
                    f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "N/A",
                    f"{info.get('volume', 0):,}",
                    f"{info.get('averageVolume', 0):,}"
                ]
            }
            
            metrics_df = pd.DataFrame(metrics_data)
            st.table(metrics_df)
            
            # Company info
            st.subheader("Company Info")
            st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
            st.markdown(f"**Industry:** {info.get('industry', 'N/A')}")
            
            # Business summary (collapsible)
            with st.expander("Business Summary"):
                st.write(info.get('longBusinessSummary', 'No information available.'))
        
        # COLUMN 2: Stock Price Chart
        with col2:
            st.subheader(f"{ticker} Stock Price Chart ({selected_range})")
            
            # Prepare data for chart
            fig = go.Figure()
            
            # Candlestick chart
            fig.add_trace(go.Candlestick(
                x=hist_data.index,
                open=hist_data['Open'],
                high=hist_data['High'],
                low=hist_data['Low'],
                close=hist_data['Close'],
                name='OHLC'
            ))
            
            # Add technical indicators if selected
            if show_ma:
                ma_data = calculate_moving_averages(hist_data)
                fig.add_trace(go.Scatter(x=ma_data.index, y=ma_data['MA20'], mode='lines', name='20-Day MA', line=dict(color='blue')))
                fig.add_trace(go.Scatter(x=ma_data.index, y=ma_data['MA50'], mode='lines', name='50-Day MA', line=dict(color='orange')))
                fig.add_trace(go.Scatter(x=ma_data.index, y=ma_data['MA200'], mode='lines', name='200-Day MA', line=dict(color='red')))
            
            if show_bollinger:
                bb_data = calculate_bollinger_bands(hist_data)
                fig.add_trace(go.Scatter(x=bb_data.index, y=bb_data['upper_band'], mode='lines', name='Upper BB', line=dict(color='gray', width=1)))
                fig.add_trace(go.Scatter(x=bb_data.index, y=bb_data['lower_band'], mode='lines', name='Lower BB', line=dict(color='gray', width=1)))
                fig.add_trace(go.Scatter(x=bb_data.index, y=bb_data['middle_band'], mode='lines', name='Middle BB', line=dict(color='purple', width=1)))
            
            # Update layout
            fig.update_layout(
                title=f"{ticker} Stock Price",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                height=600,
                xaxis_rangeslider_visible=True,
                template=plot_template
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # RSI chart (if selected)
            if show_rsi:
                rsi_data = calculate_rsi(hist_data)
                
                fig_rsi = px.line(rsi_data, x=rsi_data.index, y='RSI', title='Relative Strength Index (RSI)')
                
                # Add RSI reference lines
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
                
                fig_rsi.update_layout(
                    xaxis_title="Date",
                    yaxis_title="RSI",
                    height=300,
                    template=plot_template
                )
                
                st.plotly_chart(fig_rsi, use_container_width=True)
                
            # MACD chart (if selected)
            if show_macd:
                macd_data = calculate_macd(hist_data)
                
                # Create MACD plot
                fig_macd = go.Figure()
                
                # Add MACD line
                fig_macd.add_trace(go.Scatter(
                    x=macd_data.index, 
                    y=macd_data['macd'],
                    mode='lines',
                    name='MACD',
                    line=dict(color='blue', width=1.5)
                ))
                
                # Add signal line
                fig_macd.add_trace(go.Scatter(
                    x=macd_data.index, 
                    y=macd_data['signal'],
                    mode='lines',
                    name='Signal',
                    line=dict(color='red', width=1.5)
                ))
                
                # Add histogram as a bar chart
                colors = ['green' if val >= 0 else 'red' for val in macd_data['histogram']]
                fig_macd.add_trace(go.Bar(
                    x=macd_data.index,
                    y=macd_data['histogram'],
                    name='Histogram',
                    marker_color=colors
                ))
                
                # Update layout
                fig_macd.update_layout(
                    title='MACD (Moving Average Convergence Divergence)',
                    xaxis_title='Date',
                    yaxis_title='Value',
                    height=300,
                    template=plot_template,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig_macd, use_container_width=True)
        
        # Volume chart (below main charts)
        st.subheader("Trading Volume")
        
        # Create volume chart
        fig_volume = px.bar(
            hist_data,
            x=hist_data.index,
            y='Volume',
            title=f"{ticker} Trading Volume",
            color_discrete_sequence=['rgba(0, 128, 255, 0.7)']
        )
        
        fig_volume.update_layout(
            xaxis_title="Date",
            yaxis_title="Volume",
            height=300,
            template=plot_template
        )
        
        st.plotly_chart(fig_volume, use_container_width=True)
        
        # Historical data and download
        st.subheader("Historical Data")
        
        # Only show last rows of the data
        st.dataframe(hist_data.tail(10))
        
        # Download link for historical data
        csv = hist_data.to_csv().encode('utf-8')
        st.download_button(
            label="Download Historical Data (CSV)",
            data=csv,
            file_name=f'{ticker}_historical_data.csv',
            mime='text/csv',
        )
        
        # News section
        st.subheader(f"Latest News for {company_name}")
        
        try:
            # Get news for the ticker
            news = ticker_data.news
            
            if news:
                # Display up to 5 latest news items
                for i, news_item in enumerate(news[:5]):
                    # Format the date
                    try:
                        news_date = datetime.fromtimestamp(news_item['providerPublishTime']).strftime('%Y-%m-%d %H:%M')
                    except:
                        news_date = "N/A"
                    
                    # Create expandable news items
                    with st.expander(f"{news_item.get('title', 'No Title')} ({news_date})"):
                        st.write(news_item.get('summary', 'No summary available.'))
                        
                        # Add link to full article
                        if 'link' in news_item:
                            st.markdown(f"[Read full article]({news_item['link']})")
            else:
                st.info(f"No recent news available for {ticker}")
        except Exception as e:
            st.warning(f"Unable to fetch news: {e}")
            
        # Analyst Recommendations
        st.subheader("Analyst Recommendations")
        
        try:
            # Try to get recommendations data
            recommendations = ticker_data.recommendations
            
            if recommendations is not None and not recommendations.empty:
                # Display most recent recommendations
                st.dataframe(recommendations.tail(5))
            else:
                st.info(f"No analyst recommendations available for {ticker}")
        except Exception as e:
            st.warning(f"Unable to fetch analyst recommendations: {e}")
        
        # Market comparison
        st.subheader("Market Comparison")
        
        # Get comparative data (S&P 500, NASDAQ)
        comparison_tickers = [ticker, "^GSPC", "^IXIC"]  # Current ticker, S&P 500, NASDAQ
        comparison_names = [company_name, "S&P 500", "NASDAQ"]
        
        # Download data
        comparison_data = {}
        normalized_df = pd.DataFrame()  # Initialize empty DataFrame
        valid_datasets = 0
        
        try:
            # First verify S&P 500 data separately to confirm API is working
            try:
                sp500_check = yf.download("^GSPC", period="1mo", progress=False)
                if sp500_check.empty:
                    st.warning("⚠️ S&P 500 data could not be loaded. Market comparison might not work properly.")
            except Exception as e:
                st.warning(f"⚠️ Market data API check failed: {e}")
            
            # Loop through each ticker and try to get data
            for i, comp_ticker in enumerate(comparison_tickers):
                try:
                    # Download data with explicit date range to ensure proper index
                    comp_data = yf.download(comp_ticker, start=start_date, end=end_date, progress=False)
                    
                    # Verify we have data and it contains the Close column
                    if not comp_data.empty and 'Close' in comp_data.columns and len(comp_data) > 5:
                        # Store the closing prices with the proper name
                        comparison_data[comparison_names[i]] = comp_data['Close']
                        valid_datasets += 1
                except Exception as e:
                    st.warning(f"Could not fetch data for {comp_ticker}: {str(e)}")
            
            # Check if we have at least 2 valid datasets for comparison (need at least 2 to compare)
            if valid_datasets < 2:
                st.error("⚠️ Not enough valid datasets for comparison. Need at least 2 tickers with data.")
            else:
                # We have enough data to proceed with comparison
                try:
                    # Create the DataFrame with explicit index handling
                    comp_df = pd.DataFrame(comparison_data)
                    
                    # Handle missing values properly (check data isn't empty first)
                    if not comp_df.empty:
                        
                        # Drop rows where all values are missing
                        comp_df = comp_df.dropna(how='all')
                        
                        # Forward fill to handle different trading days
                        comp_df = comp_df.fillna(method='ffill')
                        
                        # Normalize data only if we have enough clean data
                        if len(comp_df) > 5:
                            # Get the first day with data for all columns
                            first_valid_idx = comp_df.first_valid_index()
                            
                            if first_valid_idx is not None:
                                # Normalize with explicit handling for each column
                                normalized_data = {}
                                
                                for column in comp_df.columns:
                                    # Get the first valid value for this column
                                    first_val = comp_df.loc[first_valid_idx, column]
                                    if pd.notna(first_val) and first_val != 0:  # Avoid division by zero
                                        # Create normalized column with proper index
                                        normalized_data[column] = (comp_df[column] / first_val) * 100
                                
                                # Create normalized DataFrame with same index as original
                                if normalized_data:
                                    normalized_df = pd.DataFrame(normalized_data, index=comp_df.index)
                                    
                                    # Create the comparison chart
                                    if not normalized_df.empty and normalized_df.shape[1] >= 2:
                                        # Create the chart with proper handling of datetime index
                                        fig_comp = go.Figure()
                                        
                                        # Add a trace for each ticker
                                        for column in normalized_df.columns:
                                            fig_comp.add_trace(
                                                go.Scatter(
                                                    x=normalized_df.index,
                                                    y=normalized_df[column], 
                                                    mode='lines',
                                                    name=column
                                                )
                                            )
                                        
                                        # Update layout with clear title and labels
                                        fig_comp.update_layout(
                                            title="Relative Performance Comparison (Normalized at 100)",
                                            xaxis_title="Date",
                                            yaxis_title="Normalized Price",
                                            height=500,
                                            template=plot_template,
                                            legend_title_text="Asset"
                                        )
                                        
                                        # Display the chart
                                        st.plotly_chart(fig_comp, use_container_width=True)
                                    else:
                                        st.warning("⚠️ Could not create normalized comparison data for chart.")
                            else:
                                st.error("⚠️ No valid common starting point found for normalization.")
                        else:
                            st.warning("⚠️ Not enough data points after cleaning for the comparison chart.")
                    else:
                        st.warning("⚠️ No valid data rows to process for comparison.")
                except Exception as e:
                    st.error(f"⚠️ Error processing comparison data: {str(e)}")
        except Exception as e:
            st.error(f"⚠️ Error in market comparison section: {str(e)}")
            st.info("Please try a different date range or check your internet connection.")
        
        # Wealth building strategies from provided document
        st.subheader("💡 Strategies to Build Wealth with Stocks")
        
        tabs = st.tabs([
            "High-Growth Investments", 
            "Real Estate", 
            "Entrepreneurship", 
            "Private Equity", 
            "Alternative Investments"
        ])
        
        with tabs[0]:
            st.markdown("""
            ### 1. Invest in High-Growth Stocks and ETFs
            
            - Focus on sectors with high growth potential, such as technology, healthcare, and renewable energy.
            - Consider diversified ETFs to mitigate risk while capturing market gains.
            
            **Potential return:** 10-15% annually with appropriate diversification
            """)
        
        with tabs[1]:
            st.markdown("""
            ### 2. Real Estate Investments
            
            - Invest in commercial properties, which can offer higher returns and stable cash flow.
            - Look for undervalued properties in emerging markets or areas with economic growth.
            
            **Potential return:** 8-12% annually, with potential for higher returns in growth markets
            """)
        
        with tabs[2]:
            st.markdown("""
            ### 3. Entrepreneurship
            
            - Start or acquire businesses with scalable models.
            - Focus on industries you are passionate about and have expertise in.
            
            **Potential return:** Highly variable, potentially much higher than market investments
            """)
        
        with tabs[3]:
            st.markdown("""
            ### 4. Private Equity and Venture Capital
            
            - Invest in startups or private companies with high growth potential.
            - Diversify investments across various industries to spread risk.
            
            **Potential return:** 15-25% annually, with higher risk
            """)
        
        with tabs[4]:
            st.markdown("""
            ### 5. Alternative Investments
            
            - Explore investments in assets like cryptocurrencies, commodities, or collectibles.
            - These can offer high returns but come with increased risk.
            
            **Potential return:** Highly variable, potentially much higher than traditional investments, but with significant risk
            """)
        
        # Disclaimer
        st.markdown("---")
        st.caption("""
        **Disclaimer:** This dashboard is for informational purposes only and does not constitute investment advice. 
        Past performance is not indicative of future results. Always consult with a financial advisor before making investment decisions.
        """)

except Exception as e:
    st.error(f"An error occurred while fetching data: {e}")
    st.info("Please try again later or check if the ticker symbol is correct.")

# Add special handling for Replit environment
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    # This section is only used when running the app directly, not through Streamlit's CLI
