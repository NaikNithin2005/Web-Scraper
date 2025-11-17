import streamlit as st
from scrape import (
    scrape_website, 
    split_dom_content,
    clean_body_content,
    extract_body_content
)

st.title("AI-DRIVEN WEB SCRAPING FOR SUSTAINABLE INSIGHTS AND DECISION MAKING ON E-COMMERCE")

url = st.text_input("Enter the URL of the e-commerce page to scrape:")

if st.button("Scrapr Site"):
    st.write("Scraping your site...")


    result = scrape_website(url)
    body_content = extract_body_content(result)
    cleaned_content = clean_body_content(body_content)

    st.session_state.dom_content = cleaned_content

    with st.expander("View DOM Content"):
        st.text_area("DOM Content", cleaned_content, height=300)
    



