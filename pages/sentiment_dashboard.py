import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import os
import sys
import json
from datetime import datetime, timedelta
import requests
from io import BytesIO
import base64

# Import local modules
from database import add_search_history, get_favorite_stocks, get_search_history
from ai_utils import generate_market_sentiment_analysis, analyze_news_sentiment
from monetization import is_feature_available, display_feature_teaser
from gamification import track_sentiment_check

# Configure page
st.set_page_config(
    page_title="Sentiment Dashboard",
    page_icon="📊",
    layout="wide"
)

# Function to fetch news for a ticker
def fetch_ticker_news(ticker, max_news=10):
    """
    Fetch latest news for a specific ticker using Yahoo Finance
    """
    try:
        # Get stock info and news
        stock = yf.Ticker(ticker)
        news = stock.news
        
        # Process and return the news items
        if news:
            # Limit to max_news items
            news = news[:max_news]
            
            # Process each news item
            processed_news = []
            for item in news:
                # Extract and format the publish time
                if 'providerPublishTime' in item:
                    publish_time = datetime.fromtimestamp(item['providerPublishTime'])
                    formatted_time = publish_time.strftime('%Y-%m-%d %H:%M')
                else:
                    formatted_time = "Unknown"
                
                # Create processed news item
                processed_item = {
                    'title': item.get('title', 'No title'),
                    'publisher': item.get('publisher', 'Unknown'),
                    'link': item.get('link', '#'),
                    'publish_time': formatted_time,
                    'type': item.get('type', 'STORY'),
                    'thumbnail': item.get('thumbnail', {}).get('resolutions', [{}])[0].get('url', '') if 'thumbnail' in item else ''
                }
                processed_news.append(processed_item)
                
            return processed_news
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching news for {ticker}: {e}")
        return []

# Note: analyze_news_sentiment is imported from ai_utils.py

# Function to display sentiment meter
def display_sentiment_meter(sentiment_score):
    """
    Display a sentiment meter gauge chart based on the sentiment score
    """
    # Create the gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sentiment_score * 100,  # Convert to 0-100 scale
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Market Sentiment"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 35], 'color': '#FF4B4B'},  # Bearish - red
                {'range': [35, 65], 'color': '#FFCC29'},  # Neutral - yellow
                {'range': [65, 100], 'color': '#4CBB17'}  # Bullish - green
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': sentiment_score * 100
            }
        }
    ))
    
    # Update layout
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    return fig

# Function to display sentiment distribution
def display_sentiment_distribution(distribution):
    """
    Display a pie chart showing the distribution of sentiment across news articles
    """
    # Prepare data
    labels = list(distribution.keys())
    values = list(distribution.values())
    
    # Define colors
    colors = {'bullish': '#4CBB17', 'neutral': '#FFCC29', 'bearish': '#FF4B4B'}
    color_values = [colors[label] for label in labels]
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        marker_colors=color_values
    )])
    
    # Update layout
    fig.update_layout(
        title="Sentiment Distribution",
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    return fig

# Function to display news feed with sentiment
def display_news_with_sentiment(news_items):
    """
    Display news items with their sentiment in a visually appealing way
    """
    if not news_items:
        st.info("No news available for this ticker.")
        return
    
    # Define sentiment colors
    sentiment_colors = {
        'bullish': '#4CBB17',  # Green
        'neutral': '#FFCC29',  # Yellow
        'bearish': '#FF4B4B'   # Red
    }
    
    # Define sentiment icons
    sentiment_icons = {
        'bullish': '📈',
        'neutral': '➖',
        'bearish': '📉'
    }
    
    # Display each news item
    for i, item in enumerate(news_items):
        # Get sentiment if available, default to neutral
        sentiment = item.get('sentiment', 'neutral')
        sentiment_score = item.get('sentiment_score', 0.5)
        reasoning = item.get('reasoning', '')
        
        # Create a card-like container for each news item
        with st.container():
            # Add a separator for all but the first item
            if i > 0:
                st.markdown("---")
            
            # Layout: Title row with sentiment indicator
            cols = st.columns([7, 1])
            
            with cols[0]:
                st.markdown(f"### [{item['title']}]({item['link']})")
                st.caption(f"{item['publisher']} • {item['publish_time']}")
            
            with cols[1]:
                st.markdown(f"""
                <div style="
                    background-color: {sentiment_colors.get(sentiment, '#FFCC29')};
                    color: white;
                    text-align: center;
                    padding: 5px;
                    border-radius: 5px;
                    font-weight: bold;
                    margin-top: 15px;
                ">
                    {sentiment_icons.get(sentiment, '➖')} {sentiment.capitalize()}
                </div>
                """, unsafe_allow_html=True)
            
            # Display reasoning if available
            if reasoning:
                with st.expander("Analysis"):
                    st.markdown(f"*{reasoning}*")
            
            # Display thumbnail if available
            if item.get('thumbnail'):
                st.image(item['thumbnail'], width=200)

# Main function
def main():
    st.title("📊 Market Sentiment Dashboard")
    
    # Sidebar for ticker selection
    st.sidebar.header("Select Stock")
    
    # Get favorites and history for quick selection
    favorite_stocks = get_favorite_stocks()
    search_history = get_search_history(limit=5)
    
    # Option to select from favorites
    if favorite_stocks:
        favorite_options = [f"{stock['ticker']} - {stock['company_name']}" for stock in favorite_stocks]
        selected_favorite = st.sidebar.selectbox("Select from favorites", [""] + favorite_options)
        
        if selected_favorite:
            # Extract ticker from selection
            selected_ticker = selected_favorite.split(" - ")[0]
            st.session_state['sentiment_ticker'] = selected_ticker
    
    # Option to select from history
    if search_history:
        history_options = [item['ticker'] for item in search_history]
        selected_history = st.sidebar.selectbox("Select from recent searches", [""] + history_options)
        
        if selected_history:
            st.session_state['sentiment_ticker'] = selected_history
    
    # Manual ticker input
    manual_ticker = st.sidebar.text_input("Or enter ticker symbol:", value=st.session_state.get('sentiment_ticker', ''))
    
    if manual_ticker:
        st.session_state['sentiment_ticker'] = manual_ticker.upper()
    
    # Analysis button
    analyze_button = st.sidebar.button("Analyze Sentiment", type="primary", use_container_width=True)
    
    # Process the selected ticker
    ticker = st.session_state.get('sentiment_ticker', '')
    
    if ticker and analyze_button:
        # Add to search history
        add_search_history(ticker)
        
        # Display stock information
        try:
            # Get basic stock info
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Check if valid ticker
            if 'longName' not in info:
                st.error(f"Invalid ticker symbol: {ticker}")
                return
            
            # Display stock header
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.header(f"{info.get('longName', ticker)} ({ticker})")
                st.subheader(f"{info.get('sector', 'N/A')} | {info.get('industry', 'N/A')}")
            
            with col2:
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
                if isinstance(current_price, (int, float)):
                    price_change = info.get('regularMarketChangePercent', 0) * 100
                    price_color = 'green' if price_change >= 0 else 'red'
                    st.markdown(f"""
                    <div style="text-align: right;">
                        <h2 style="margin-bottom: 0;">${current_price:.2f}</h2>
                        <p style="color: {price_color}; margin-top: 0;">
                            {price_change:.2f}% {('▲' if price_change >= 0 else '▼')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<h2 style='text-align: right;'>{current_price}</h2>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Fetch news and analyze sentiment
            with st.spinner("Fetching latest news and analyzing sentiment..."):
                news_items = fetch_ticker_news(ticker)
                
                if news_items:
                    # Track sentiment check for gamification
                    track_sentiment_check(ticker)
                    
                    # Basic sentiment analysis (for all plans)
                    sentiment_analysis = analyze_news_sentiment(news_items)
                    
                    # Check if user has access to advanced sentiment analysis
                    has_advanced_sentiment = is_feature_available('advanced_sentiment')
                    
                    if sentiment_analysis:
                        # Display overall sentiment
                        st.subheader("Overall Market Sentiment")
                        
                        # Sentiment score and distribution in columns
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Display sentiment meter
                            sentiment_score = sentiment_analysis.get('overall_score', 0.5)
                            sentiment_meter = display_sentiment_meter(sentiment_score)
                            st.plotly_chart(sentiment_meter, use_container_width=True)
                            
                            # Display overall sentiment text
                            overall_sentiment = sentiment_analysis.get('overall_sentiment', 'neutral')
                            sentiment_text = {
                                'bullish': 'The overall sentiment appears BULLISH - positive news and outlook dominate.',
                                'neutral': 'The overall sentiment appears NEUTRAL - mixed signals without clear direction.',
                                'bearish': 'The overall sentiment appears BEARISH - negative news and concerns dominate.'
                            }
                            
                            st.markdown(f"""
                            <div style="
                                background-color: {'#E8F5E9' if overall_sentiment == 'bullish' else '#FFF8E1' if overall_sentiment == 'neutral' else '#FFEBEE'};
                                padding: 10px;
                                border-radius: 5px;
                                margin-bottom: 10px;
                            ">
                                <h3>{sentiment_text.get(overall_sentiment, 'Neutral sentiment detected.')}</h3>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            # Display sentiment distribution
                            distribution = sentiment_analysis.get('sentiment_distribution', {'bullish': 0, 'neutral': 0, 'bearish': 0})
                            distribution_chart = display_sentiment_distribution(distribution)
                            st.plotly_chart(distribution_chart, use_container_width=True)
                            
                            # Display numeric breakdown
                            st.markdown("### Sentiment Breakdown")
                            st.markdown(f"""
                            - 📈 **Bullish**: {distribution.get('bullish', 0)}%
                            - ➖ **Neutral**: {distribution.get('neutral', 0)}%
                            - 📉 **Bearish**: {distribution.get('bearish', 0)}%
                            """)
                        
                        # Display news feed with sentiment analysis
                        st.markdown("---")
                        st.subheader("Latest News & Analysis")
                        display_news_with_sentiment(sentiment_analysis.get('articles', []))
                        
                        # Display teaser for advanced sentiment analysis if user doesn't have premium
                        if not has_advanced_sentiment:
                            st.markdown("---")
                            display_feature_teaser('advanced_sentiment')
                    else:
                        st.error("Could not analyze sentiment. Please try again.")
                else:
                    st.info(f"No recent news found for {ticker}.")
            
        except Exception as e:
            st.error(f"Error analyzing {ticker}: {e}")
    else:
        # Display default welcome message
        st.info("👈 Select a stock from the sidebar or enter a ticker symbol to analyze its market sentiment.")
        
        # Display example of the dashboard with an image
        st.markdown("### What You'll See:")
        st.markdown("""
        - 📰 **Latest News Analysis**: AI reads the news so you don't have to, highlighting key sentiment
        - 📊 **Sentiment Meter**: Visual gauge of market mood
        - 📈 **Bullish/Bearish Signals**: Clear indicators for investment decisions
        """)

# Run the main function
if __name__ == "__main__":
    main()