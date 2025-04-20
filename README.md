# 💹 AI-Powered Investment Dashboard

A full-stack, AI-enhanced stock research platform that combines intelligent stock screening, real-time sentiment analysis, gamification, and premium account features — all built using **Streamlit** + **OpenAI**.

> ⚡ Built with love by [Traci Davis](https://www.linkedin.com/in/traci-davis-23502235a/)  
> 💸 Goal: Scale this to a $50M fintech startup

---

## 🚀 Features

### 🤖 AI Stock Screener
- Search stocks with natural language:  
  _“Show me tech stocks under $50 with strong growth”_
- AI-driven results with detailed financial metrics and performance charts

### 🧠 Sentiment Dashboard
- Real-time market sentiment pulled from live news headlines
- AI-powered analysis to flag bullish, bearish, or neutral trends
- Interactive pie chart and news cards with summary reasoning

### 🏆 Gamification System
- Earn badges like “Portfolio Pioneer” and “Sharp Eye”
- Track activity metrics: stocks analyzed, streaks, favorites added
- Global leaderboard for top users

### 🔒 Premium Account System
- Unlock advanced AI recommendations, full sentiment breakdowns, and exclusive market data
- Built using `localStorage` for persistent session tracking
- In-app plan switching & premium badge visuals

---

## 🛠 Tech Stack

- **Frontend:** Streamlit (custom components, layout tweaks)
- **Backend:** Python + OpenAI API + yfinance
- **State Management:** `localStorage`, `st.session_state`
- **Charts:** matplotlib, Plotly
- **Premium Logic:** Modular setup via `monetization.py`

---



## ⚙️ Local Development

```bash
git clone https://github.com/traci1003/your-repo-name.git
cd your-repo-name
pip install -r requirements.txt
streamlit run app.py
## 🚀 Live Demo

👉 Try the app here: [https://your-app-url.replit.app](https://your-app-url.replit.app)
## 📸 Screenshots



```bash
git clone https://github.com/traci1003/StockAnalyzer.git
cd StockAnalyzer
pip install -r requirements.txt
streamlit run main.py

