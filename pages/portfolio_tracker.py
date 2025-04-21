import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import database as db

# Set page title
st.set_page_config(
    page_title="Portfolio Tracker",
    page_icon="💼",
    layout="wide"
)

# Import monetization features
from monetization import is_feature_available, display_feature_teaser

# Page title
st.title("💼 Portfolio Tracker")
st.markdown("Track your investments and analyze your portfolio performance.")

# Function to calculate portfolio performance
def calculate_portfolio_performance(holdings):
    if not holdings:
        return pd.DataFrame(), 0, 0, 0, 0, 0
    
    portfolio_data = []
    total_value = 0
    total_cost = 0
    total_realized_gain = 0
    
    # Keep track of sectors
    sector_lookup = {}
    
    for holding in holdings:
        ticker = holding['ticker']
        shares = holding['shares']
        purchase_price = holding['purchase_price'] if holding['purchase_price'] else 0
        sell_price = holding['sell_price'] if holding['sell_price'] else 0
        is_watchlist = holding['is_watchlist'] == 1
        
        # Get latest data for the ticker
        ticker_data = yf.Ticker(ticker)
        info = ticker_data.info
        
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        company_name = info.get('shortName', ticker)
        
        # Get sector if not provided
        sector = holding['sector']
        if not sector and ticker not in sector_lookup:
            sector = info.get('sector', 'Not Available')
            sector_lookup[ticker] = sector
        elif ticker in sector_lookup:
            sector = sector_lookup[ticker]
        
        # Calculate values
        current_value = current_price * shares
        cost_basis = purchase_price * shares if purchase_price else 0
        
        # Handle sold stocks
        realized_gain = 0
        if sell_price and sell_price > 0:
            realized_gain = (sell_price - purchase_price) * shares if purchase_price else 0
            current_value = sell_price * shares  # Use sell value instead of current value
            total_realized_gain += realized_gain
        
        # Calculate unrealized profit/loss for active positions
        profit_loss = current_value - cost_basis if purchase_price else 0
        profit_loss_percent = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0
        
        # Calculate days held
        purchase_date = datetime.strptime(holding['purchase_date'], '%Y-%m-%d') if holding['purchase_date'] else None
        sell_date = datetime.strptime(holding['sell_date'], '%Y-%m-%d') if holding['sell_date'] else None
        
        days_held = None
        if purchase_date:
            if sell_date:
                days_held = (sell_date - purchase_date).days
            else:
                days_held = (datetime.now() - purchase_date).days
        
        # Add to totals (watchlist items don't count toward totals)
        if not is_watchlist:
            total_value += current_value
            if purchase_price:
                total_cost += cost_basis
        
        # Create row
        portfolio_data.append({
            'ID': holding['id'],
            'Ticker': ticker,
            'Company': company_name,
            'Sector': sector,
            'Shares': shares,
            'Purchase Price': f"${purchase_price:.2f}" if purchase_price else "Not Set",
            'Purchase Date': holding['purchase_date'] if holding['purchase_date'] else "Not Set",
            'Current Price': f"${current_price:.2f}",
            'Current Value': current_value,
            'Cost Basis': cost_basis if purchase_price else "Not Set",
            'Profit/Loss': profit_loss if purchase_price else "Not Set",
            'Profit/Loss %': f"{profit_loss_percent:.2f}%" if purchase_price else "Not Set",
            'Is Watchlist': is_watchlist,
            'Sell Price': f"${sell_price:.2f}" if sell_price else "Not Set",
            'Sell Date': holding['sell_date'] if holding['sell_date'] else "Not Set",
            'Realized Gain': realized_gain if sell_price and purchase_price else "Not Set",
            'Status': "Sold" if sell_price and sell_price > 0 else ("Watchlist" if is_watchlist else "Active"),
            'Days Held': days_held if days_held is not None else "N/A",
            'Date Added': holding['date_added'],
            'Notes': holding['notes'] if holding['notes'] else ""
        })
    
    # Create DataFrame
    df = pd.DataFrame(portfolio_data)
    
    # Calculate total profit/loss and average return
    total_profit_loss = total_value - total_cost
    total_profit_loss_percent = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
    
    # Calculate average return percentage across positions
    # Filter to only include non-watchlist items with a purchase price
    active_positions = [row for row in portfolio_data if not row['Is Watchlist'] and not isinstance(row['Profit/Loss %'], str)]
    if active_positions:
        avg_return_pct = sum([float(row['Profit/Loss %'].replace('%', '')) for row in active_positions if not isinstance(row['Profit/Loss %'], str)]) / len(active_positions)
    else:
        avg_return_pct = 0
    
    return df, total_value, total_profit_loss, total_profit_loss_percent, avg_return_pct, total_realized_gain

# Initialize session state for filters
if 'include_watchlist' not in st.session_state:
    st.session_state.include_watchlist = True
if 'selected_sector' not in st.session_state:
    st.session_state.selected_sector = None
if 'filter_type' not in st.session_state:
    st.session_state.filter_type = None

# Main layout with filter controls at the top
st.subheader("Portfolio Filters")
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    # List of available sectors
    sectors = db.get_available_sectors()
    sector_options = ["All Sectors"] + sectors
    selected_sector = st.selectbox(
        "Filter by Sector",
        options=sector_options,
        index=0
    )
    st.session_state.selected_sector = None if selected_sector == "All Sectors" else selected_sector

with filter_col2:
    filter_options = ["All Holdings", "Active Only", "Sold Only", "Gainers", "Losers"]
    selected_filter = st.selectbox(
        "Filter by Status",
        options=filter_options,
        index=0
    )
    
    if selected_filter == "Active Only":
        st.session_state.filter_type = "active"
    elif selected_filter == "Sold Only":
        st.session_state.filter_type = "sold"
    elif selected_filter == "Gainers":
        st.session_state.filter_type = "gainers"
    elif selected_filter == "Losers":
        st.session_state.filter_type = "losers"
    else:
        st.session_state.filter_type = None

with filter_col3:
    include_watchlist = st.checkbox("Include Watchlist Items", value=st.session_state.include_watchlist)
    st.session_state.include_watchlist = include_watchlist

with filter_col4:
    if st.button("Reset Filters"):
        st.session_state.include_watchlist = True
        st.session_state.selected_sector = None
        st.session_state.filter_type = None
        st.rerun()

# Main content area
col1, col2 = st.columns([1, 2])

# COLUMN 1: Add/Edit Holdings
with col1:
    # Tabs for different actions
    add_tab, sell_tab, watchlist_tab = st.tabs(["Add Position", "Record Sale", "Add to Watchlist"])
    
    # Add Position Tab
    with add_tab:
        with st.form("add_stock_form"):
            ticker_input = st.text_input("Ticker Symbol").upper()
            shares_input = st.number_input("Number of Shares", min_value=0.01, step=0.01)
            purchase_price = st.number_input("Purchase Price ($)", min_value=0.01, step=0.01, value=None)
            purchase_date = st.date_input("Purchase Date", value=datetime.today())
            
            # Get sector info
            sector_input = st.text_input("Sector (optional)")
            
            notes = st.text_area("Notes (optional)")
            
            submitted = st.form_submit_button("Add to Portfolio")
            
            if submitted and ticker_input and shares_input > 0:
                try:
                    # Verify ticker exists
                    ticker_data = yf.Ticker(ticker_input)
                    info = ticker_data.info
                    company_name = info.get('shortName', ticker_input)
                    
                    # Get sector if not provided
                    if not sector_input:
                        sector_input = info.get('sector', None)
                    
                    # Add to database
                    success, _ = db.add_portfolio_holding(
                        ticker_input, 
                        company_name, 
                        shares_input,
                        purchase_price,
                        purchase_date.strftime('%Y-%m-%d') if purchase_date else None,
                        sell_price=None,
                        sell_date=None,
                        is_watchlist=0,
                        sector=sector_input,
                        notes=notes
                    )
                    
                    if success:
                        st.success(f"Added {shares_input} shares of {ticker_input} to your portfolio!")
                        st.rerun()
                    else:
                        st.error("Failed to add holding. Please try again.")
                except Exception as e:
                    st.error(f"Error: Could not add holding. Please check the ticker symbol and try again. {str(e)}")
    
    # Record Sale Tab
    with sell_tab:
        # Get active holdings (non-watchlist, non-sold)
        active_holdings = [h for h in db.get_portfolio_holdings(include_watchlist=False, filter_type='active') 
                          if h['sell_price'] is None or h['sell_price'] == 0]
        
        if not active_holdings:
            st.info("You don't have any active positions to sell. Add a position first.")
        else:
            with st.form("sell_stock_form"):
                # Create a dropdown of available holdings
                holding_options = [(h['id'], f"{h['ticker']} - {h['shares']} shares @ ${h['purchase_price'] if h['purchase_price'] else 0:.2f}") 
                                  for h in active_holdings]
                
                selected_holding_id = st.selectbox(
                    "Select Position to Sell",
                    options=[h[0] for h in holding_options],
                    format_func=lambda x: next((h[1] for h in holding_options if h[0] == x), x)
                )
                
                # Get the selected holding
                selected_holding = next((h for h in active_holdings if h['id'] == selected_holding_id), None)
                
                if selected_holding:
                    # Show current info
                    ticker = selected_holding['ticker']
                    shares = selected_holding['shares']
                    purchase_price = selected_holding['purchase_price'] if selected_holding['purchase_price'] else 0
                    
                    # Get current market price
                    ticker_data = yf.Ticker(ticker)
                    current_price = ticker_data.info.get('currentPrice', ticker_data.info.get('regularMarketPrice', 0))
                    
                    st.info(f"Current market price: ${current_price:.2f}")
                    
                    # Sell form fields
                    sell_price = st.number_input("Sell Price ($)", min_value=0.01, value=current_price, step=0.01)
                    sell_date = st.date_input("Sell Date", value=datetime.today())
                    
                    # Calculate and display realized gain/loss
                    realized_gain = (sell_price - purchase_price) * shares
                    gain_percent = (realized_gain / (purchase_price * shares) * 100) if purchase_price > 0 else 0
                    
                    gain_color = "green" if realized_gain >= 0 else "red"
                    st.markdown(f"**Realized Gain/Loss:** <span style='color:{gain_color}'>${realized_gain:.2f} ({gain_percent:.2f}%)</span>", unsafe_allow_html=True)
                    
                    submitted = st.form_submit_button("Record Sale")
                    
                    if submitted:
                        success = db.update_portfolio_holding(
                            selected_holding_id,
                            shares,
                            purchase_price,
                            selected_holding['purchase_date'],
                            sell_price=sell_price,
                            sell_date=sell_date.strftime('%Y-%m-%d'),
                            notes=selected_holding['notes']
                        )
                        
                        if success:
                            st.success(f"Sale of {shares} shares of {ticker} recorded successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to record sale. Please try again.")
    
    # Watchlist Tab
    with watchlist_tab:
        with st.form("add_watchlist_form"):
            ticker_input = st.text_input("Ticker Symbol", key="watchlist_ticker").upper()
            shares_input = st.number_input("Simulated Shares (for tracking)", min_value=0.01, step=1.0, value=100.0, key="watchlist_shares")
            target_price = st.number_input("Target Price (optional)", min_value=0.0, step=0.01, value=0.0, key="watchlist_price")
            notes = st.text_area("Notes (optional)", key="watchlist_notes")
            
            submitted = st.form_submit_button("Add to Watchlist")
            
            if submitted and ticker_input:
                try:
                    # Verify ticker exists
                    ticker_data = yf.Ticker(ticker_input)
                    info = ticker_data.info
                    company_name = info.get('shortName', ticker_input)
                    sector = info.get('sector', None)
                    
                    # Add to database as watchlist item
                    success, _ = db.add_portfolio_holding(
                        ticker_input, 
                        company_name, 
                        shares_input,
                        purchase_price=target_price if target_price > 0 else None,
                        purchase_date=None,
                        sell_price=None,
                        sell_date=None,
                        is_watchlist=1,
                        sector=sector,
                        notes=notes
                    )
                    
                    if success:
                        st.success(f"Added {ticker_input} to your watchlist!")
                        st.rerun()
                    else:
                        st.error("Failed to add to watchlist. Please try again.")
                except Exception as e:
                    st.error(f"Error: Could not add to watchlist. Please check the ticker symbol and try again. {str(e)}")
    
    # Display existing holdings for editing
    st.subheader("Edit Holdings")
    
    # Check if unlimited portfolio is available, otherwise limit to 10 stocks (free plan limit)
    has_unlimited_portfolio = is_feature_available('unlimited_portfolio')
    
    # Get filtered holdings
    all_holdings = db.get_portfolio_holdings(
        include_watchlist=st.session_state.include_watchlist,
        sector=st.session_state.selected_sector,
        filter_type=st.session_state.filter_type if st.session_state.filter_type not in ['gainers', 'losers'] else None
    )
    
    # Apply portfolio limit for free tier
    if not has_unlimited_portfolio and len(all_holdings) > 10:
        holdings = all_holdings[:10]
        display_feature_teaser('unlimited_portfolio')
    else:
        holdings = all_holdings
    
    if not holdings:
        st.info("No holdings match your current filters. Adjust the filters or add new holdings.")
    else:
        for holding in holdings:
            # Get status label
            status_label = ""
            if holding['is_watchlist'] == 1:
                status_label = "🔍 WATCHLIST"
            elif holding['sell_price'] and holding['sell_price'] > 0:
                status_label = "💰 SOLD"
            
            # Display holding for editing
            with st.expander(f"{holding['ticker']} - {holding['shares']} shares {status_label}"):
                with st.form(f"edit_form_{holding['id']}"):
                    is_watchlist = holding['is_watchlist'] == 1
                    is_sold = holding['sell_price'] is not None and holding['sell_price'] > 0
                    
                    shares = st.number_input(
                        "Shares", 
                        min_value=0.01, 
                        value=float(holding['shares']), 
                        key=f"shares_{holding['id']}"
                    )
                    
                    # Different UI for watchlist vs regular holdings
                    if is_watchlist:
                        price = st.number_input(
                            "Target Price ($)", 
                            min_value=0.0, 
                            value=float(holding['purchase_price']) if holding['purchase_price'] else 0.0, 
                            key=f"price_{holding['id']}"
                        )
                        date = None
                    else:
                        price = st.number_input(
                            "Purchase Price ($)", 
                            min_value=0.0, 
                            value=float(holding['purchase_price']) if holding['purchase_price'] else 0.0, 
                            key=f"price_{holding['id']}"
                        )
                        
                        date = st.date_input(
                            "Purchase Date", 
                            value=datetime.strptime(holding['purchase_date'], '%Y-%m-%d') if holding['purchase_date'] else datetime.today(),
                            key=f"date_{holding['id']}"
                        )
                    
                    # For sold positions, show sell information
                    if is_sold:
                        sell_price = st.number_input(
                            "Sell Price ($)", 
                            min_value=0.0, 
                            value=float(holding['sell_price']), 
                            key=f"sell_price_{holding['id']}"
                        )
                        
                        sell_date = st.date_input(
                            "Sell Date", 
                            value=datetime.strptime(holding['sell_date'], '%Y-%m-%d') if holding['sell_date'] else datetime.today(),
                            key=f"sell_date_{holding['id']}"
                        )
                    else:
                        sell_price = None
                        sell_date = None
                    
                    # Sector input
                    sector = st.text_input(
                        "Sector",
                        value=holding['sector'] if holding['sector'] else "",
                        key=f"sector_{holding['id']}"
                    )
                    
                    notes = st.text_area(
                        "Notes", 
                        value=holding['notes'] if holding['notes'] else "",
                        key=f"notes_{holding['id']}"
                    )
                    
                    # For watchlist items, add convert option
                    if is_watchlist:
                        convert_watchlist = st.checkbox("Convert to portfolio position", key=f"convert_{holding['id']}")
                    else:
                        convert_watchlist = False
                    
                    # For active positions, add mark as sold option
                    if not is_watchlist and not is_sold:
                        mark_as_sold = st.checkbox("Mark as sold", key=f"sell_{holding['id']}")
                        if mark_as_sold:
                            sell_price = st.number_input(
                                "Sell Price ($)", 
                                min_value=0.0, 
                                value=0.0, 
                                key=f"new_sell_price_{holding['id']}"
                            )
                            
                            sell_date = st.date_input(
                                "Sell Date", 
                                value=datetime.today(),
                                key=f"new_sell_date_{holding['id']}"
                            )
                    else:
                        mark_as_sold = False
                    
                    # Use side-by-side buttons without columns (to avoid nesting columns)
                    update_col, delete_col = st.columns(2)
                    update = update_col.form_submit_button("Update")
                    delete = delete_col.form_submit_button("Delete", type="primary")
                    
                    if update:
                        # If converting from watchlist to portfolio
                        if is_watchlist and convert_watchlist:
                            # Need purchase date for portfolio position
                            purchase_date = datetime.today().strftime('%Y-%m-%d')
                            
                            success = db.update_portfolio_holding(
                                holding['id'],
                                shares,
                                price if price > 0 else None,
                                purchase_date,
                                sell_price=None,
                                sell_date=None,
                                is_watchlist=0,  # Convert to regular position
                                sector=sector if sector else None,
                                notes=notes
                            )
                        # If marking as sold
                        elif not is_watchlist and not is_sold and mark_as_sold:
                            success = db.update_portfolio_holding(
                                holding['id'],
                                shares,
                                price if price > 0 else None,
                                date.strftime('%Y-%m-%d') if date else None,
                                sell_price=sell_price if sell_price and sell_price > 0 else None,
                                sell_date=sell_date.strftime('%Y-%m-%d') if sell_date else None,
                                is_watchlist=0,
                                sector=sector if sector else None,
                                notes=notes
                            )
                        # Regular update
                        else:
                            success = db.update_portfolio_holding(
                                holding['id'],
                                shares,
                                price if price > 0 else None,
                                date.strftime('%Y-%m-%d') if date else None,
                                sell_price=sell_price if sell_price and sell_price > 0 else None,
                                sell_date=sell_date.strftime('%Y-%m-%d') if sell_date else None,
                                is_watchlist=1 if is_watchlist else 0,
                                sector=sector if sector else None,
                                notes=notes
                            )
                        
                        if success:
                            st.success("Holding updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update holding.")
                    
                    if delete:
                        if db.remove_portfolio_holding(holding['id']):
                            st.success("Holding deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete holding.")

# COLUMN 2: Portfolio Overview
with col2:
    # Get portfolio data with filters
    holdings = db.get_portfolio_holdings(
        include_watchlist=st.session_state.include_watchlist,
        sector=st.session_state.selected_sector,
        filter_type=st.session_state.filter_type if st.session_state.filter_type not in ['gainers', 'losers'] else None
    )
    
    # Calculate portfolio performance
    df, total_value, total_profit_loss, total_profit_loss_percent, avg_return_pct, total_realized_gain = calculate_portfolio_performance(holdings)
    
    # Apply gainers/losers filter after getting data
    if st.session_state.filter_type == 'gainers' and not df.empty:
        # Filter to only include positions with positive returns
        df = df[df['Profit/Loss'].apply(lambda x: isinstance(x, (int, float)) and x > 0)]
    elif st.session_state.filter_type == 'losers' and not df.empty:
        # Filter to only include positions with negative returns
        df = df[df['Profit/Loss'].apply(lambda x: isinstance(x, (int, float)) and x < 0)]
    
    if df.empty:
        st.info("Add stocks to your portfolio to see your performance data here.")
    else:
        # Portfolio summary metrics
        st.subheader("Portfolio Summary")
        
        # Create metrics rows
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("Total Portfolio Value", f"${total_value:.2f}")
        
        with metric_col2:
            delta_color = "normal" if total_profit_loss >= 0 else "inverse"
            st.metric("Unrealized Profit/Loss", f"${total_profit_loss:.2f}", f"{total_profit_loss_percent:.2f}%", delta_color=delta_color)
        
        with metric_col3:
            st.metric("Number of Holdings", len(df))
        
        # Second row of metrics
        metric2_col1, metric2_col2, metric2_col3 = st.columns(3)
        
        with metric2_col1:
            st.metric("Realized Gains", f"${total_realized_gain:.2f}")
        
        with metric2_col2:
            avg_return_color = "normal" if avg_return_pct >= 0 else "inverse"
            st.metric("Average Return", f"{avg_return_pct:.2f}%", delta_color=avg_return_color)
        
        with metric2_col3:
            # Count holdings by status
            active_count = len([h for h in df.to_dict('records') if h['Status'] == 'Active'])
            watchlist_count = len([h for h in df.to_dict('records') if h['Status'] == 'Watchlist'])
            sold_count = len([h for h in df.to_dict('records') if h['Status'] == 'Sold'])
            
            status_text = f"Active: {active_count}"
            if watchlist_count > 0:
                status_text += f" | Watch: {watchlist_count}"
            if sold_count > 0:
                status_text += f" | Sold: {sold_count}"
                
            st.metric("Holdings by Status", status_text)
        
        # Show tabs for different views
        overview_tab, allocation_tab, details_tab = st.tabs(["Overview", "Allocation", "Details"])
        
        with overview_tab:
            # Show allocations by ticker
            st.subheader("Portfolio Breakdown")
            
            # Create visualization based on holding status
            df_active = df[df['Status'] == 'Active'].copy() if 'Status' in df.columns else df.copy()
            if not df_active.empty:
                # Create stacked bar chart showing active holdings
                fig_breakdown = px.bar(
                    df_active,
                    x="Ticker",
                    y="Current Value",
                    color="Profit/Loss %",
                    color_continuous_scale=[(0, "red"), (0.5, "yellow"), (1, "green")],
                    labels={"Current Value": "Value ($)", "Ticker": "Stock Symbol"},
                    title="Active Holdings Breakdown",
                    hover_data=["Company", "Shares", "Purchase Price", "Current Price", "Profit/Loss"]
                )
                
                fig_breakdown.update_layout(
                    xaxis_title="Stock",
                    yaxis_title="Value ($)",
                    coloraxis_colorbar_title="Return %"
                )
                
                st.plotly_chart(fig_breakdown, use_container_width=True)
            else:
                st.info("No active holdings to display.")
        
        with allocation_tab:
            # View allocations by different dimensions
            alloc_type = st.radio("Allocation View", ["By Stock", "By Sector"], horizontal=True)
            
            if alloc_type == "By Stock":
                # Filter to exclude watchlist items for value allocation
                df_value = df[df['Is Watchlist'] == False].copy() if 'Is Watchlist' in df.columns else df.copy()
                
                if not df_value.empty:
                    # Create pie chart by stock
                    fig_pie = px.pie(
                        df_value, 
                        values='Current Value', 
                        names='Ticker',
                        title="Portfolio Allocation by Stock",
                        hover_data=['Company', 'Shares', 'Profit/Loss %', 'Status'],
                        labels={'Current Value': 'Value ($)'}
                    )
                    
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No holdings data available for stock allocation view.")
            else:
                # Filter to exclude watchlist items for sector allocation
                df_sector = df[(df['Is Watchlist'] == False) & (df['Sector'].notna())].copy() if 'Is Watchlist' in df.columns else df.copy()
                
                if not df_sector.empty and 'Sector' in df_sector.columns:
                    # Group by sector
                    sector_data = df_sector.groupby('Sector')['Current Value'].sum().reset_index()
                    
                    # Create pie chart by sector
                    fig_sector = px.pie(
                        sector_data, 
                        values='Current Value', 
                        names='Sector',
                        title="Portfolio Allocation by Sector",
                        labels={'Current Value': 'Value ($)'}
                    )
                    
                    fig_sector.update_traces(textposition='inside', textinfo='percent+label')
                    
                    st.plotly_chart(fig_sector, use_container_width=True)
                else:
                    st.info("No sector data available. Add sector information to your holdings.")
        
        with details_tab:
            # Select view type
            view_type = st.radio("View Type", ["Active Holdings", "Watchlist", "Sold Positions", "All Holdings"], horizontal=True)
            
            if view_type == "Active Holdings":
                display_df = df[df['Status'] == 'Active'].copy() if 'Status' in df.columns else df.copy()
                display_cols = ['Ticker', 'Company', 'Sector', 'Shares', 'Purchase Price', 'Current Price', 
                                'Current Value', 'Profit/Loss', 'Profit/Loss %', 'Days Held']
            elif view_type == "Watchlist":
                display_df = df[df['Status'] == 'Watchlist'].copy() if 'Status' in df.columns else pd.DataFrame()
                display_cols = ['Ticker', 'Company', 'Sector', 'Shares', 'Purchase Price', 'Current Price', 
                                'Current Value', 'Notes']
            elif view_type == "Sold Positions":
                display_df = df[df['Status'] == 'Sold'].copy() if 'Status' in df.columns else pd.DataFrame()
                display_cols = ['Ticker', 'Company', 'Sector', 'Shares', 'Purchase Price', 'Sell Price', 
                                'Realized Gain', 'Days Held', 'Sell Date']
            else:  # All Holdings
                display_df = df.copy()
                display_cols = ['Ticker', 'Company', 'Status', 'Shares', 'Purchase Price', 'Current Price', 
                                'Current Value', 'Profit/Loss', 'Profit/Loss %']
            
            # Filter to only include available columns
            display_cols = [col for col in display_cols if col in display_df.columns]
            
            if not display_df.empty:
                # Format the dataframe for display
                format_df = display_df[display_cols].copy()
                
                # Reformat numeric columns for display
                if 'Current Value' in format_df.columns:
                    format_df['Current Value'] = format_df['Current Value'].apply(lambda x: f"${x:.2f}" if isinstance(x, (int, float)) else x)
                
                if 'Profit/Loss' in format_df.columns:
                    format_df['Profit/Loss'] = format_df['Profit/Loss'].apply(lambda x: f"${x:.2f}" if isinstance(x, (int, float)) else x)
                
                if 'Realized Gain' in format_df.columns:
                    format_df['Realized Gain'] = format_df['Realized Gain'].apply(lambda x: f"${x:.2f}" if isinstance(x, (int, float)) else x)
                
                st.dataframe(format_df, use_container_width=True)
            else:
                st.info(f"No data available for '{view_type}' view.")
        
        # Export options
        st.subheader("Export Portfolio Data")
        
        # Convert DataFrame to CSV
        csv = df.to_csv(index=False).encode('utf-8')
        
        # Download button
        st.download_button(
            label="Download Portfolio Data (CSV)",
            data=csv,
            file_name=f"portfolio_data_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.caption("""
**Disclaimer:** This portfolio tracker is for informational purposes only and does not constitute investment advice. 
Portfolio values are based on current market prices and may not reflect actual trading opportunities or market conditions.
Always consult with a financial advisor before making investment decisions.
""")