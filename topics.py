import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from html import escape
from pathlib import Path
import plotly.express as px
import json
import base64

@st.cache_data
def load_data():
    try:
        blogs = pd.read_csv("blogs.csv")
        topics = pd.read_csv("topics.csv")
        with open("topic_labels.json", "r") as f:
            topic_labels = json.load(f)
        try:
            with open("topic_data.json", "r") as f:
                topic_data = json.load(f)
        except FileNotFoundError:
            st.warning("topic_data.json not found. Keyword visualization will be unavailable.")
            topic_data = []
        return blogs, topics, topic_labels, topic_data
    except FileNotFoundError:
        st.error("Data files not found. Please make sure 'blogs.csv', 'topics.csv', 'topic_labels.json' and 'topic_data.json' are in the same directory.")
        return None, None, None, None

# Load once at import (uses Streamlit cache)
blogs, topics_df, topic_labels_dict, topic_data = load_data()
if blogs is None:
    st.stop()

# Shared green palette
green_palette = ['#2ecc40', '#27ae60', '#16a085', '#229954', '#1e8449', '#239b56', '#28b463', '#58d68d']

# Encode link icon (fallback to a unicode if file missing)
# Encode link icon (no fallback)
with open("link.png", "rb") as image_file:
    encoded_link_icon = base64.b64encode(image_file.read()).decode()
link_icon_html = f'<img src="data:image/png;base64,{encoded_link_icon}" alt="Link" width="16" style="vertical-align:-3px;">'


def inject_css(path: str = "style.css") -> None:
    css = Path(path).read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def show():
    inject_css() 
    st.markdown("<h1>SEEDS Topics Explorer</h1>", unsafe_allow_html=True)
    st.info("Filter by topic and year to explore insights, trends, and key voices in the world of Green Software Engineering.", icon="ℹ️")

    # ---------------- Filters ----------------
    topic_label_list_for_selectbox = list(topic_labels_dict.values())

    col_topics, col_years = st.columns([3, 1])
    with col_topics:
        selected_topic_labels = st.multiselect(
            "Choose topic(s):",
            topic_label_list_for_selectbox,
            default=[]
        )

    with col_years:
        if not topics_df.empty and 'Timestamp' in topics_df.columns:
            topics_df['Timestamp'] = pd.to_datetime(topics_df['Timestamp'])
            years = topics_df['Timestamp'].dt.year.unique()
            years.sort()
            c1, c2 = st.columns(2)
            with c1:
                start_year = st.selectbox("Start Year", options=years, index=0)
            with c2:
                end_year = st.selectbox("End Year", options=years, index=len(years) - 1)
        else:
            start_year, end_year = None, None

    if not selected_topic_labels:
        st.info("Please select at least one topic from the dropdown to see the analysis.")
        return

    selected_topic_numbers = [
        int(num_str)
        for num_str, label in topic_labels_dict.items()
        if label in selected_topic_labels
    ]

    selected_articles_df = blogs[blogs['topic_label'].isin(selected_topic_labels)].copy()
    selected_topics_over_time_df = topics_df[topics_df['Topic'].isin(selected_topic_numbers)].copy()

    if start_year is not None and end_year is not None and not selected_topics_over_time_df.empty:
        selected_topics_over_time_df['Timestamp'] = pd.to_datetime(selected_topics_over_time_df['Timestamp'])
        selected_topics_over_time_df = selected_topics_over_time_df[
            (selected_topics_over_time_df['Timestamp'].dt.year >= start_year) &
            (selected_topics_over_time_df['Timestamp'].dt.year <= end_year)
        ]

    # --------------- Row 1 (3 charts) ---------------
    col_wc, col_bar, col_pie = st.columns([1.05, 1.05, 1.35])

    # -------- Word Cloud --------
    with col_wc:
        st.markdown("<h3 class='section-title'>The Green Cloud</h3>", unsafe_allow_html=True)
        topic_text = " ".join(selected_articles_df['body'].dropna().tolist())
        if topic_text.strip():
            wc = WordCloud(
                width=800,
                height=800,
                background_color="white",
                colormap="Greens",
                max_words=200,
                collocations=False,
                random_state=42
            ).generate(topic_text)

            fig, ax = plt.subplots(figsize=(4, 4))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig, use_container_width=True)
        else:
            st.info("No text available to generate a word cloud for these topics.")

    # Horizontal Bar Chart
    with col_bar:
        st.markdown("<h3 class='section-title'>Top 10 Keywords</h3>", unsafe_allow_html=True)
        keywords_list = []
        for topic_number in selected_topic_numbers:
            selected_topic_data_item = next((item for item in topic_data if item.get('topic_number') == topic_number), None)
            if selected_topic_data_item and selected_topic_data_item.get('keywords'):
                keywords_list.extend(selected_topic_data_item['keywords'])

        if keywords_list:
            keywords_df = pd.DataFrame(keywords_list, columns=['Keyword', 'Score'])
            keywords_df = keywords_df.groupby('Keyword', as_index=False)['Score'].sum().sort_values('Score', ascending=False)
            fig_bar = px.bar(
                keywords_df.head(10),
                x='Score', y='Keyword', orientation='h', title='Top 10 Keywords',
                color='Keyword', color_discrete_sequence=green_palette
            )
            fig_bar.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                plot_bgcolor='#f8fff8',
                paper_bgcolor='#f8fff8',
                margin=dict(l=10, r=10, b=10, t=30),
                showlegend=False,
                height=440
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No keywords found for these topics.")

  
    # Pie Chart
    with col_pie:
        st.markdown("<h3 class='section-title'>Top Voices</h3>", unsafe_allow_html=True)
        if not selected_articles_df.empty and 'author' in selected_articles_df.columns:
            author_counts = selected_articles_df['author'].value_counts().reset_index()
            author_counts.columns = ['Author', 'Count']

            # keep your "Others" aggregation logic
            top_authors_df = author_counts[author_counts['Count'] > 1].copy()
            others_count = author_counts[author_counts['Count'] == 1]['Count'].sum()
            if others_count > 0:
                others_row = pd.DataFrame([{'Author': 'Others', 'Count': others_count}])
                pie_chart_data = pd.concat([top_authors_df, others_row], ignore_index=True)
            else:
                pie_chart_data = top_authors_df

            if not pie_chart_data.empty:
                fig_pie = px.pie(
                    pie_chart_data,
                    names='Author',
                    values='Count',
                    color_discrete_sequence=green_palette
                )
                # let the pie fill the column and reduce wasted padding
                fig_pie.update_traces(
                    textposition='inside',
                    textinfo='label',
                    insidetextorientation='radial',
                    marker=dict(line=dict(width=2))
                )
                fig_pie.update_layout(
                    height=440,                     # bigger than bar (340) & WC; feels dominant
                    margin=dict(l=0, r=0, t=30, b=0),
                    showlegend=False,
                    plot_bgcolor='#f8fff8',
                    paper_bgcolor='#f8fff8'
                )
                st.plotly_chart(fig_pie, use_container_width=True)  # key change: responsive width
            else:
                st.info("No author data available to display a pie chart for these topics.")
        else:
            st.info("No blogs available to display author distribution for these topics.")


    # --------------- Row 2 (Line) ---------------
    st.markdown("<h3 class='section-title'>📈 Topic Growth Over Time</h3>", unsafe_allow_html=True)
    if not selected_topics_over_time_df.empty:
        selected_topics_over_time_df['Topic_Label'] = selected_topics_over_time_df['Topic'].map(
            lambda x: topic_labels_dict.get(str(x), str(x))
        )
        count_col = 'Frequency' if 'Frequency' in selected_topics_over_time_df.columns else selected_topics_over_time_df.columns[-2]
        fig_line = px.line(
            selected_topics_over_time_df, x='Timestamp', y=count_col, color='Topic_Label',
            color_discrete_sequence=green_palette
        )
        fig_line.update_traces(mode='lines+markers')
        fig_line.update_layout(
            plot_bgcolor='#eafaf1',
            paper_bgcolor='#eafaf1',
            margin=dict(l=10, r=10, b=10, t=30),
            height=420
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No topic growth data available for these topics.")

    # --------------- Row 3 (Table) ---------------
    st.markdown("<h3 class='section-title'>Top Blog Recommendations</h3>", unsafe_allow_html=True)

    # Use exact columns, assume they exist
    blog_table_df = selected_articles_df[['title', 'author', 'organisation', 'published_year', 'url']].head(10).copy()
    blog_table_df.index = range(1, len(blog_table_df) + 1)

    # tidy + rename (sanitation only)
    blog_table_df = blog_table_df.fillna("").astype(str).applymap(lambda s: s.strip())
    blog_table_df.loc[blog_table_df["organisation"].fillna("").astype(str).str.strip() == "", "organisation"] = "Independent Author"
    blog_table_df.columns = ["Title", "Author", "Organisation", "Year", "URL"]

    # Build HTML rows
    rows_html = []
    for i, row in blog_table_df.iterrows():
        title = escape(row["Title"])
        author = escape(row["Author"])
        org = escape(row["Organisation"])
        year = escape(row["Year"])
        url = row["URL"].strip()
        link_html = f"<a class='seeds-link' href='{escape(url)}' target='_blank' rel='noopener'>{link_icon_html}</a>" if url else ""
        rows_html.append(
            f"<tr>"
            f"<td class='idx'>{i}</td>"
            f"<td>{title}</td>"
            f"<td>{author}</td>"
            f"<td>{org}</td>"
            f"<td>{year}</td>"
            f"<td>{link_html}</td>"
            f"</tr>"
        )

    table_html = f"""
    <div class="panel seeds-table-wrapper">
    <table class="seeds-table">
        <thead>
        <tr>
            <th class='idx'>#</th>
            <th>Title</th>
            <th>Author</th>
            <th>Organisation</th>
            <th>Year</th>
            <th>URL</th>
        </tr>
        </thead>
        <tbody>
        {''.join(rows_html)}
        </tbody>
    </table>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)


