import streamlit as st
from datetime import datetime, timedelta
import json
import os

# Define premium feature plans and their descriptions
PREMIUM_PLANS = {
    "free": {
        "name": "Free",
        "description": "Basic stock analysis and portfolio tracking",
        "price": "$0/month",
        "features": [
            "Basic stock analysis",
            "Portfolio tracking (up to 10 stocks)",
            "Daily price alerts (up to 3)",
            "Basic technical indicators"
        ],
        "color": "#9E9E9E"  # Grey
    },
    "basic": {
        "name": "Basic",
        "description": "Enhanced analysis and more portfolio features",
        "price": "$9.99/month",
        "features": [
            "All Free features",
            "Unlimited portfolio stocks",
            "Daily price alerts (up to 10)",
            "Advanced technical indicators",
            "Portfolio performance reports",
            "No advertisements"
        ],
        "color": "#4CAF50"  # Green
    },
    "pro": {
        "name": "Pro",
        "description": "Advanced AI-powered financial insights",
        "price": "$19.99/month",
        "features": [
            "All Basic features",
            "Unlimited price alerts",
            "AI-powered portfolio recommendations",
            "Advanced sentiment analysis",
            "Market prediction indicators",
            "Custom strategy backtesting",
            "Priority customer support"
        ],
        "color": "#2196F3"  # Blue
    },
    "enterprise": {
        "name": "Enterprise",
        "description": "Professional-grade investing tools",
        "price": "$49.99/month",
        "features": [
            "All Pro features",
            "Real-time data feeds",
            "Advanced option analytics",
            "Institutional-grade research",
            "Custom API access",
            "White-label reporting",
            "Dedicated account manager"
        ],
        "color": "#9C27B0"  # Purple
    }
}

# Define premium features and which plans they belong to
PREMIUM_FEATURES = {
    "unlimited_portfolio": {
        "name": "Unlimited Portfolio Stocks",
        "description": "Track and manage an unlimited number of stocks in your portfolio",
        "plans": ["basic", "pro", "enterprise"],
        "teaser_message": "Upgrade to Basic plan to track more than 10 stocks in your portfolio!",
        "feature_id": "unlimited_portfolio",
        "learn_more_url": "#upgrade",
        "icon": "💼"
    },
    "custom_themes": {
        "name": "Custom Themes",
        "description": "Access premium theme options for your dashboard",
        "plans": ["basic", "pro", "enterprise"],
        "teaser_message": "Upgrade to Basic plan for exclusive premium themes!",
        "feature_id": "custom_themes",
        "learn_more_url": "#upgrade",
        "icon": "🎨"
    },
    "unlimited_alerts": {
        "name": "Unlimited Price Alerts",
        "description": "Create unlimited price alerts for your favorite stocks",
        "plans": ["pro", "enterprise"],
        "teaser_message": "Upgrade to Pro plan for unlimited price alerts!",
        "feature_id": "unlimited_alerts",
        "learn_more_url": "#upgrade",
        "icon": "🔔"
    },
    "ai_recommendations": {
        "name": "AI-Powered Recommendations",
        "description": "Get personalized investment recommendations powered by AI",
        "plans": ["pro", "enterprise"],
        "teaser_message": "Upgrade to Pro for AI-powered stock recommendations!",
        "feature_id": "ai_recommendations",
        "learn_more_url": "#upgrade",
        "icon": "🤖"
    },
    "advanced_technical": {
        "name": "Advanced Technical Indicators",
        "description": "Access to advanced technical indicators and custom chart tools",
        "plans": ["basic", "pro", "enterprise"],
        "teaser_message": "Upgrade to Basic plan for advanced technical indicators!",
        "feature_id": "advanced_technical",
        "learn_more_url": "#upgrade",
        "icon": "📊"
    },
    "performance_reports": {
        "name": "Portfolio Performance Reports",
        "description": "Detailed performance reports with benchmarking and analytics",
        "plans": ["basic", "pro", "enterprise"],
        "teaser_message": "Upgrade to Basic plan for detailed portfolio performance reports!",
        "feature_id": "performance_reports",
        "learn_more_url": "#upgrade",
        "icon": "📝"
    },
    "advanced_sentiment": {
        "name": "Advanced Sentiment Analysis",
        "description": "Deeper sentiment analysis with source-level detail and trends",
        "plans": ["pro", "enterprise"],
        "teaser_message": "Upgrade to Pro plan for advanced sentiment analysis!",
        "feature_id": "advanced_sentiment",
        "learn_more_url": "#upgrade",
        "icon": "📊"
    },
    "backtesting": {
        "name": "Strategy Backtesting",
        "description": "Test your investment strategies against historical data",
        "plans": ["pro", "enterprise"],
        "teaser_message": "Upgrade to Pro plan to backtest your investment strategies!",
        "feature_id": "backtesting",
        "learn_more_url": "#upgrade",
        "icon": "⏱️"
    },
    "realtime_data": {
        "name": "Real-time Market Data",
        "description": "Access to real-time market data without delays",
        "plans": ["enterprise"],
        "teaser_message": "Upgrade to Enterprise plan for real-time market data!",
        "feature_id": "realtime_data",
        "learn_more_url": "#upgrade",
        "icon": "⚡"
    }
}

# File path for storing feature impressions and clicks
DATA_DIR = "data"
IMPRESSIONS_FILE = os.path.join(DATA_DIR, "feature_impressions.json")
CLICKS_FILE = os.path.join(DATA_DIR, "feature_clicks.json")

def get_user_plan():
    """Get the current user's subscription plan - defaults to free"""
    # Look for the premium status in session state first (used for testing)
    if 'user_plan' in st.session_state:
        return st.session_state.user_plan
    
    # Check if the user is requesting a trial
    query_params = st.query_params
    if 'trial' in query_params and query_params['trial'] == 'true':
        # Start a trial
        start_trial('pro')
        # Clear the trial parameter to avoid reactivating on refresh
        cleaned_params = dict(query_params)
        if 'trial' in cleaned_params:
            del cleaned_params['trial']
        # Set the cleaned parameters
        st.query_params.update(cleaned_params)
        st.session_state.user_plan = 'pro'
        return 'pro'
    
    # Check for a premium account in localStorage
    # We'll handle the localStorage part in JavaScript
    if 'premium_status_checked' not in st.session_state:
        # Create a placeholder for the localStorage check
        st.session_state.premium_status_checked = True
        
        # Add JavaScript to check localStorage and also check for trial
        st.markdown("""
        <script>
        // Function to check premium status in localStorage
        function checkPremiumStatus() {
            // First check if there's an active trial
            const trialEndTime = localStorage.getItem('trialEndTime');
            
            if (trialEndTime) {
                // Check if trial has expired
                const now = new Date();
                const endTime = new Date(trialEndTime);
                
                if (now < endTime) {
                    // Trial is still active
                    const trialPlan = localStorage.getItem('trialPlan') || 'pro';

                    // We'll rely on reading localStorage again on refresh
                    // instead of setting URL parameters
                    window.location.reload();
                    return;
                } else {
                    // Trial has expired - remove it
                    localStorage.removeItem('trialEndTime');
                    localStorage.removeItem('trialPlan');
                }
            }
            
            // If no active trial, check for regular premium subscription
            const premiumPlan = localStorage.getItem('premiumPlan');
            if (premiumPlan) {
                // Update the JavaScript variable and reload
                // We'll read localStorage again on refresh
                window.location.reload();
            }
        }
        
        // Run on page load
        document.addEventListener('DOMContentLoaded', function() {
            checkPremiumStatus();
        });
        </script>
        """, unsafe_allow_html=True)
    
    # Check if premium_plan is in the URL parameters (set by JavaScript)
    query_params = st.query_params
    if 'premium_plan' in query_params:
        plan = query_params['premium_plan']
        if plan in PREMIUM_PLANS:
            is_trial = 'is_trial' in query_params and query_params['is_trial'] == 'true'
            plan_display = f"{plan} (Trial)" if is_trial else plan
            st.session_state.user_plan = plan
            st.session_state.is_trial = is_trial
            return plan
    
    # Default to free if no premium plan found
    st.session_state.user_plan = "free"
    st.session_state.is_trial = False
    return "free"


def start_trial(plan='pro'):
    """Start a free trial of a premium plan"""
    if plan not in PREMIUM_PLANS or plan == 'free':
        return False
        
    # Calculate end time (24 hours from now)
    trial_end = (datetime.now() + timedelta(hours=24)).isoformat()
    
    # Add JavaScript to set trial in localStorage
    st.markdown(f"""
    <script>
    // Store trial information in localStorage
    localStorage.setItem('trialEndTime', '{trial_end}');
    localStorage.setItem('trialPlan', '{plan}');
    
    // Show a welcome message
    setTimeout(function() {{
        alert('Your 24-hour trial of {PREMIUM_PLANS[plan]["name"]} has started! Enjoy all premium features until {trial_end}');
    }}, 1000);
    </script>
    """, unsafe_allow_html=True)
    
    return True

def is_feature_available(feature_id):
    """Check if a feature is available in the user's current plan"""
    user_plan = get_user_plan()
    
    if feature_id not in PREMIUM_FEATURES:
        # If feature doesn't exist in our registry, default to available
        return True
    
    feature = PREMIUM_FEATURES[feature_id]
    return user_plan in feature.get("plans", [])

def display_feature_teaser(feature_id):
    """Display a teaser/upgrade prompt for a premium feature"""
    if feature_id not in PREMIUM_FEATURES:
        return
    
    # Track impression for analytics
    track_feature_impression(feature_id)
    
    feature = PREMIUM_FEATURES[feature_id]
    icon = feature.get("icon", "🔒")
    message = feature.get("teaser_message", "Upgrade to access this premium feature!")
    
    st.info(f"{icon} {message}")
    
    # Add an upgrade button and track clicks for analytics
    if st.button(f"Learn More About {feature['name']}", key=f"learn_more_{feature_id}"):
        track_feature_click(feature_id)
        st.session_state['show_subscription_page'] = True
        # In a real app, you might redirect to a specific upgrade page
        # For now, we'll just show it on the current page
        display_subscription_plans()

def display_subscription_plans():
    """Display available subscription plans in a comparison table"""
    st.header("📈 Upgrade Your Investment Journey")
    st.write("Choose the plan that's right for you")
    
    plans = list(PREMIUM_PLANS.values())
    cols = st.columns(len(plans))
    
    # Display plan cards
    for i, plan in enumerate(plans):
        with cols[i]:
            st.markdown(f"""
            <div style="
                border: 1px solid {plan['color']}; 
                border-radius: 10px; 
                padding: 10px; 
                height: 100%;
                background-color: rgba({int(plan['color'][1:3], 16)}, {int(plan['color'][3:5], 16)}, {int(plan['color'][5:7], 16)}, 0.1);
            ">
                <h3 style="color: {plan['color']}; text-align: center;">{plan['name']}</h3>
                <h2 style="text-align: center;">{plan['price']}</h2>
                <p style="text-align: center; font-style: italic;">{plan['description']}</p>
                <hr>
                <ul>
            """, unsafe_allow_html=True)
            
            for feature in plan['features']:
                st.markdown(f"<li>{feature}</li>", unsafe_allow_html=True)
            
            st.markdown("</ul></div>", unsafe_allow_html=True)
            
            if plan['name'] != "Free":
                plan_id = plan['name'].lower()
                if st.button(f"Choose {plan['name']}", key=f"choose_{plan_id}"):
                    # Store the plan choice in session state
                    set_test_plan(plan_id)
                    
                    # Add JavaScript to store the premium plan in localStorage
                    st.markdown(f"""
                    <script>
                        // Store the plan in localStorage
                        localStorage.setItem('premiumPlan', '{plan_id}');
                        // Show a success message via JavaScript alert
                        setTimeout(function() {{
                            alert('Success! Your {plan["name"]} subscription is now active.\\n\\nThis is a demo - in a real app, this would process payment via Stripe.');
                        }}, 500);
                    </script>
                    """, unsafe_allow_html=True)
                    
                    st.success(f"Great choice! {plan['name']} plan selected. Your premium features are now active.")
            else:
                st.markdown("<div style='height: 34px;'></div>", unsafe_allow_html=True)  # Spacer

def set_test_plan(plan_name):
    """Set the user's plan for testing purposes only"""
    if plan_name in PREMIUM_PLANS:
        st.session_state.user_plan = plan_name
        # In a real app, this would update the user's subscription in a database
        st.success(f"For testing: Your plan is now set to {plan_name}.")
        st.session_state['show_subscription_page'] = False

def display_most_wanted_features():
    """Display analytics about which premium features users are most interested in"""
    # Load impression and click data from files
    impression_data = load_impression_data()
    click_data = load_click_data()
    
    # If there's no data, don't show anything
    if not impression_data and not click_data:
        return
    
    # Prepare data for display
    feature_stats = []
    for feature_id in PREMIUM_FEATURES:
        impressions = impression_data.get(feature_id, 0)
        clicks = click_data.get(feature_id, 0)
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        
        feature_stats.append({
            "feature": PREMIUM_FEATURES[feature_id]["name"],
            "impressions": impressions,
            "clicks": clicks,
            "ctr": ctr
        })
    
    # Sort by click-through rate
    feature_stats.sort(key=lambda x: x["ctr"], reverse=True)
    
    # Display the data
    st.subheader("Most Wanted Premium Features")
    st.write("Based on user interactions:")
    
    # Create a table of feature stats
    import pandas as pd
    stats_df = pd.DataFrame(feature_stats)
    stats_df.columns = ["Feature", "Impressions", "Clicks", "CTR (%)"]
    stats_df["CTR (%)"] = stats_df["CTR (%)"].round(2)
    
    st.table(stats_df)

def track_feature_impression(feature_id):
    """Track when a user sees a premium feature teaser"""
    impression_data = load_impression_data()
    
    # Increment the impression count for this feature
    if feature_id in impression_data:
        impression_data[feature_id] += 1
    else:
        impression_data[feature_id] = 1
    
    # Save the updated data
    save_impression_data(impression_data)

def track_feature_click(feature_id):
    """Track when a user clicks on a premium feature teaser"""
    click_data = load_click_data()
    
    # Increment the click count for this feature
    if feature_id in click_data:
        click_data[feature_id] += 1
    else:
        click_data[feature_id] = 1
    
    # Save the updated data
    save_click_data(click_data)

def load_impression_data():
    """Load feature impression data from file"""
    try:
        if os.path.exists(IMPRESSIONS_FILE):
            with open(IMPRESSIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading impression data: {e}")
    
    return {}

def save_impression_data(data):
    """Save feature impression data to file"""
    try:
        # Make sure the data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        
        with open(IMPRESSIONS_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Error saving impression data: {e}")

def load_click_data():
    """Load feature click data from file"""
    try:
        if os.path.exists(CLICKS_FILE):
            with open(CLICKS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading click data: {e}")
    
    return {}

def save_click_data(data):
    """Save feature click data to file"""
    try:
        # Make sure the data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        
        with open(CLICKS_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Error saving click data: {e}")

def reset_test_plan():
    """Reset the user's plan back to free (for testing)"""
    st.session_state.user_plan = "free"
    st.session_state.is_trial = False
    
    # Clear premium-related query parameters
    if 'premium_plan' in st.query_params or 'is_trial' in st.query_params:
        # Create a clean dict of current params
        cleaned_params = {}
        for k, v in st.query_params.items():
            if k not in ['premium_plan', 'is_trial']:
                cleaned_params[k] = v
        
        # Update query params to remove premium-related keys
        st.query_params.update(cleaned_params)
    
    # Add JavaScript to remove the premium plan and trial info from localStorage
    st.markdown("""
    <script>
        // Check if it's a trial
        const isTrial = localStorage.getItem('trialEndTime') !== null;
        
        // Remove trial information if present
        localStorage.removeItem('trialEndTime');
        localStorage.removeItem('trialPlan');
        
        // Remove premium plan info
        localStorage.removeItem('premiumPlan');
        
        // Show a success message
        setTimeout(function() {
            if (isTrial) {
                alert('Your premium trial has been cancelled.');
            } else {
                alert('Your premium subscription has been cancelled.');
            }
        }, 500);
        
        // Reload the page
        window.location.reload();
    </script>
    """, unsafe_allow_html=True)
    
    st.success("Your plan has been reset to Free.")