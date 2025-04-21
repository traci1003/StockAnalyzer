import os
import json
import openai
from openai import OpenAI
import pandas as pd
import yfinance as yf

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_portfolio(holdings, user_preferences=None):
    """
    Analyze a portfolio and provide AI-powered recommendations
    
    Parameters:
    - holdings: List of portfolio holdings with ticker, shares, purchase details, etc.
    - user_preferences: Dictionary of user preferences like risk tolerance, investment goals, etc.
    
    Returns:
    - Dictionary containing analysis and recommendations
    """
    if not holdings or len(holdings) == 0:
        return {
            "summary": "Your portfolio is empty. Please add some holdings to receive personalized recommendations.",
            "risk_assessment": None,
            "diversification": None,
            "recommendations": [],
            "insights": []
        }
    
    # Get additional market data for context
    tickers = [holding['ticker'] for holding in holdings]
    try:
        # Get sector and basic info for all stocks in portfolio
        stock_info = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                stock_info[ticker] = {
                    "sector": stock.info.get("sector", "Unknown"),
                    "industry": stock.info.get("industry", "Unknown"),
                    "marketCap": stock.info.get("marketCap", 0),
                    "beta": stock.info.get("beta", 1.0),
                    "dividendYield": stock.info.get("dividendYield", 0) * 100 if stock.info.get("dividendYield") else 0
                }
            except Exception as e:
                stock_info[ticker] = {
                    "sector": "Unknown",
                    "industry": "Unknown",
                    "marketCap": 0,
                    "beta": 1.0,
                    "dividendYield": 0
                }
    except Exception as e:
        # Default to empty data if API call fails
        stock_info = {ticker: {"sector": "Unknown", "industry": "Unknown", "marketCap": 0, "beta": 1.0, "dividendYield": 0} for ticker in tickers}
    
    # Prepare portfolio data for the AI
    portfolio_data = []
    total_value = 0
    for holding in holdings:
        ticker = holding['ticker']
        current_price = holding.get('current_price', 0)
        shares = holding.get('shares', 0)
        value = current_price * shares if current_price and shares else 0
        total_value += value
        
        portfolio_data.append({
            "ticker": ticker,
            "company": holding.get('company_name', ''),
            "shares": shares,
            "current_price": current_price,
            "value": value,
            "purchase_price": holding.get('purchase_price', 0),
            "purchase_date": holding.get('purchase_date', ''),
            "sector": holding.get('sector', stock_info.get(ticker, {}).get('sector', 'Unknown')),
            "industry": stock_info.get(ticker, {}).get('industry', 'Unknown'),
            "market_cap": stock_info.get(ticker, {}).get('marketCap', 0),
            "beta": stock_info.get(ticker, {}).get('beta', 1.0),
            "dividend_yield": stock_info.get(ticker, {}).get('dividendYield', 0)
        })
    
    # Calculate sector allocation
    sectors = {}
    for holding in portfolio_data:
        sector = holding['sector'] if holding['sector'] != 'Unknown' else 'Other'
        value = holding['value']
        if sector in sectors:
            sectors[sector] += value
        else:
            sectors[sector] = value
    
    # Calculate sector percentages
    sector_allocation = []
    for sector, value in sectors.items():
        if total_value > 0:
            percentage = (value / total_value) * 100
            sector_allocation.append({"sector": sector, "percentage": percentage})
    
    # Sort by percentage
    sector_allocation = sorted(sector_allocation, key=lambda x: x['percentage'], reverse=True)
    
    # User preferences context
    risk_profile = user_preferences.get('risk_profile', 'Moderate') if user_preferences else 'Moderate'
    investment_horizon = user_preferences.get('investment_horizon', 'Medium-term') if user_preferences else 'Medium-term'
    investment_goals = user_preferences.get('investment_goals', 'Balanced growth') if user_preferences else 'Balanced growth'
    
    # Generate prompt for OpenAI
    system_prompt = """You are an expert financial advisor and portfolio analyst. Analyze the provided portfolio data and generate personalized investment recommendations.
    Focus on providing actionable insights about:
    1. Overall portfolio assessment and risk profile
    2. Diversification analysis (sector allocation, asset distribution)
    3. Specific stock recommendations (what to buy, hold, or sell)
    4. Areas for portfolio improvement
    5. Potential opportunities based on market conditions
    
    Your analysis should be data-driven, personalized to the user's risk profile and goals, and presented in a clear, professional manner.
    Include specific tickers when making recommendations. Be thorough but concise.
    
    Provide your response as a JSON object with the following structure:
    {
        "summary": "Brief assessment of the overall portfolio",
        "risk_assessment": "Analysis of the portfolio's risk level",
        "diversification": "Assessment of diversification across sectors",
        "recommendations": [
            {
                "type": "buy"|"sell"|"hold"|"watch",
                "ticker": "Symbol",
                "reasoning": "Brief explanation"
            }
        ],
        "insights": [
            "Key insight 1",
            "Key insight 2"
        ]
    }
    """
    
    # Prepare the portfolio data as a string
    portfolio_str = json.dumps({
        "holdings": portfolio_data,
        "sector_allocation": sector_allocation,
        "total_value": total_value,
        "preferences": {
            "risk_profile": risk_profile,
            "investment_horizon": investment_horizon,
            "investment_goals": investment_goals
        }
    }, indent=2)
    
    user_prompt = f"Please analyze the following investment portfolio and provide recommendations:\n{portfolio_str}"
    
    try:
        # Make API call to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=2000
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        # Return error information
        return {
            "summary": f"There was an error generating AI recommendations: {str(e)}",
            "risk_assessment": "Unable to assess risk due to an error.",
            "diversification": "Unable to analyze diversification due to an error.",
            "recommendations": [],
            "insights": ["Please try again later or contact support if the issue persists."]
        }

def screen_stocks(query, max_results=5):
    """
    Use OpenAI to interpret a natural language query and return stock recommendations
    
    Parameters:
    - query: Natural language query describing the desired stock characteristics
    - max_results: Maximum number of results to return
    
    Returns:
    - Dictionary containing screened stocks and interpretation
    """
    if not OPENAI_API_KEY:
        return {
            "interpretation": "Error: OpenAI API key not set.",
            "stocks": [],
            "filters": {}
        }
    
    try:
        # Define the system prompt for stock screening
        system_prompt = """
        You are an expert financial advisor specialized in stock screening and recommendations.
        Your task is to recommend stocks based on user criteria and return the results in a specific JSON format.
        
        Only recommend actual, real publicly traded companies with valid ticker symbols that can be looked up using Yahoo Finance.
        The tickers should be valid for US exchanges (NYSE, NASDAQ).
        Do not make up companies or tickers.
        
        Output format (strictly JSON):
        {
          "interpretation": "Brief explanation of how you interpreted the user's request",
          "stocks": [
            {
              "ticker": "AAPL",
              "name": "Apple Inc.",
              "reason": "Brief reason why this stock matches the criteria"
            },
            // more stocks...
          ],
          "filters": {
            "min_market_cap": null,  // minimum market cap in billions USD, or null if not specified
            "max_pe": null,          // maximum PE ratio, or null if not specified
            "min_dividend": null,    // minimum dividend yield percentage, or null if not specified
            "sector": null,          // sector name, or null if not specified
            "risk_level": null       // "low", "medium", "high", or null if not specified
          }
        }
        
        Include between 3-5 stocks in your recommendations.
        """
        
        # Call the OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1200
        )
        
        # Parse the response
        response_content = response.choices[0].message.content
        result = json.loads(response_content)
        
        return result
    except Exception as e:
        # Return error information
        return {
            "interpretation": f"Error: {str(e)}",
            "stocks": [],
            "filters": {}
        }

def analyze_news_sentiment(news_items):
    """
    Analyze the sentiment of news headlines using OpenAI
    
    Parameters:
    - news_items: List of news items with 'title' keys
    
    Returns:
    - Dictionary containing sentiment analysis
    """
    # Check if there are news items to analyze
    if not news_items:
        return {
            "overall_sentiment": "neutral",
            "overall_score": 0.5,
            "sentiment_distribution": {"bullish": 0, "neutral": 0, "bearish": 0},
            "articles": []
        }
    
    # Extract headlines for analysis
    headlines = [item['title'] for item in news_items]
    
    # Generate prompt for OpenAI
    system_prompt = """You are an expert financial news analyst. 
    Analyze the sentiment of the provided news headlines about a stock or company.
    
    For each headline, determine if the sentiment is:
    - bullish (positive for the stock price)
    - bearish (negative for the stock price)
    - neutral (neither clearly positive nor negative)
    
    Provide a sentiment score between 0 and 1 for each headline, where:
    - 0 to 0.35 is bearish
    - 0.36 to 0.65 is neutral
    - 0.66 to 1 is bullish
    
    Also provide an overall sentiment assessment and score.
    
    Return your analysis as JSON with the following structure:
    {
        "overall_sentiment": "bullish"|"neutral"|"bearish",
        "overall_score": 0.75, 
        "sentiment_distribution": {"bullish": 60, "neutral": 30, "bearish": 10},
        "articles": [
            {
                "headline": "Article headline text",
                "sentiment": "bullish"|"neutral"|"bearish",
                "score": 0.75,
                "reasoning": "Brief explanation of the sentiment"
            }
        ]
    }
    
    The sentiment_distribution should be the percentage of articles in each category.
    """
    
    # Prepare the headlines as a string
    headlines_text = "\n".join([f"- {headline}" for headline in headlines])
    
    try:
        # Call the OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze the sentiment of these headlines:\n{headlines_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=1500
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Combine the results with the original news items
        for i, article_analysis in enumerate(result['articles']):
            if i < len(news_items):
                news_items[i]['sentiment'] = article_analysis.get('sentiment', 'neutral')
                news_items[i]['sentiment_score'] = article_analysis.get('score', 0.5)
                news_items[i]['reasoning'] = article_analysis.get('reasoning', '')
        
        # Set the overall analysis
        result['articles'] = news_items
        
        return result
    
    except Exception as e:
        # Return basic structure with neutral sentiment
        return {
            "overall_sentiment": "neutral",
            "overall_score": 0.5,
            "sentiment_distribution": {"bullish": 0, "neutral": 100, "bearish": 0},
            "articles": news_items
        }

def generate_market_sentiment_analysis(tickers):
    """
    Generate market sentiment analysis for a list of tickers
    
    Parameters:
    - tickers: List of stock tickers to analyze
    
    Returns:
    - Dictionary containing sentiment analysis
    """
    if not tickers or len(tickers) == 0:
        return {
            "overall_market": "No tickers provided for sentiment analysis.",
            "stocks": {}
        }
    
    # Get some basic stock info for context
    stock_data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1mo")
            
            # Calculate monthly performance
            if not hist.empty:
                start_price = hist['Close'].iloc[0]
                end_price = hist['Close'].iloc[-1]
                monthly_change = ((end_price - start_price) / start_price) * 100
            else:
                monthly_change = 0
                
            stock_data[ticker] = {
                "name": info.get("shortName", ticker),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
                "monthly_change": monthly_change
            }
        except Exception as e:
            stock_data[ticker] = {
                "name": ticker,
                "sector": "Unknown",
                "error": str(e)
            }
    
    # Generate prompt for OpenAI
    system_prompt = """You are an expert financial market analyst. Analyze the provided stock data and generate a market sentiment analysis.
    Focus on providing insights about:
    1. Overall market sentiment
    2. Individual stock sentiment (bullish, bearish, or neutral)
    3. Recent performance and key factors affecting each stock
    
    Your analysis should be data-driven and presented in a clear, professional manner.
    
    Provide your response as a JSON object with the following structure:
    {
        "overall_market": "Brief assessment of the overall market sentiment",
        "stocks": {
            "TICKER1": {
                "sentiment": "bullish"|"bearish"|"neutral",
                "analysis": "Brief analysis with key points",
                "outlook": "Short-term outlook"
            },
            "TICKER2": {...}
        }
    }
    """
    
    # Prepare the stock data as a string
    stock_data_str = json.dumps(stock_data, indent=2)
    
    user_prompt = f"Please analyze the following stocks and provide a market sentiment analysis:\n{stock_data_str}"
    
    try:
        # Make API call to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=2000
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        # Return error information
        return {
            "overall_market": f"There was an error generating sentiment analysis: {str(e)}",
            "stocks": {ticker: {"sentiment": "unknown", "analysis": "Error in analysis", "outlook": "Unknown"} for ticker in tickers}
        }