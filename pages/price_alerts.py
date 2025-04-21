import streamlit as st
import pandas as pd
import yfinance as yf
import database as db
import time
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Price Alerts",
    page_icon="🔔",
    layout="wide"
)

# Page title
st.title("🔔 Price Alerts")
st.markdown("Set up alerts to get notified when stocks hit your target prices")

# Initialize session state variables
if 'alerts_data' not in st.session_state:
    st.session_state.alerts_data = None
if 'last_price_check' not in st.session_state:
    st.session_state.last_price_check = None
if 'alert_message' not in st.session_state:
    st.session_state.alert_message = None
if 'alert_type' not in st.session_state:
    st.session_state.alert_type = None
if 'notification_history' not in st.session_state:
    st.session_state.notification_history = []

# Function to check if any alerts have been triggered
def check_price_alerts():
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
            st.error(f"Error fetching data for {ticker}: {str(e)}")
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
            
            # Add to notification history for in-app display
            direction = "above" if is_above else "below"
            message = f"Price Alert: {ticker} is now ${current_price:.2f}, {direction} your target of ${target_price:.2f}"
            st.session_state.notification_history.append({
                'ticker': ticker,
                'message': message,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    return triggered_alerts

# Create tabs
tabs = st.tabs(["Current Alerts", "Set New Alert", "Triggered Alerts"])

# Tab 1: Current Alerts
with tabs[0]:
    st.subheader("Your Active Price Alerts")
    
    # Button to manually check alerts
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Check Alerts Now"):
            with st.spinner("Checking current prices..."):
                triggered = check_price_alerts()
                st.session_state.last_price_check = time.time()
                if triggered:
                    st.session_state.alert_message = f"🔔 {len(triggered)} alert(s) triggered!"
                    st.session_state.alert_type = "success"
                else:
                    st.session_state.alert_message = "No alerts triggered"
                    st.session_state.alert_type = "info"
    
    with col2:
        # Show timestamp of last check
        if st.session_state.last_price_check:
            st.caption(f"Last checked: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.session_state.last_price_check))}")
    
    # Display any messages
    if st.session_state.alert_message:
        if st.session_state.alert_type == "success":
            st.success(st.session_state.alert_message)
        elif st.session_state.alert_type == "info":
            st.info(st.session_state.alert_message)
        elif st.session_state.alert_type == "warning":
            st.warning(st.session_state.alert_message)
        elif st.session_state.alert_type == "error":
            st.error(st.session_state.alert_message)
    
    # Get current alerts
    current_alerts = db.get_price_alerts(active_only=True)
    
    if current_alerts:
        # Convert to DataFrame
        alerts_df = pd.DataFrame(current_alerts)
        
        # Fetch current prices for comparison
        tickers = set(alerts_df['ticker'])
        current_prices = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                current_prices[ticker] = current_price
            except:
                current_prices[ticker] = 0
        
        # Add current price to DataFrame
        alerts_df['current_price'] = alerts_df['ticker'].map(current_prices)
        
        # Add human readable columns
        alerts_df['direction'] = alerts_df['is_above'].apply(lambda x: "Above ↑" if x == 1 else "Below ↓")
        alerts_df['distance'] = ((alerts_df['current_price'] - alerts_df['target_price']) / alerts_df['target_price'] * 100).round(2)
        alerts_df['distance_str'] = alerts_df.apply(
            lambda row: f"{abs(row['distance']):.2f}% {'away' if (row['is_above'] == 1 and row['current_price'] < row['target_price']) or (row['is_above'] == 0 and row['current_price'] > row['target_price']) else 'TRIGGERED'}", 
            axis=1
        )
        
        # Format the DataFrame for display
        display_df = alerts_df[['ticker', 'target_price', 'direction', 'current_price', 'distance_str', 'date_created']]
        display_df.columns = ['Ticker', 'Target Price', 'Direction', 'Current Price', 'Status', 'Date Created']
        
        # Display the alerts table
        st.dataframe(display_df.style.format({
            'Target Price': '${:.2f}',
            'Current Price': '${:.2f}',
            'Date Created': lambda x: x.split('.')[0] if '.' in x else x
        }), use_container_width=True)
        
        # Add option to delete alerts
        if st.button("Delete Selected Alerts"):
            st.warning("Alert deletion coming soon")
    else:
        st.info("You don't have any active price alerts. Go to the 'Set New Alert' tab to create one.")

# Tab 2: Set New Alert
with tabs[1]:
    st.subheader("Create a New Price Alert")
    
    # Get portfolio stocks and favorite stocks
    portfolio_stocks = db.get_portfolio_holdings(include_watchlist=True)
    favorite_stocks = db.get_favorite_stocks()
    
    # Combine unique tickers from both sources
    all_stocks = set([stock['ticker'] for stock in portfolio_stocks])
    all_stocks.update([stock['ticker'] for stock in favorite_stocks])
    all_stocks = sorted(list(all_stocks))
    
    # Check if we have a ticker from the main page
    if 'alert_ticker' in st.session_state:
        default_ticker = st.session_state.alert_ticker
        default_company = st.session_state.alert_company
        # Clear the session state so it doesn't persist on refresh
        use_custom = True
        st.info(f"Setting alert for {default_company} ({default_ticker})")
        # Clear after we've used it
        del st.session_state.alert_ticker
        del st.session_state.alert_company
    else:
        default_ticker = ""
        default_company = ""
        use_custom = st.checkbox("Enter a custom ticker")
    
    if use_custom:
        ticker = st.text_input("Enter ticker symbol", default_ticker).upper()
    else:
        if all_stocks:
            ticker = st.selectbox("Select a stock", all_stocks)
        else:
            ticker = st.text_input("Enter ticker symbol (no portfolio or favorite stocks found)", default_ticker).upper()
    
    if ticker:
        # Fetch current price
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            company_name = info.get('shortName', ticker)
            
            # Display current price and company info
            st.metric(f"{company_name} ({ticker})", f"${current_price:.2f}")
            
            # Set the target price
            col1, col2 = st.columns(2)
            
            with col1:
                target_price = st.number_input("Target Price ($)", 
                                             min_value=0.01, 
                                             value=round(current_price, 2),
                                             step=0.01,
                                             format="%.2f")
            
            with col2:
                # Calculate difference from current price
                diff_pct = ((target_price - current_price) / current_price) * 100
                st.metric("Difference from current", f"{diff_pct:.2f}%", delta=f"{diff_pct:.2f}%")
            
            # Set alert type (above or below)
            is_above = st.radio("Alert me when price goes:", 
                              ["Above target", "Below target"],
                              index=0 if target_price > current_price else 1)
            
            is_above_value = 1 if is_above == "Above target" else 0
            
            # Notification options
            st.subheader("Notification Options")
            
            st.info("Price alerts will appear in the app dashboard when triggered.")
            
            # Add notes field
            notes = st.text_area("Add notes (optional)", "", max_chars=200, 
                               help="Add any notes about this alert for your reference")
            
            # Submit button
            if st.button("Create Alert"):
                # Add the alert to the database
                alert_id = db.add_price_alert(
                    ticker=ticker,
                    target_price=target_price,
                    is_above=is_above_value,
                    phone_number=None,
                    email=None
                )
                
                if alert_id:
                    st.success(f"Alert created successfully! You'll be notified when {ticker} goes {'above' if is_above_value else 'below'} ${target_price:.2f}")
                else:
                    st.error("Failed to create alert. Please try again.")
        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {str(e)}")

# Tab 3: Triggered Alerts History
with tabs[2]:
    st.subheader("Triggered Alert History")
    
    # Create two columns for alerts from database and current session
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### From Database")
        # Get all triggered alerts
        triggered_alerts = db.get_price_alerts(active_only=False)
        triggered_alerts = [alert for alert in triggered_alerts if alert['is_triggered'] == 1]
        
        if triggered_alerts:
            # Convert to DataFrame
            alerts_df = pd.DataFrame(triggered_alerts)
            
            # Add human readable columns
            alerts_df['direction'] = alerts_df['is_above'].apply(lambda x: "Above ↑" if x == 1 else "Below ↓")
            
            # Format the DataFrame for display
            display_df = alerts_df[['ticker', 'target_price', 'direction', 'date_created', 'date_triggered']]
            display_df.columns = ['Ticker', 'Target Price', 'Direction', 'Date Created', 'Date Triggered']
            
            # Display the alerts table
            st.dataframe(display_df.style.format({
                'Target Price': '${:.2f}',
                'Date Created': lambda x: x.split('.')[0] if '.' in x else x,
                'Date Triggered': lambda x: x.split('.')[0] if '.' in x and x is not None else x
            }), use_container_width=True)
            
            # Button to clear database history
            if st.button("Clear DB History"):
                with st.spinner("Clearing triggered alerts..."):
                    deleted_count = db.delete_all_triggered_alerts()
                    st.success(f"Cleared {deleted_count} triggered alerts from the database")
                    st.rerun()
        else:
            st.info("No alerts have been triggered in the database yet.")
    
    with col2:
        st.markdown("### This Session")
        # Show notification history from the current session
        if st.session_state.notification_history:
            # Convert notification history to DataFrame
            notif_df = pd.DataFrame(st.session_state.notification_history)
            
            # Display the table
            st.dataframe(notif_df, use_container_width=True)
            
            # Button to clear session history
            if st.button("Clear Session History"):
                st.session_state.notification_history = []
                st.rerun()
        else:
            st.info("No alerts have been triggered in this session.")

# Add information about price alerts
st.markdown("---")
st.subheader("About Price Alerts")
st.markdown("""
- **In-app alerts** are visible when you check alerts in this dashboard
- **Alerts are checked** when you manually click "Check Alerts Now"
- Prices are fetched from Yahoo Finance in real-time when checked
- **Notification history** is maintained across sessions
""")