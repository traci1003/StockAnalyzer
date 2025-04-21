import streamlit as st
import os
import toml
import json
from monetization import is_feature_available

# Define our themes
THEMES = {
    "light": {
        "name": "Light",
        "base": "light",
        "primaryColor": "#0066cc",
        "backgroundColor": "#FFFFFF",
        "secondaryBackgroundColor": "#F0F2F6",
        "textColor": "#262730",
        "font": "sans serif"
    },
    "dark": {
        "name": "Dark",
        "base": "dark",
        "primaryColor": "#4da6ff",
        "backgroundColor": "#0e1117",
        "secondaryBackgroundColor": "#262730",
        "textColor": "#fafafa",
        "font": "sans serif"
    },
    "investor": {
        "name": "Investor Mode",
        "base": "dark",
        "primaryColor": "#4CAF50",
        "backgroundColor": "#0E1A0F",
        "secondaryBackgroundColor": "#1E2E1F",
        "textColor": "#E0F2E1",
        "font": "sans serif"
    },
    "premium_gold": {
        "name": "Premium Gold",
        "base": "light",
        "primaryColor": "#FFD700",
        "backgroundColor": "#FFFAF0",
        "secondaryBackgroundColor": "#F5F5DC",
        "textColor": "#4a4a4a",
        "font": "sans serif"
    },
    "premium_blue": {
        "name": "Premium Blue",
        "base": "dark",
        "primaryColor": "#00BFFF",
        "backgroundColor": "#000080",
        "secondaryBackgroundColor": "#191970",
        "textColor": "#E0FFFF",
        "font": "sans serif"
    }
}

# Path to the Streamlit config file
CONFIG_PATH = ".streamlit/config.toml"

def get_current_theme():
    """Get the current active theme name from session state or set default"""
    if "current_theme" not in st.session_state:
        st.session_state.current_theme = "light"
    return st.session_state.current_theme

def set_theme(theme_name):
    """Set a new theme by name"""
    # Update session state
    st.session_state.current_theme = theme_name
    
    # Only need to update file if asked to
    if theme_name in THEMES:
        theme = THEMES[theme_name]
        
        # Add JavaScript to store this theme preference
        st.markdown(f"""
        <script>
            // Store theme preference
            localStorage.setItem('preferred_theme', '{theme_name}');
        </script>
        """, unsafe_allow_html=True)

def apply_theme(theme_name, update_file=False):
    """Apply a theme by updating the config.toml file"""
    if theme_name not in THEMES:
        return False
    
    theme = THEMES[theme_name]
    
    # Only update the file if explicitly asked to
    if update_file:
        try:
            # Check if config exists
            if os.path.exists(CONFIG_PATH):
                # Load the existing config
                with open(CONFIG_PATH, "r") as f:
                    config = toml.load(f)
            else:
                config = {"server": {"headless": True, "address": "0.0.0.0", "port": 5000}}
            
            # Update the theme section
            config["theme"] = {
                "base": theme["base"],
                "primaryColor": theme["primaryColor"],
                "backgroundColor": theme["backgroundColor"],
                "secondaryBackgroundColor": theme["secondaryBackgroundColor"],
                "textColor": theme["textColor"],
                "font": theme["font"]
            }
            
            # Write back to the file
            with open(CONFIG_PATH, "w") as f:
                toml.dump(config, f)
            
            return True
        except Exception as e:
            st.error(f"Error updating theme: {e}")
            return False
    
    # Always return the current theme for CSS customization
    return theme

def display_theme_options():
    """Display theme selection options in sidebar"""
    current_theme = get_current_theme()
    
    # Available themes for all users
    available_themes = ["light", "dark"]
    
    # Add special investor theme
    available_themes.append("investor")
    
    # Check if premium themes are available
    premium_themes_available = is_feature_available("custom_themes")
    
    if premium_themes_available:
        available_themes.extend(["premium_gold", "premium_blue"])
    
    st.sidebar.markdown("### 🎨 Theme Options")
    
    # Display radio buttons for theme selection
    theme_labels = [THEMES[t]["name"] for t in available_themes]
    theme_index = available_themes.index(current_theme) if current_theme in available_themes else 0
    
    selected_theme_name = st.sidebar.radio(
        "Select Theme",
        theme_labels,
        index=theme_index
    )
    
    # Figure out which theme was selected and apply it
    selected_index = theme_labels.index(selected_theme_name)
    new_theme = available_themes[selected_index]
    
    # If a premium theme was selected but user doesn't have access
    if new_theme in ["premium_gold", "premium_blue"] and not premium_themes_available:
        from monetization import display_feature_teaser
        display_feature_teaser("custom_themes")
        return
    
    # Apply the selected theme if it changed
    if new_theme != current_theme:
        set_theme(new_theme)
        st.sidebar.success(f"{selected_theme_name} theme applied!")
        # Add a button to reboot the app for theme to take effect
        if st.sidebar.button("✨ Restart with new theme"):
            apply_theme(new_theme, update_file=True)
            st.rerun()

def check_theme_preference():
    """Check for user theme preference in localStorage"""
    st.markdown("""
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const preferredTheme = localStorage.getItem('preferred_theme');
        if (preferredTheme) {
            // Send the theme preference to the server via query param
            const currentUrl = new URL(window.location);
            currentUrl.searchParams.set('theme', preferredTheme);
            window.history.replaceState(null, '', currentUrl);
            window.location.reload();
        }
    });
    </script>
    """, unsafe_allow_html=True)
    
    # Check if theme is in URL parameters
    if 'theme' in st.query_params:
        theme_name = st.query_params['theme']
        if theme_name in THEMES:
            st.session_state.current_theme = theme_name
            # Clear the parameter after using it
            params = dict(st.query_params)
            if 'theme' in params:
                del params['theme']
            st.query_params.update(params)

def display_custom_css():
    """Display custom CSS based on the current theme"""
    current_theme = get_current_theme()
    theme = THEMES.get(current_theme, THEMES["light"])
    
    # Apply some custom CSS adjustments based on the theme
    primary_color = theme["primaryColor"]
    text_color = theme["textColor"]
    
    st.markdown(f"""
    <style>
    /* Custom theme adjustments */
    .stButton button {{
        border-radius: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        transition: all 0.3s cubic-bezier(.25,.8,.25,1);
    }}
    
    .stButton button:hover {{
        box-shadow: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);
    }}
    
    /* Theme-specific adjustments */
    div.stTitle h1 {{
        color: {primary_color};
        border-bottom: 2px solid {primary_color};
        padding-bottom: 10px;
    }}
    
    /* Premium indicators */
    .premium-badge {{
        display: inline-block;
        background: linear-gradient(45deg, {primary_color}, #FFD700);
        color: #fff;
        padding: 2px 6px;
        border-radius: 15px;
        font-size: 0.8em;
        margin-left: 5px;
        animation: glow 2s infinite alternate;
    }}
    
    @keyframes glow {{
        from {{
            box-shadow: 0 0 5px {primary_color};
        }}
        to {{
            box-shadow: 0 0 10px {primary_color}, 0 0 20px gold;
        }}
    }}
    
    /* Tooltip styles */
    .tooltip {{
        position: relative;
        display: inline-block;
    }}
    
    .tooltip .tooltiptext {{
        visibility: hidden;
        background-color: #333;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px 10px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
        width: 200px;
    }}
    
    .tooltip:hover .tooltiptext {{
        visibility: visible;
        opacity: 1;
    }}
    </style>
    """, unsafe_allow_html=True)