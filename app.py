# Main entrypoint for Streamlit Community Cloud
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the actual Streamlit app
import phase5_ui.streamlit_app
