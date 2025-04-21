import streamlit as st
import pandas as pd
import plotly.express as px
import time
import database as db
import yfinance as yf
from ai_utils import analyze_portfolio, generate_market_sentiment_analysis
from monetization import is_feature_available, display_feature_teaser
from gamification import track_ai_screener_use

# Set page config
st.set_page_config(
    page_title="AI Investment Advisor",
    page_icon="🤖",
    layout="wide"
)

# Page title
st.title("🤖 AI Investment Advisor")
st.markdown("Get personalized investment recommendations and insights powered by AI")

# Initialize session state variables
if 'ai_recommendations' not in st.session_state:
    st.session_state.ai_recommendations = None
if 'sentiment_analysis' not in st.session_state:
    st.session_state.sentiment_analysis = None
if 'last_recommendation_time' not in st.session_state:
    st.session_state.last_recommendation_time = None
if 'last_sentiment_time' not in st.session_state:
    st.session_state.last_sentiment_time = None
if 'has_advanced_ai' not in st.session_state:
    st.session_state.has_advanced_ai = is_feature_available('advanced_ai_recommendations')
if 'has_premium_sentiment' not in st.session_state:
    st.session_state.has_premium_sentiment = is_feature_available('premium_market_sentiment')

# Create tabs for different AI services
tabs = st.tabs(["Portfolio Recommendations", "Market Sentiment", "User Preferences"])

# Tab 1: Portfolio Recommendations
with tabs[0]:
    st.subheader("AI-Powered Portfolio Recommendations")
    st.markdown("Our AI analyzes your portfolio holdings to provide personalized recommendations tailored to your investment goals and preferences.")
    
    # Get portfolio data
    holdings = db.get_portfolio_holdings(include_watchlist=False)
    
    if len(holdings) == 0:
        st.warning("⚠️ Your portfolio is empty. Please add some holdings in the Portfolio Tracker to receive personalized recommendations.")
        recommendation_disabled = True
    else:
        # Process the portfolio data
        portfolio_data = []
        total_value = 0
        total_cost = 0
        
        # Process each holding with current price data
        for holding in holdings:
            ticker = holding['ticker']
            shares = holding['shares']
            purchase_price = holding['purchase_price'] if holding['purchase_price'] else 0
            
            # Fetch current price data from yfinance
            try:
                ticker_data = yf.Ticker(ticker)
                info = ticker_data.info
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                
                # Add current price to holding
                holding_with_price = holding.copy()
                holding_with_price['current_price'] = current_price
                holding_with_price['value'] = current_price * shares
                portfolio_data.append(holding_with_price)
                
                # Calculate totals
                total_value += current_price * shares
                total_cost += purchase_price * shares
            except Exception as e:
                st.error(f"Error fetching data for {ticker}: {str(e)}")
        
        # Create DataFrame from processed data
        portfolio_df = pd.DataFrame(portfolio_data)
        
        # Calculate average return
        if 'purchase_price' in portfolio_df.columns and 'current_price' in portfolio_df.columns:
            portfolio_df['gain_loss_pct'] = ((portfolio_df['current_price'] - portfolio_df['purchase_price']) / portfolio_df['purchase_price']) * 100
            avg_return = portfolio_df['gain_loss_pct'].mean() if not portfolio_df['gain_loss_pct'].empty else 0
            
            # Display portfolio summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Holdings", f"{len(portfolio_data)}")
            with col2:
                st.metric("Portfolio Value", f"${total_value:,.2f}")
            with col3:
                st.metric("Average Return", f"{avg_return:.2f}%", delta=f"{avg_return:.2f}%")
        
        recommendation_disabled = False
    
    # Button to generate recommendations
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Generate Recommendations", key="gen_recommendations", disabled=recommendation_disabled):
            with st.spinner("Analyzing your portfolio and generating recommendations..."):
                # Get user preferences
                user_preferences = db.get_user_preferences()
                
                # Track usage for gamification
                track_ai_screener_use()
                
                # Update session state for premium feature access
                st.session_state.has_advanced_ai = is_feature_available('advanced_ai_recommendations')
                
                # Generate recommendations using the portfolio data with current prices
                if 'portfolio_data' in locals():
                    recommendations = analyze_portfolio(portfolio_data, user_preferences)
                else:
                    # This should not happen, but handle it gracefully
                    st.error("Portfolio data is not available. Please try again.")
                    recommendations = {
                        'summary': 'Unable to analyze portfolio',
                        'risk_assessment': 'N/A',
                        'diversification': 'N/A',
                        'recommendations': [],
                        'insights': ['Please try again later']
                    }
                st.session_state.ai_recommendations = recommendations
                st.session_state.last_recommendation_time = time.time()
    
    with col2:
        # Show timestamp of last recommendation
        if st.session_state.last_recommendation_time:
            st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.session_state.last_recommendation_time))}")
    
    # Display the AI recommendations
    if st.session_state.ai_recommendations:
        recommendations = st.session_state.ai_recommendations
        
        # Portfolio summary
        st.markdown("### Portfolio Assessment")
        st.markdown(f"**{recommendations['summary']}**")
        
        # Create 2 columns for risk and diversification
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Risk Assessment")
            st.markdown(recommendations['risk_assessment'])
        
        with col2:
            st.markdown("#### Diversification Analysis")
            st.markdown(recommendations['diversification'])
        
        # Specific recommendations
        st.markdown("### Investment Recommendations")
        
        if recommendations['recommendations']:
            # Convert recommendations to DataFrame
            rec_df = pd.DataFrame(recommendations['recommendations'])
            
            # Create styled table with color-coded recommendation types
            def highlight_recommendation_type(val):
                color_map = {
                    'buy': 'background-color: #d4f1d4',    # Light green
                    'sell': 'background-color: #ffd4d4',   # Light red
                    'hold': 'background-color: #e6f3ff',   # Light blue
                    'watch': 'background-color: #fff2cc'   # Light yellow
                }
                return color_map.get(val.lower(), '')
            
            # Apply styles and display
            styled_rec = rec_df.style.applymap(highlight_recommendation_type, subset=['type'])
            st.dataframe(styled_rec, use_container_width=True)
        else:
            st.info("No specific stock recommendations at this time.")
        
        # Key insights
        st.markdown("### Key Insights")
        for insight in recommendations['insights']:
            st.markdown(f"• {insight}")
        
        # Display premium teaser for advanced AI recommendations if not available
        if not st.session_state.has_advanced_ai:
            st.markdown("---")
            display_feature_teaser('advanced_ai_recommendations')
        
        # Disclaimer
        st.markdown("---")
        st.caption("""
        **Disclaimer:** These recommendations are generated by an AI model and should not be considered financial advice. 
        Always do your own research and consult with a professional financial advisor before making investment decisions.
        """)

# Tab 2: Market Sentiment
with tabs[1]:
    st.subheader("Market Sentiment Analysis")
    st.markdown("Get AI-powered sentiment analysis for stocks in your portfolio and watchlist.")
    
    # Get all tickers from portfolio and watchlist
    portfolio_stocks = db.get_portfolio_holdings(include_watchlist=True)
    all_tickers = list(set([stock['ticker'] for stock in portfolio_stocks]))
    
    # Let user add additional tickers
    with st.expander("Add tickers for sentiment analysis"):
        additional_tickers = st.text_input("Enter additional ticker symbols (separated by commas)", "")
        if additional_tickers:
            new_tickers = [ticker.strip().upper() for ticker in additional_tickers.split(',')]
            all_tickers = list(set(all_tickers + new_tickers))
    
    # Display the list of tickers that will be analyzed
    st.markdown(f"**Analyzing {len(all_tickers)} stocks:** {', '.join(all_tickers)}" if all_tickers else "No stocks selected for analysis.")
    
    # Button to generate sentiment analysis
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Analyze Market Sentiment", key="analyze_sentiment", disabled=len(all_tickers) == 0):
            with st.spinner("Analyzing market sentiment..."):
                # Update session state for premium feature access
                st.session_state.has_premium_sentiment = is_feature_available('premium_market_sentiment')
                
                # Track sentiment analysis for gamification
                track_ai_screener_use()
                
                # Generate market sentiment analysis
                sentiment = generate_market_sentiment_analysis(all_tickers)
                st.session_state.sentiment_analysis = sentiment
                st.session_state.last_sentiment_time = time.time()
    
    with col2:
        # Show timestamp of last analysis
        if st.session_state.last_sentiment_time:
            st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.session_state.last_sentiment_time))}")
    
    # Display the sentiment analysis
    if st.session_state.sentiment_analysis:
        sentiment = st.session_state.sentiment_analysis
        
        # Display overall market sentiment
        st.markdown("### Overall Market Assessment")
        st.markdown(sentiment['overall_market'])
        
        # Display individual stock sentiments
        st.markdown("### Stock Sentiment Analysis")
        
        # Prepare data for display
        sentiment_data = []
        for ticker, analysis in sentiment['stocks'].items():
            if isinstance(analysis, dict): 
                sentiment_data.append({
                    "Ticker": ticker,
                    "Sentiment": analysis.get('sentiment', 'unknown').capitalize(),
                    "Analysis": analysis.get('analysis', 'No analysis available'),
                    "Outlook": analysis.get('outlook', 'Unknown')
                })
        
        if sentiment_data:
            sent_df = pd.DataFrame(sentiment_data)
            
            # Create a function to highlight sentiment
            def highlight_sentiment(val):
                if val.lower() == 'bullish':
                    return 'background-color: #d4f1d4'
                elif val.lower() == 'bearish':
                    return 'background-color: #ffd4d4'
                elif val.lower() == 'neutral':
                    return 'background-color: #f0f0f0'
                else:
                    return ''
            
            # Apply styles and display
            styled_sent = sent_df.style.applymap(highlight_sentiment, subset=['Sentiment'])
            st.dataframe(styled_sent, use_container_width=True)
        
        # Display premium teaser for market sentiment if not available
        if not st.session_state.has_premium_sentiment:
            st.markdown("---")
            display_feature_teaser('premium_market_sentiment')
        
        # Disclaimer
        st.markdown("---")
        st.caption("""
        **Disclaimer:** This sentiment analysis is generated by an AI model based on available market data and should not be considered financial advice. 
        Market conditions can change rapidly. Always do your own research before making investment decisions.
        """)

# Tab 3: User Preferences
with tabs[2]:
    st.subheader("Your Investment Preferences")
    st.markdown("Set your investment preferences to receive more personalized AI recommendations.")
    
    # Get current preferences
    current_prefs = db.get_user_preferences()
    
    # Risk profile
    risk_profile = st.select_slider(
        "Risk Tolerance",
        options=["Very Conservative", "Conservative", "Moderate", "Aggressive", "Very Aggressive"],
        value=current_prefs.get('risk_profile', 'Moderate')
    )
    
    # Investment horizon
    investment_horizon = st.radio(
        "Investment Time Horizon",
        options=["Short-term (< 1 year)", "Medium-term (1-5 years)", "Long-term (5+ years)"],
        index=["Short-term (< 1 year)", "Medium-term (1-5 years)", "Long-term (5+ years)"].index(current_prefs.get('investment_horizon', 'Medium-term (1-5 years)'))
    )
    
    # Investment goals
    investment_goals = st.multiselect(
        "Investment Goals",
        options=["Capital Preservation", "Income Generation", "Balanced Growth", "Capital Appreciation", "Aggressive Growth"],
        default=current_prefs.get('investment_goals', ['Balanced Growth'])
    )
    
    # Additional preferences
    col1, col2 = st.columns(2)
    
    with col1:
        prefer_dividends = st.checkbox("Prefer dividend-paying stocks", value=current_prefs.get('prefer_dividends', False))
        esg_focus = st.checkbox("Focus on ESG/Sustainable investing", value=current_prefs.get('esg_focus', False))
    
    with col2:
        tax_efficiency = st.checkbox("Prioritize tax efficiency", value=current_prefs.get('tax_efficiency', False))
        international_exposure = st.checkbox("Seek international exposure", value=current_prefs.get('international_exposure', False))
    
    # Sector preferences
    sector_preferences = st.multiselect(
        "Preferred Sectors",
        options=["Technology", "Healthcare", "Consumer Discretionary", "Consumer Staples", "Financials", 
                "Industrials", "Energy", "Utilities", "Materials", "Real Estate", "Communication Services"],
        default=current_prefs.get('sector_preferences', [])
    )
    
    # Button to save preferences
    if st.button("Save Preferences"):
        new_preferences = {
            'risk_profile': risk_profile,
            'investment_horizon': investment_horizon,
            'investment_goals': investment_goals,
            'prefer_dividends': prefer_dividends,
            'esg_focus': esg_focus,
            'tax_efficiency': tax_efficiency,
            'international_exposure': international_exposure,
            'sector_preferences': sector_preferences
        }
        
        # Update in database
        db.update_user_preferences(new_preferences)
        st.success("Your investment preferences have been saved! The AI will use these to generate more personalized recommendations.")