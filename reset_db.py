import sqlite3
import os

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

# Connect to the database
conn = sqlite3.connect('data/stock_dashboard.db')
cursor = conn.cursor()

# Drop the portfolio_holdings table if it exists
cursor.execute("DROP TABLE IF EXISTS portfolio_holdings")

# Create the portfolio_holdings table with the full schema
cursor.execute('''
CREATE TABLE portfolio_holdings (
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

# Commit changes and close the connection
conn.commit()
conn.close()

print("Portfolio holdings table has been reset with the correct schema.")