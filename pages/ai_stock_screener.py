import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import os
import sys
import json
from datetime import datetime, timedelta

# Import local modules
from database import add_search_history, add_favorite_stock, is_favorite_stock, add_portfolio_holding
from utils import calculate_moving_averages, calculate_rsi, calculate_bollinger_bands, calculate_macd
from ai_utils import screen_stocks

# Import OpenAI
import openai

# Configure page
st.set_page_config(
    page_title="AI Stock Screener",
    page_icon="🔍",
    layout="wide"
)

# Set up OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_stock_data(ticker, period='6mo'):
    """Get stock data for a specific ticker"""
    try:
        # Download stock data
        data = yf.download(ticker, period=period, progress=False)
        if data.empty:
            return None
        
        # Get stock info
        stock_info = yf.Ticker(ticker).info
        return {'data': data, 'info': stock_info}
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return None

def screen_stocks_with_openai(query, max_results=5):
    """
    Use OpenAI to interpret a natural language query and return stock recommendations
    """
    if not OPENAI_API_KEY:
        st.error("⚠️ OpenAI API key not set. Please provide your API key in the settings.")
        return None
    
    try:
        # Use the centralized function from ai_utils.py
        result = screen_stocks(query, max_results)
        
        # Check for errors
        if "Error:" in result.get("interpretation", ""):
            st.error(result["interpretation"])
            return None
            
        return result
    except Exception as e:
        st.error(f"Error calling OpenAI API: {e}")
        return None

def fetch_stock_metrics(ticker_list):
    """Fetch key metrics for a list of tickers"""
    metrics_df = pd.DataFrame()
    
    for ticker in ticker_list:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract key metrics
            metrics = {
                'Ticker': ticker,
                'Company': info.get('shortName', 'N/A'),
                'Price': info.get('currentPrice', info.get('regularMarketPrice', 'N/A')),
                'Market Cap (B)': info.get('marketCap', 'N/A') / 1e9 if info.get('marketCap') else 'N/A',
                'P/E Ratio': info.get('trailingPE', 'N/A'),
                'Dividend Yield (%)': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 'N/A',
                'YTD Change (%)': info.get('ytdReturn', 'N/A'),
                'Sector': info.get('sector', 'N/A'),
                'Industry': info.get('industry', 'N/A')
            }
            
            # Add to dataframe
            metrics_df = pd.concat([metrics_df, pd.DataFrame([metrics])], ignore_index=True)
            
        except Exception as e:
            st.warning(f"Could not fetch metrics for {ticker}: {e}")
    
    return metrics_df

def display_stock_metrics(metrics_df):
    """Display stock metrics in a formatted table"""
    # Format the metrics
    formatted_df = metrics_df.copy()
    
    # Format numeric columns
    if 'Market Cap (B)' in formatted_df.columns:
        formatted_df['Market Cap (B)'] = formatted_df['Market Cap (B)'].apply(
            lambda x: f"${x:.2f}B" if isinstance(x, (int, float)) else x
        )
    
    if 'P/E Ratio' in formatted_df.columns:
        formatted_df['P/E Ratio'] = formatted_df['P/E Ratio'].apply(
            lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x
        )
    
    if 'Dividend Yield (%)' in formatted_df.columns:
        formatted_df['Dividend Yield (%)'] = formatted_df['Dividend Yield (%)'].apply(
            lambda x: f"{x:.2f}%" if isinstance(x, (int, float)) else x
        )
    
    if 'Price' in formatted_df.columns:
        formatted_df['Price'] = formatted_df['Price'].apply(
            lambda x: f"${x:.2f}" if isinstance(x, (int, float)) else x
        )
    
    if 'YTD Change (%)' in formatted_df.columns:
        formatted_df['YTD Change (%)'] = formatted_df['YTD Change (%)'].apply(
            lambda x: f"{x:.2f}%" if isinstance(x, (int, float)) else x
        )
    
    # Display the table
    st.dataframe(formatted_df, use_container_width=True)

def generate_stock_comparison_chart(tickers, period='6mo'):
    """Generate a comparison chart for multiple tickers"""
    if not tickers:
        return None
    
    # Download data
    comparison_data = {}
    for ticker in tickers:
        try:
            stock_data = yf.download(ticker, period=period, progress=False)
            if not stock_data.empty and 'Close' in stock_data.columns:
                comparison_data[ticker] = stock_data['Close']
        except Exception as e:
            st.warning(f"Could not fetch data for {ticker}: {e}")
    
    if not comparison_data:
        return None
    
    # Create dataframe
    df = pd.DataFrame(comparison_data)
    
    # Normalize data (starting at 100)
    normalized_df = df.dropna(how='all')
    first_valid_idx = normalized_df.first_valid_index()
    
    if first_valid_idx is None:
        return None
    
    # Normalize each column individually
    normalized_data = {}
    for column in normalized_df.columns:
        first_val = normalized_df.loc[first_valid_idx, column]
        if pd.notna(first_val) and first_val != 0:
            normalized_data[column] = (normalized_df[column] / first_val) * 100
    
    normalized_df = pd.DataFrame(normalized_data, index=normalized_df.index)
    
    # Create the chart
    fig = go.Figure()
    
    for column in normalized_df.columns:
        fig.add_trace(
            go.Scatter(
                x=normalized_df.index,
                y=normalized_df[column],
                mode='lines',
                name=column
            )
        )
    
    # Update layout
    fig.update_layout(
        title="Relative Performance Comparison (Normalized at 100)",
        xaxis_title="Date",
        yaxis_title="Normalized Price",
        height=500,
        template="plotly_white",
        legend_title_text="Ticker"
    )
    
    return fig

def main():
    st.title("🔍 AI Stock Screener")
    st.write("Ask for stock recommendations in plain language. The AI will analyze your request and suggest matching stocks.")
    
    # Example queries the user can try
    with st.expander("Example queries to try"):
        st.markdown("""
        - "Show me dividend stocks with yields over 4% in the utilities sector"
        - "What are good growth stocks under $50 per share in the technology sector?"
        - "Recommend low volatility blue-chip stocks for a conservative portfolio"
        - "Find me undervalued small-cap stocks with strong fundamentals"
        - "What are the best renewable energy stocks with good growth potential?"
        """)
    
    # User input for stock screening
    query = st.text_area("Describe the stocks you're looking for:", 
                    placeholder="Example: 'Find me high-dividend stocks with low P/E ratios in the healthcare sector'",
                    height=100)
    
    # Check if OpenAI API key is available
    if not OPENAI_API_KEY:
        st.warning("⚠️ OpenAI API key is required for this feature. Please add your API key in the settings.")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        search_button = st.button("🔍 Find Stocks", type="primary", use_container_width=True)
    
    # Process the query
    if search_button and query:
        with st.spinner("AI is analyzing your request and finding matching stocks..."):
            # Get stock recommendations from OpenAI
            recommendations = screen_stocks_with_openai(query)
            
            if recommendations:
                # Show AI's interpretation
                st.subheader("AI Interpretation")
                st.info(recommendations.get('interpretation', 'No interpretation provided'))
                
                # Extract filter information
                filters = recommendations.get('filters', {})
                if any(filters.values()):
                    st.subheader("Applied Filters")
                    filter_cols = st.columns(5)
                    
                    with filter_cols[0]:
                        if filters.get('min_market_cap'):
                            st.metric("Min Market Cap", f"${filters['min_market_cap']}B")
                    
                    with filter_cols[1]:
                        if filters.get('max_pe'):
                            st.metric("Max P/E Ratio", filters['max_pe'])
                    
                    with filter_cols[2]:
                        if filters.get('min_dividend'):
                            st.metric("Min Dividend", f"{filters['min_dividend']}%")
                    
                    with filter_cols[3]:
                        if filters.get('sector'):
                            st.metric("Sector", filters['sector'])
                    
                    with filter_cols[4]:
                        if filters.get('risk_level'):
                            st.metric("Risk Level", filters['risk_level'].capitalize())
                
                # Extract stock recommendations
                stocks = recommendations.get('stocks', [])
                if stocks:
                    # Get list of tickers
                    tickers = [stock['ticker'] for stock in stocks]
                    
                    # Fetch additional metrics
                    st.subheader("Recommended Stocks")
                    with st.spinner("Fetching stock metrics..."):
                        metrics_df = fetch_stock_metrics(tickers)
                        if not metrics_df.empty:
                            display_stock_metrics(metrics_df)
                        else:
                            st.warning("Could not fetch metrics for the recommended stocks.")
                    
                    # Show reasons for recommendations
                    st.subheader("Why These Stocks?")
                    for stock in stocks:
                        with st.expander(f"{stock['ticker']} - {stock['name']}"):
                            st.write(stock['reason'])
                            
                            col1, col2, col3 = st.columns([1, 1, 1])
                            with col1:
                                if st.button(f"View Details for {stock['ticker']}", key=f"view_{stock['ticker']}"):
                                    # Add to search history
                                    add_search_history(stock['ticker'])
                                    # Redirect to main app
                                    st.session_state['ticker'] = stock['ticker']
                                    st.session_state['redirect_to_main'] = True
                                    st.rerun()
                            
                            with col2:
                                if st.button(f"Add {stock['ticker']} to Favorites", key=f"fav_{stock['ticker']}"):
                                    add_favorite_stock(stock['ticker'], stock['name'])
                                    st.success(f"Added {stock['ticker']} to favorites")
                            
                            with col3:
                                if st.button(f"Add {stock['ticker']} to Watchlist", key=f"watch_{stock['ticker']}"):
                                    add_portfolio_holding(stock['ticker'], stock['name'], 0, is_watchlist=1)
                                    st.success(f"Added {stock['ticker']} to watchlist")
                    
                    # Generate comparison chart
                    st.subheader("Performance Comparison")
                    with st.spinner("Generating comparison chart..."):
                        comparison_chart = generate_stock_comparison_chart(tickers)
                        if comparison_chart:
                            st.plotly_chart(comparison_chart, use_container_width=True)
                        else:
                            st.warning("Could not generate comparison chart. Insufficient data.")
                else:
                    st.warning("No stock recommendations were provided.")
            else:
                st.error("Failed to get recommendations. Please try again.")
    
    # Handle redirect to main app
    if st.session_state.get('redirect_to_main'):
        st.session_state['redirect_to_main'] = False
        # Normally we would redirect, but in Streamlit this is handled differently
        # We'll just instruct the user
        st.info(f"Navigating to {st.session_state.get('ticker')} details. Please click on 'Home' and the stock will be loaded.")

# Run the main function
if __name__ == "__main__":
    main()