import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

from monetization import (
    display_subscription_plans,
    get_user_plan,
    reset_test_plan,
    display_most_wanted_features,
    PREMIUM_FEATURES,
    PREMIUM_PLANS
)

# Configure page
st.set_page_config(
    page_title="Premium Features",
    page_icon="⭐",
    layout="wide"
)

def main():
    st.title("⭐ Premium Features")
    
    # Get current plan
    current_plan = get_user_plan()
    plan_info = PREMIUM_PLANS.get(current_plan, PREMIUM_PLANS["free"])
    
    # Display current plan info
    st.markdown(f"""
    <div style="
        background-color: rgba({int(plan_info['color'][1:3], 16)}, {int(plan_info['color'][3:5], 16)}, {int(plan_info['color'][5:7], 16)}, 0.2);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    ">
        <h3>Your Current Plan: {plan_info['name']}</h3>
        <p>{plan_info['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Available Plans", "Account Management", "Feature Comparison", "Analytics"])
    
    with tab1:
        display_subscription_plans()
    
    # Account Management Tab
    with tab2:
        st.subheader("Account Management")
        
        # Get current plan information
        current_plan = get_user_plan()
        plan_info = PREMIUM_PLANS.get(current_plan, PREMIUM_PLANS["free"])
        
        # Display subscription details
        st.markdown("### Subscription Details")
        
        # Create a simulated subscription start date (for demo purposes)
        if current_plan != "free":
            # For premium plans, show more details
            start_date = datetime.now() - timedelta(days=14)
            renewal_date = datetime.now() + timedelta(days=16)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                **Current Plan:** {plan_info['name']}  
                **Price:** {plan_info['price']}  
                **Status:** Active  
                **Start Date:** {start_date.strftime('%B %d, %Y')}  
                **Next Renewal:** {renewal_date.strftime('%B %d, %Y')}
                """)
            
            with col2:
                # Show a premium badge with the plan's color
                st.markdown(f"""
                <div style="
                    background-color: {plan_info['color']}; 
                    color: white; 
                    padding: 10px 20px; 
                    border-radius: 15px;
                    display: inline-block;
                    font-weight: bold;
                    text-align: center;
                    margin-bottom: 15px;
                ">
                    PREMIUM {plan_info['name'].upper()}
                </div>
                """, unsafe_allow_html=True)
                
                # Add a billing history link (simulated)
                st.markdown("""
                [View Billing History](#) | [Download Invoices](#)
                """)
            
            # Payment method information
            st.markdown("### Payment Method")
            st.markdown("""
            💳 Credit Card ending in **••••4242**  
            Expires: 12/28
            """)
            
            # Add buttons for managing the subscription
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Change Plan"):
                    st.session_state['show_change_plan'] = True
            
            with col2:
                if st.button("Update Payment Method"):
                    st.info("In a real app, this would open a Stripe payment update form.")
            
            with col3:
                if st.button("Cancel Subscription"):
                    reset_test_plan()
                    st.rerun()
            
            # Plan change section (shown when the Change Plan button is clicked)
            if st.session_state.get('show_change_plan', False):
                st.markdown("---")
                st.markdown("### Change Your Plan")
                
                # Show only the plans different from the current one
                available_plans = [p for p in PREMIUM_PLANS.values() if p['name'].lower() != current_plan]
                cols = st.columns(len(available_plans))
                
                for i, plan in enumerate(available_plans):
                    with cols[i]:
                        plan_id = plan['name'].lower()
                        st.markdown(f"""
                        <div style="
                            border: 1px solid {plan['color']}; 
                            border-radius: 10px; 
                            padding: 10px; 
                            text-align: center;
                            background-color: rgba({int(plan['color'][1:3], 16)}, {int(plan['color'][3:5], 16)}, {int(plan['color'][5:7], 16)}, 0.1);
                        ">
                            <h4>{plan['name']}</h4>
                            <p>{plan['price']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"Switch to {plan['name']}", key=f"switch_{plan_id}"):
                            # Change the plan
                            st.session_state.user_plan = plan_id
                            
                            # Add JavaScript to update localStorage
                            st.markdown(f"""
                            <script>
                                localStorage.setItem('premiumPlan', '{plan_id}');
                                setTimeout(function() {{
                                    alert('Your plan has been changed to {plan["name"]}.');
                                    window.location.reload();
                                }}, 500);
                            </script>
                            """, unsafe_allow_html=True)
                            
                            st.success(f"Your plan has been changed to {plan['name']}.")
                            st.session_state['show_change_plan'] = False
        else:
            # For free plan, show upgrade prompt
            st.info("You are currently on the Free plan. Upgrade to a premium plan to access exclusive features!")
            
            if st.button("Upgrade Now"):
                st.session_state['active_tab'] = 0  # Switch to Available Plans tab
                st.rerun()
        
        # Data privacy section
        st.markdown("---")
        st.markdown("### Data & Privacy")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Data Export**")
            if st.button("Export My Data"):
                st.info("In a real app, this would prepare your data for download.")
        
        with col2:
            st.markdown("**Account Deletion**")
            if st.button("Delete My Account", type="primary", use_container_width=True):
                st.error("Account deletion is disabled in this demo. In a real app, this would permanently remove your account and data.")
        
        # Reset plan button (for testing only)
        st.markdown("---")
        st.caption("For demo purposes only:")
        if st.button("Reset to Free Plan"):
            reset_test_plan()
            st.rerun()
    
    with tab3:
        st.subheader("Feature Comparison")
        
        # Create a feature comparison table
        feature_comparison = []
        for feature_id, feature in PREMIUM_FEATURES.items():
            row = {
                "Feature": f"{feature['icon']} {feature['name']}",
                "Description": feature['description']
            }
            
            # Add columns for each plan
            for plan_id, plan in PREMIUM_PLANS.items():
                row[plan['name']] = "✅" if plan_id in feature['plans'] else "❌"
            
            feature_comparison.append(row)
        
        # Convert to DataFrame and display
        comparison_df = pd.DataFrame(feature_comparison)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # Feature details
        st.subheader("Feature Details")
        
        for feature_id, feature in PREMIUM_FEATURES.items():
            with st.expander(f"{feature['icon']} {feature['name']}"):
                st.write(feature['description'])
                
                # Display which plans include this feature
                available_in = [PREMIUM_PLANS[plan]['name'] for plan in feature['plans']]
                st.write(f"**Available in:** {', '.join(available_in)}")
                
                # Add a simulated screenshot or example
                st.info("Feature preview would appear here in a production app")
    
    with tab4:
        st.subheader("Premium Features Analytics")
        st.write("This data helps us understand which features are most valuable to users.")
        
        # Display premium feature analytics
        display_most_wanted_features()
        
        # Add some simulated conversion data
        st.subheader("Conversion Metrics")
        
        # Create simulated conversion data
        conversion_data = {
            "Date": [
                (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") 
                for i in range(14, -1, -1)
            ],
            "Unique Visitors": [120, 135, 140, 130, 150, 160, 175, 185, 190, 200, 210, 205, 220, 230, 240],
            "Feature Impressions": [80, 95, 100, 90, 110, 120, 130, 140, 145, 155, 165, 160, 175, 180, 190],
            "Upgrade Clicks": [8, 10, 11, 9, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
            "Conversions": [2, 3, 2, 2, 3, 4, 3, 4, 4, 5, 5, 6, 6, 7, 8]
        }
        
        # Calculate rates
        conv_df = pd.DataFrame(conversion_data)
        conv_df["Impression Rate"] = (conv_df["Feature Impressions"] / conv_df["Unique Visitors"] * 100).round(1)
        conv_df["Click Rate"] = (conv_df["Upgrade Clicks"] / conv_df["Feature Impressions"] * 100).round(1)
        conv_df["Conversion Rate"] = (conv_df["Conversions"] / conv_df["Upgrade Clicks"] * 100).round(1)
        
        # Display the metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_imp_rate = conv_df["Impression Rate"].mean()
            st.metric("Avg. Impression Rate", f"{avg_imp_rate:.1f}%")
        
        with col2:
            avg_click_rate = conv_df["Click Rate"].mean()
            st.metric("Avg. Click Rate", f"{avg_click_rate:.1f}%")
        
        with col3:
            avg_conv_rate = conv_df["Conversion Rate"].mean()
            st.metric("Avg. Conversion Rate", f"{avg_conv_rate:.1f}%")
        
        # Plot conversion funnel
        funnel_values = [
            conv_df["Unique Visitors"].sum(),
            conv_df["Feature Impressions"].sum(),
            conv_df["Upgrade Clicks"].sum(),
            conv_df["Conversions"].sum()
        ]
        
        funnel_labels = [
            "Unique Visitors",
            "Feature Impressions",
            "Upgrade Clicks",
            "Conversions"
        ]
        
        fig = go.Figure(go.Funnel(
            y=funnel_labels,
            x=funnel_values,
            textinfo="value+percent initial",
            marker={"color": ["#4682B4", "#5F9EA0", "#6495ED", "#4169E1"]}
        ))
        
        fig.update_layout(
            title="Premium Feature Conversion Funnel",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Disclaimer about simulated data
        st.caption("Note: The conversion metrics shown are simulated for demonstration purposes.")

if __name__ == "__main__":
    main()