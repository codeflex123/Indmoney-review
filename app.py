import streamlit as st
import pandas as pd
import plotly.express as px
import time
import sys
import os
import json

from db import get_db_connection, init_db
from phase4_delivery.mailer import Mailer
from phase1_ingestion.scraper import scrape_reviews, save_to_db, save_to_json
from phase2_llm.analyzer import ReviewAnalyzer
from phase3_insights.pulsar import Pulsar


st.set_page_config(
    page_title="INDmoney Pulse Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Functions ---
@st.cache_data(ttl=60)
def fetch_reviews(limit=100):
    df = pd.DataFrame()
    try:
        conn = get_db_connection()
        query = f"SELECT * FROM reviews ORDER BY at DESC LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        conn.close()
    except Exception:
        pass

    if df.empty:
        # Fallback to local reviews_preview.json if database is empty (e.g. fresh Streamlit deployment)
        try:
            with open("phase1_ingestion/reviews_preview.json", "r") as f:
                data = json.load(f)
                df = pd.DataFrame(data)
                if not df.empty:
                    df['at'] = pd.to_datetime(df['at'])
                    df = df.sort_values(by='at', ascending=False)
        except Exception:
            pass

    if not df.empty:
        # Standardize column naming in case Postgres names are returned
        if 'thumbs_up_count' in df.columns:
            df = df.rename(columns={'thumbs_up_count': 'thumbsUpCount'})
        if 'review_id' in df.columns:
            df = df.rename(columns={'review_id': 'reviewId'})
        return df.head(limit).to_dict('records')
    return []

@st.cache_data(ttl=60)
def fetch_analysis():
    try:
        with open("phase2_llm/analysis_results.json", "r") as f:
            return json.load(f)
    except Exception:
        return None

def trigger_pipeline(limit=500):
    try:
        with st.spinner("Scraping Google Play Store..."):
            init_db()
            data = scrape_reviews(max_count=limit, weeks=12)
            save_to_db(data)
            save_to_json(data)
            
        with st.spinner("Analyzing Sentiment with Groq AI..."):
            analyzer = ReviewAnalyzer()
            analyzer.run_analysis(limit=limit)
            
        with st.spinner("Generating Executive Report with Gemini..."):
            pulsar = Pulsar()
            pulsar.run()
            
        st.success("Analysis Complete!")
        # Clear cached functions to load the new data immediately
        fetch_reviews.clear()
        fetch_analysis.clear()
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Pipeline failed: {str(e)}")

def trigger_email(email_address):
    try:
        mailer = Mailer(recipient=email_address)
        success, message = mailer.send_email()
        if success:
            st.toast(f"Email delivery initiated to {email_address}!", icon="📧")
            return True
        else:
            st.error(f"Failed to send email: {message}")
            return False
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False

def fetch_email_preview():
    try:
        with open("weekly_pulse.md", "r") as f:
            return f.read()
    except Exception:
        return "No preview available. Run pipeline first."



# --- Main UI ---
st.title("📈 INDmoney Pulse")
st.markdown("**Institutional Sentiment Intelligence**")

# System Status
st.sidebar.success("✅ System Active (Streamlit Native)")

# --- Sidebar Control Panel ---
st.sidebar.header("Control Center")

num_reviews = st.sidebar.number_input("Number of Reviews to Analyze", min_value=10, max_value=2000, value=500, step=50)

if st.sidebar.button("🚀 Run Full Analysis", use_container_width=True):
    trigger_pipeline(num_reviews)

st.sidebar.markdown("---")
st.sidebar.subheader("Delivery Actions")

with st.sidebar.expander("Email Settings", expanded=True):
    recipient_email = st.text_input("Recipient Email", placeholder="executive@indmoney.com")
    if st.button("📧 Email Weekly Report", use_container_width=True):
        if recipient_email:
            trigger_email(recipient_email)
        else:
            st.warning("Please provide a recipient email.")

# --- Content Sections ---
reviews_data = fetch_reviews(100)
analysis_data = fetch_analysis()

tab1, tab2, tab3 = st.tabs(["📊 Intelligence Cluster", "💬 Raw Signals", "📨 Email Preview"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Theme Distribution")
        if analysis_data and "categorized_reviews" in analysis_data:
            themes = analysis_data["categorized_reviews"]
            if themes:
                # Prepare data for Plotly
                theme_names = []
                counts = []
                for theme, count in themes.items():
                    theme_names.append(theme)
                    counts.append(count)
                
                df_themes = pd.DataFrame({"Theme": theme_names, "Count": counts})
                df_themes = df_themes.sort_values(by="Count", ascending=True)
                
                fig = px.pie(
                    df_themes, 
                    values="Count", 
                    names="Theme", 
                    color_discrete_sequence=px.colors.sequential.Purples_r,
                    hole=0.4
                )
                
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    textfont=dict(color="#ffffff", size=11)
                )
                
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    margin=dict(l=10, r=10, t=10, b=10),
                    showlegend=False,
                    height=450
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No themes found.")
        else:
            st.info("No analysis data available. Run the pipeline first.")
            
    with col2:
        st.subheader("⚡ Signal Extraction (Top Quotes)")
        if analysis_data and "top_quotes" in analysis_data:
            quotes = analysis_data["top_quotes"]
            for q in quotes:
                score = q.get("score", 5) if isinstance(q, dict) else 5
                content = q.get("content", q) if isinstance(q, dict) else q
                
                st.markdown(f"> {'⭐' * int(score)}\n> *\"{content}\"*")
                st.divider()
        else:
            st.info("No quotes available.")

with tab2:
    st.subheader("Recent Feed")
    if reviews_data:
        df_reviews = pd.DataFrame(reviews_data)
        # Select relevant columns and format
        if not df_reviews.empty:
            st.dataframe(
                df_reviews[['score', 'content', 'at', 'thumbsUpCount']],
                column_config={
                    "score": st.column_config.NumberColumn("Rating", format="⭐ %d"),
                    "content": "Review Content",
                    "at": st.column_config.DatetimeColumn("Date", format="D MMM YYYY"),
                    "thumbsUpCount": st.column_config.NumberColumn("Helpful", format="👍 %d"),
                },
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No raw reviews found.")

with tab3:
    st.subheader("Weekly Pulse Preview")
    st.markdown("This is the exact content that will be emailed to stakeholders.")
    
    preview_md = fetch_email_preview()
    with st.container(border=True):
        st.markdown(preview_md)
