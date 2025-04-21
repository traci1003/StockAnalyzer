import sqlite3
import os
from datetime import datetime

# Create the data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Database connection
DB_PATH = 'data/stock_dashboard.db'

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create favorite_stocks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorite_stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL UNIQUE,
        company_name TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create search_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create user_preferences table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        id INTEGER PRIMARY KEY,
        theme TEXT DEFAULT 'Light',
        default_timeframe TEXT DEFAULT '1 Year',
        show_moving_averages INTEGER DEFAULT 1,
        show_rsi INTEGER DEFAULT 0,
        show_bollinger INTEGER DEFAULT 0,
        show_macd INTEGER DEFAULT 0,
        risk_profile TEXT DEFAULT 'Moderate',
        investment_horizon TEXT DEFAULT 'Medium-term (1-5 years)',
        investment_goals TEXT DEFAULT 'Balanced Growth',
        prefer_dividends INTEGER DEFAULT 0,
        esg_focus INTEGER DEFAULT 0,
        tax_efficiency INTEGER DEFAULT 0,
        international_exposure INTEGER DEFAULT 0,
        sector_preferences TEXT DEFAULT '[]'
    )
    ''')
    
    # Create portfolio_holdings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS portfolio_holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        company_name TEXT,
        shares REAL NOT NULL,
        purchase_price REAL,
        purchase_date TEXT,
        sell_price REAL,
        sell_date TEXT,
        is_watchlist INTEGER DEFAULT 0,
        sector TEXT,
        notes TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create price alerts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS price_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        target_price REAL NOT NULL,
        is_above INTEGER NOT NULL,
        is_active INTEGER DEFAULT 1,
        is_triggered INTEGER DEFAULT 0,
        notification_sent INTEGER DEFAULT 0,
        phone_number TEXT,
        email TEXT,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_triggered TIMESTAMP
    )
    ''')
    
    # Insert default preferences if table is empty
    cursor.execute('SELECT COUNT(*) FROM user_preferences')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO user_preferences (id, theme, default_timeframe, show_moving_averages, 
                                      show_rsi, show_bollinger, show_macd)
        VALUES (1, 'Light', '1 Year', 1, 0, 0, 0)
        ''')
    
    conn.commit()
    conn.close()

# Favorite stocks functions
def add_favorite_stock(ticker, company_name):
    """Add a stock to favorites"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO favorite_stocks (ticker, company_name) VALUES (?, ?)',
            (ticker.upper(), company_name)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # Stock already exists in favorites
        success = False
    finally:
        conn.close()
    return success

def remove_favorite_stock(ticker):
    """Remove a stock from favorites"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM favorite_stocks WHERE ticker = ?', (ticker.upper(),))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_favorite_stocks():
    """Get all favorite stocks"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM favorite_stocks ORDER BY company_name')
    favorites = cursor.fetchall()
    conn.close()
    return favorites

def is_favorite_stock(ticker):
    """Check if a stock is in favorites"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM favorite_stocks WHERE ticker = ?', (ticker.upper(),))
    result = cursor.fetchone() is not None
    conn.close()
    return result

# Search history functions
def add_search_history(ticker):
    """Add a ticker search to history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO search_history (ticker, timestamp) VALUES (?, ?)',
        (ticker.upper(), datetime.now())
    )
    conn.commit()
    conn.close()

def get_search_history(limit=10):
    """Get recent search history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT ticker, COUNT(*) as count, MAX(timestamp) as last_search FROM search_history GROUP BY ticker ORDER BY last_search DESC LIMIT ?',
        (limit,)
    )
    history = cursor.fetchall()
    conn.close()
    return history

def clear_search_history():
    """Clear all search history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM search_history')
    conn.commit()
    conn.close()

# User preferences functions
def get_user_preferences():
    """Get user preferences"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_preferences WHERE id = 1')
    preferences = dict(cursor.fetchone())
    conn.close()
    return preferences

def update_user_preferences(preferences):
    """Update user preferences"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current preferences first
    current_prefs = get_user_preferences()
    
    # Update with new values while keeping existing ones if not provided
    for key in preferences:
        current_prefs[key] = preferences[key]
    
    # Special handling for sector_preferences as it's stored as a string
    if 'sector_preferences' in preferences and isinstance(preferences['sector_preferences'], list):
        import json
        current_prefs['sector_preferences'] = json.dumps(preferences['sector_preferences'])
    
    # Update the database
    cursor.execute('''
    UPDATE user_preferences SET 
        theme = ?,
        default_timeframe = ?,
        show_moving_averages = ?,
        show_rsi = ?,
        show_bollinger = ?,
        show_macd = ?,
        risk_profile = ?,
        investment_horizon = ?,
        investment_goals = ?,
        prefer_dividends = ?,
        esg_focus = ?,
        tax_efficiency = ?,
        international_exposure = ?,
        sector_preferences = ?
    WHERE id = 1
    ''', (
        current_prefs.get('theme', 'Light'),
        current_prefs.get('default_timeframe', '1 Year'),
        current_prefs.get('show_moving_averages', 1),
        current_prefs.get('show_rsi', 0),
        current_prefs.get('show_bollinger', 0),
        current_prefs.get('show_macd', 0),
        current_prefs.get('risk_profile', 'Moderate'),
        current_prefs.get('investment_horizon', 'Medium-term (1-5 years)'),
        current_prefs.get('investment_goals', 'Balanced Growth'),
        current_prefs.get('prefer_dividends', 0),
        current_prefs.get('esg_focus', 0),
        current_prefs.get('tax_efficiency', 0),
        current_prefs.get('international_exposure', 0),
        current_prefs.get('sector_preferences', '[]')
    ))
    conn.commit()
    conn.close()

# Portfolio functions
def add_portfolio_holding(ticker, company_name, shares, purchase_price=None, purchase_date=None, 
                     sell_price=None, sell_date=None, is_watchlist=0, sector=None, notes=None):
    """Add a stock to portfolio"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO portfolio_holdings 
               (ticker, company_name, shares, purchase_price, purchase_date,
                sell_price, sell_date, is_watchlist, sector, notes) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (ticker.upper(), company_name, shares, purchase_price, purchase_date,
             sell_price, sell_date, is_watchlist, sector, notes)
        )
        conn.commit()
        success = True
        holding_id = cursor.lastrowid
    except Exception as e:
        success = False
        holding_id = None
    finally:
        conn.close()
    return success, holding_id

def update_portfolio_holding(holding_id, shares, purchase_price=None, purchase_date=None, 
                            sell_price=None, sell_date=None, is_watchlist=None, sector=None, notes=None):
    """Update a portfolio holding"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First get the current values to avoid overwriting with None
    current = get_portfolio_holding(holding_id)
    if not current:
        return False
    
    # Use current values if new ones aren't provided
    if is_watchlist is None:
        is_watchlist = current['is_watchlist']
    if sector is None:
        sector = current['sector']
    
    try:
        cursor.execute(
            '''UPDATE portfolio_holdings 
               SET shares = ?, purchase_price = ?, purchase_date = ?,
                   sell_price = ?, sell_date = ?, is_watchlist = ?, sector = ?, notes = ?
               WHERE id = ?''',
            (shares, purchase_price, purchase_date, 
             sell_price, sell_date, is_watchlist, sector, notes, holding_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
    except Exception as e:
        success = False
    finally:
        conn.close()
    return success

def remove_portfolio_holding(holding_id):
    """Remove a stock from portfolio"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM portfolio_holdings WHERE id = ?', (holding_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_portfolio_holdings(include_watchlist=True, sector=None, filter_type=None):
    """
    Get portfolio holdings with filters
    
    Parameters:
    - include_watchlist: Whether to include watchlist items (default: True)
    - sector: Filter by sector (default: None for all sectors)
    - filter_type: 'active', 'sold', 'gainers', 'losers', or None for all holdings
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM portfolio_holdings WHERE 1=1'
    params = []
    
    # Watchlist filter
    if not include_watchlist:
        query += ' AND is_watchlist = 0'
    
    # Sector filter
    if sector:
        query += ' AND sector = ?'
        params.append(sector)
    
    # Type filter
    if filter_type == 'active':
        query += ' AND (sell_price IS NULL OR sell_price = 0)'
    elif filter_type == 'sold':
        query += ' AND sell_price IS NOT NULL AND sell_price > 0'
    
    # We can't apply gainers/losers filter here since we need current prices
    # This will be handled after retrieving the data
    
    query += ' ORDER BY ticker'
    
    cursor.execute(query, params)
    holdings = cursor.fetchall()
    conn.close()
    return holdings

def get_portfolio_holding(holding_id):
    """Get a specific portfolio holding"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM portfolio_holdings WHERE id = ?', (holding_id,))
    holding = cursor.fetchone()
    conn.close()
    return holding

def get_ticker_holdings(ticker):
    """Get all holdings for a specific ticker"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM portfolio_holdings WHERE ticker = ? ORDER BY purchase_date', (ticker.upper(),))
    holdings = cursor.fetchall()
    conn.close()
    return holdings

def get_available_sectors():
    """Get list of all sectors in the portfolio"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT sector FROM portfolio_holdings WHERE sector IS NOT NULL ORDER BY sector')
    sectors = [row['sector'] for row in cursor.fetchall()]
    conn.close()
    return sectors

# Price Alert functions
def add_price_alert(ticker, target_price, is_above, phone_number=None, email=None):
    """
    Add a new price alert
    
    Parameters:
    - ticker: Stock ticker symbol
    - target_price: Target price for alert
    - is_above: 1 if alert when price goes above target, 0 for below
    - phone_number: Optional phone number for SMS alerts
    - email: Optional email for email alerts
    
    Returns:
    - ID of the new alert or None if failed
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO price_alerts
               (ticker, target_price, is_above, phone_number, email)
               VALUES (?, ?, ?, ?, ?)''',
            (ticker.upper(), target_price, is_above, phone_number, email)
        )
        conn.commit()
        alert_id = cursor.lastrowid
    except Exception as e:
        alert_id = None
    finally:
        conn.close()
    return alert_id

def get_price_alerts(ticker=None, active_only=True):
    """
    Get price alerts, optionally filtered by ticker
    
    Parameters:
    - ticker: Optional ticker to filter alerts (if None, returns all alerts)
    - active_only: If True, returns only active alerts
    
    Returns:
    - List of price alert dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM price_alerts WHERE 1=1'
    params = []
    
    if ticker:
        query += ' AND ticker = ?'
        params.append(ticker.upper())
    
    if active_only:
        query += ' AND is_active = 1'
    
    query += ' ORDER BY date_created DESC'
    
    cursor.execute(query, params)
    alerts = cursor.fetchall()
    conn.close()
    return alerts

def update_price_alert(alert_id, target_price=None, is_above=None, is_active=None):
    """
    Update a price alert
    
    Parameters:
    - alert_id: ID of the alert to update
    - target_price: New target price (if None, not updated)
    - is_above: New is_above value (if None, not updated)
    - is_active: New is_active value (if None, not updated)
    
    Returns:
    - True if updated successfully, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current values
    cursor.execute('SELECT * FROM price_alerts WHERE id = ?', (alert_id,))
    alert = cursor.fetchone()
    if not alert:
        conn.close()
        return False
    
    # Update with new values if provided
    updated_target = target_price if target_price is not None else alert['target_price']
    updated_is_above = is_above if is_above is not None else alert['is_above']
    updated_is_active = is_active if is_active is not None else alert['is_active']
    
    try:
        cursor.execute(
            '''UPDATE price_alerts 
               SET target_price = ?, is_above = ?, is_active = ?
               WHERE id = ?''',
            (updated_target, updated_is_above, updated_is_active, alert_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
    except Exception as e:
        success = False
    finally:
        conn.close()
    return success

def delete_price_alert(alert_id):
    """
    Delete a price alert
    
    Parameters:
    - alert_id: ID of the alert to delete
    
    Returns:
    - True if deleted successfully, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM price_alerts WHERE id = ?', (alert_id,))
        conn.commit()
        success = cursor.rowcount > 0
    except Exception as e:
        success = False
    finally:
        conn.close()
    return success

def delete_all_triggered_alerts():
    """
    Delete all triggered price alerts
    
    Returns:
    - Number of alerts deleted
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM price_alerts WHERE is_triggered = 1')
        deleted_count = cursor.rowcount
        conn.commit()
    except Exception as e:
        deleted_count = 0
    finally:
        conn.close()
    return deleted_count

def mark_alert_triggered(alert_id, notification_sent=1):
    """
    Mark a price alert as triggered
    
    Parameters:
    - alert_id: ID of the alert to mark
    - notification_sent: Whether notification was sent
    
    Returns:
    - True if updated successfully, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''UPDATE price_alerts 
               SET is_triggered = 1, 
                   notification_sent = ?,
                   date_triggered = CURRENT_TIMESTAMP
               WHERE id = ?''',
            (notification_sent, alert_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
    except Exception as e:
        success = False
    finally:
        conn.close()
    return success

def get_pending_alerts():
    """
    Get active, non-triggered alerts that need to be checked
    
    Returns:
    - List of alert dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT * FROM price_alerts 
           WHERE is_active = 1 AND is_triggered = 0
           ORDER BY ticker, target_price'''
    )
    alerts = cursor.fetchall()
    conn.close()
    return alerts

# Achievements and gamification functions
def init_gamification_tables():
    """Initialize tables needed for gamification features"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create achievements table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        achievement_id TEXT NOT NULL,
        date_earned TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create user_stats table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY,
        total_points INTEGER DEFAULT 0,
        stocks_analyzed INTEGER DEFAULT 0,
        sentiment_checks INTEGER DEFAULT 0,
        ai_screener_uses INTEGER DEFAULT 0,
        stocks_favorited INTEGER DEFAULT 0,
        portfolio_additions INTEGER DEFAULT 0,
        app_opens INTEGER DEFAULT 0,
        consecutive_days INTEGER DEFAULT 0,
        last_visit_date TEXT,
        sectors_in_portfolio TEXT DEFAULT '[]',
        highest_sentiment_score REAL DEFAULT 0,
        lowest_sentiment_score REAL DEFAULT 0,
        search_history_count INTEGER DEFAULT 0,
        date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Insert default user stats if table is empty
    cursor.execute('SELECT COUNT(*) FROM user_stats')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO user_stats (
            id, total_points, stocks_analyzed, sentiment_checks, ai_screener_uses,
            stocks_favorited, portfolio_additions, app_opens, consecutive_days,
            last_visit_date, sectors_in_portfolio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            1, 0, 0, 0, 0, 0, 0, 0, 0, 
            datetime.now().strftime("%Y-%m-%d"), '[]'
        ))
    
    conn.commit()
    conn.close()

def add_achievement(achievement_id):
    """Add an achievement to the user's record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO achievements (achievement_id) VALUES (?)',
            (achievement_id,)
        )
        conn.commit()
        success = True
    except Exception as e:
        success = False
    finally:
        conn.close()
    
    return success

def get_achievements():
    """Get all earned achievements"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT achievement_id, date_earned FROM achievements ORDER BY date_earned DESC')
    achievements = cursor.fetchall()
    
    conn.close()
    return achievements

def get_user_stats():
    """Get user stats for gamification"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user_stats WHERE id = 1')
    stats = cursor.fetchone()
    
    if stats:
        # Convert JSON strings to Python objects
        import json
        stats_dict = dict(stats)
        
        # Convert sectors JSON string to list
        try:
            stats_dict['sectors_in_portfolio'] = json.loads(stats_dict['sectors_in_portfolio'])
        except:
            stats_dict['sectors_in_portfolio'] = []
        
        # Get achievements and add to stats
        cursor.execute('SELECT achievement_id FROM achievements')
        achievement_rows = cursor.fetchall()
        stats_dict['achievements'] = [row['achievement_id'] for row in achievement_rows]
        
        conn.close()
        return stats_dict
    else:
        conn.close()
        return None

def update_user_stats(stats):
    """Update user stats for gamification"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert lists to JSON strings
    import json
    if 'sectors_in_portfolio' in stats and isinstance(stats['sectors_in_portfolio'], list):
        sectors_json = json.dumps(stats['sectors_in_portfolio'])
    else:
        sectors_json = '[]'
    
    # Remove achievements from stats as they are stored in a separate table
    stats_copy = stats.copy()
    if 'achievements' in stats_copy:
        del stats_copy['achievements']
    
    try:
        cursor.execute('''
        UPDATE user_stats SET
            total_points = ?,
            stocks_analyzed = ?,
            sentiment_checks = ?,
            ai_screener_uses = ?,
            stocks_favorited = ?,
            portfolio_additions = ?,
            app_opens = ?,
            consecutive_days = ?,
            last_visit_date = ?,
            sectors_in_portfolio = ?,
            highest_sentiment_score = ?,
            lowest_sentiment_score = ?,
            search_history_count = ?,
            date_updated = ?
        WHERE id = 1
        ''', (
            stats_copy.get('total_points', 0),
            stats_copy.get('stocks_analyzed', 0),
            stats_copy.get('sentiment_checks', 0),
            stats_copy.get('ai_screener_uses', 0),
            stats_copy.get('stocks_favorited', 0),
            stats_copy.get('portfolio_additions', 0),
            stats_copy.get('app_opens', 0),
            stats_copy.get('consecutive_days', 0),
            stats_copy.get('last_visit_date', datetime.now().strftime("%Y-%m-%d")),
            sectors_json,
            stats_copy.get('highest_sentiment_score', 0),
            stats_copy.get('lowest_sentiment_score', 0),
            stats_copy.get('search_history_count', 0),
            datetime.now()
        ))
        conn.commit()
        success = cursor.rowcount > 0
    except Exception as e:
        success = False
    finally:
        conn.close()
    
    return success

# Initialize the database
init_db()
init_gamification_tables()