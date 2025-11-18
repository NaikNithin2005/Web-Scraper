import streamlit as st
import json  # Added for JSON downloading
from scrape import (
    scrape_website,
    split_dom_content,  # This function was imported but not used in your original code
    clean_body_content,
    extract_body_content
)

# --- Page Configuration (More polished) ---
st.set_page_config(
    page_title="AI Web Scraper",
    layout="wide",
    page_icon="🤖"  # Added an icon
)

# --- Sidebar (Cleaner organization) ---
with st.sidebar:
    st.title("🛠️ Configuration")

    st.subheader("AI Processing")
    summarize_option = st.checkbox("Summarize Extracted Content")
    extract_keywords = st.checkbox("Extract Keywords")
    
    st.markdown("---")

    st.subheader("Download Settings")
    enable_download = st.checkbox("Enable Download Button", value=True)
    
    st.markdown("---")
    st.info("This scraper is optimized for e-commerce product pages.")


# --- Main Page ---
st.title("🤖 AI-Driven E-Commerce Scraper")
st.write(
    "This tool helps you scrape and clean e-commerce product content for research, "
    "AI processing, analytics, and sustainable decision-making."
)

# --- Input Area ---
url = st.text_input("Enter the URL of the e-commerce page to scrape:")

col1, col2 = st.columns([1, 1])

with col1:
    # Made button "primary" for better UI
    scrape_btn = st.button("🔍 Scrape Site", use_container_width=True, type="primary")

with col2:
    # Changed text for clarity
    clear_btn = st.button("🗑️ Clear Results", use_container_width=True)


# --- Button Logic ---
if clear_btn:
    # Clears the entire session state to reset the app
    st.session_state.clear()
    st.rerun()

if scrape_btn:
    if not url or not url.startswith("http"):
        st.error("Please enter a valid URL starting with http or https.")
    else:
        # Use a spinner for a cleaner "loading" experience
        with st.spinner("Scraping website... This may take a moment."):
            try:
                # Save URL to state for JSON download
                st.session_state.scraped_url = url 
                
                progress = st.progress(0, text="Initializing...")

                progress.progress(30, text="Fetching website...")
                result = scrape_website(url)

                progress.progress(60, text="Extracting body content...")
                body_content = extract_body_content(result)
                # Save raw content to state
                st.session_state.raw_content = body_content 

                progress.progress(90, text="Cleaning content...")
                cleaned_content = clean_body_content(body_content)
                # Save cleaned content to state
                st.session_state.dom_content = cleaned_content 
                
                progress.progress(100, text="Done!")
                progress.empty()  # Remove progress bar on success
                st.success("Scraping completed successfully!")
            
            except Exception as e:
                st.error(f"An error occurred: {e}")
                # Clear state if scraping failed
                if "dom_content" in st.session_state:
                    del st.session_state.dom_content
                if "raw_content" in st.session_state:
                    del st.session_state.raw_content


# --- Results Display (Persistent) ---
# This check makes the results stay on screen until "Clear" is pressed
if "dom_content" in st.session_state:
    st.markdown("---")
    st.subheader("Scraping Results")

    # MODIFIED: Use tabs for a much cleaner and more "elegant" layout
    tab1, tab2, tab3 = st.tabs(["✨ Cleaned Content", "📄 Raw HTML Body", "💡 AI Insights"])

    with tab1:
        st.text_area("Cleaned Text:", st.session_state.dom_content, height=400)
    
    with tab2:
        st.text_area("Raw Body Content:", st.session_state.raw_content, height=400)

    with tab3:
        # Group AI outputs in containers for better visual separation
        if summarize_option:
            with st.container(border=True):
                st.subheader("Content Summary")
                st.warning("Summarization model not implemented yet.")
                # st.write("Summarization model output would go here...")
        
        if extract_keywords:
            with st.container(border=True):
                st.subheader("Extracted Keywords")
                st.warning("Keyword extraction not implemented yet.")
                # st.write("Keyword model output would go here...")

        if not summarize_option and not extract_keywords:
            st.info("Enable 'Summarize' or 'Extract Keywords' in the sidebar to see AI insights.")

    # --- Download Logic (MODIFIED) ---
    if enable_download:
        st.markdown("---")
        st.subheader("⬇️ Download Content")
        
        cleaned_content = st.session_state.dom_content
        
        # NEW: Ask the user for the file type
        file_type = st.radio(
            "Select download format:",
            ("Text (.txt)", "JSON (.json)"),
            horizontal=True
        )

        # Prepare data and parameters based on the user's choice
        if file_type == "Text (.txt)":
            data_to_download = cleaned_content
            file_name = "cleaned_content.txt"
            mime = "text/plain"
        
        elif file_type == "JSON (.json)":
            # Create a JSON structure
            json_data = {
                "url": st.session_state.get("scraped_url", "unknown"),
                "cleaned_content": cleaned_content
            }
            # Convert dict to a string for downloading
            data_to_download = json.dumps(json_data, indent=4) 
            file_name = "cleaned_content.json"
            mime = "application/json"

        # The download button is now dynamic
        st.download_button(
            label=f"Download as {file_type}",
            data=data_to_download,
            file_name=file_name,
            mime=mime,
            use_container_width=True
        )