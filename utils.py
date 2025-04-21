import pandas as pd
import numpy as np

def calculate_moving_averages(data):
    """
    Calculate simple moving averages
    """
    df = data.copy()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    return df

def calculate_rsi(data, window=14):
    """
    Calculate Relative Strength Index
    """
    df = data.copy()
    delta = df['Close'].diff()
    gain = delta.mask(delta < 0, 0)
    loss = -delta.mask(delta > 0, 0)
    
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def calculate_bollinger_bands(data, window=20, num_std=2):
    """
    Calculate Bollinger Bands
    """
    df = data.copy()
    df['middle_band'] = df['Close'].rolling(window=window).mean()
    df['std'] = df['Close'].rolling(window=window).std()
    df['upper_band'] = df['middle_band'] + (df['std'] * num_std)
    df['lower_band'] = df['middle_band'] - (df['std'] * num_std)
    
    return df

def calculate_macd(data, fast=12, slow=26, signal=9):
    """
    Calculate MACD (Moving Average Convergence Divergence)
    """
    df = data.copy()
    df['ema_fast'] = df['Close'].ewm(span=fast, min_periods=fast).mean()
    df['ema_slow'] = df['Close'].ewm(span=slow, min_periods=slow).mean()
    df['macd'] = df['ema_fast'] - df['ema_slow']
    df['signal'] = df['macd'].ewm(span=signal, min_periods=signal).mean()
    df['histogram'] = df['macd'] - df['signal']
    
    return df
