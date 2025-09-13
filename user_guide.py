import streamlit as st
import base64

def show():
    # Add leaf icon
    with open("seeds_leaf.png", "rb") as img_file:
        encoded_leaf_icon = base64.b64encode(img_file.read()).decode()
    leaf_icon_html = f'<img src="data:image/png;base64,{encoded_leaf_icon}" alt="Leaf" width="38" style="vertical-align:-10px; margin-right:10px;">'

    st.markdown(f"<h1>{leaf_icon_html}SEEDS Dashboard User Guide</h1>", unsafe_allow_html=True)
    
    # Introduction to Green Software Engineering
    st.markdown("""
    ## What is Green Software Engineering?
    
    Green Software Engineering (GSE) is an emerging discipline that focuses on designing, developing, and deploying software 
    solutions with environmental sustainability in mind. It aims to reduce the carbon footprint of software systems through 
    energy-efficient coding practices, optimised resource utilisation, and sustainable software architecture.
    """)

    # About SEEDS Dashboard
    st.markdown("""
    ## About SEEDS Dashboard
    
    The SEEDS (Sustainable, Efficient, and Eco-Friendly Development Strategies) Dashboard is a visualisation tool that analyses and presents 
    trends in Green Software Engineering discussions across field of computing. It processes blog posts to identify key topics, top contributers, and emerging trends in the GSE space.
    """)

    # Dashboard Features
    st.markdown("""
    ## Dashboard Features
    
    ### 1. Multiple Topic Selection And Year Range Filter
    - Use the multiselect dropdown to choose one or more topics of interest
    - Filter content by year range using the Start Year and End Year selectors
    
    ### 2. Visualisations
    
    #### The Green Cloud
    - Word cloud visualisation showing the most frequent terms in selected topics
    - Larger words indicate higher frequency of occurrence
    
    #### Top 10 Keywords
    - Horizontal bar chart displaying the most significant keywords
    - Shows relative importance through bar length
    
    #### Top Voices
    - Pie chart showing the top blog authors in the selected topics
    - Highlights key contributors in the GSE community
    
    #### Topic Growth Over Time
    - Line graph tracking topic trend over time
    - By picking different topics,you can compare their growth over your preferred time period
    - Shows trends and evolution of discussions
    
    ### 3. Blog Recommendations
    - Curated list of top blog posts related to selected topics
    - Includes title, author, organisation, and publication year
    - Direct links to full articles
    """)


    # Footer
    st.info("For more information about Green Software Engineering, visit the [Green Software Foundation](https://greensoftware.foundation)")


