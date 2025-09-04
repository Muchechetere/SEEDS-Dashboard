import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler

# Try UMAP first; fall back to PCA if unavailable
try:
    from umap.umap_ import UMAP
    _USE_UMAP = True
except Exception:
    from sklearn.decomposition import PCA
    _USE_UMAP = False

@st.cache_data
def load_docs3d():
    try:
        return pd.read_csv("docs_3d.csv")
    except Exception:
        return None

@st.cache_data
def load_sources():
    topics = pd.read_csv("topics.csv")
    with open("topic_labels.json", "r") as f:
        topic_labels = json.load(f)
    try:
        with open("topic_data.json", "r") as f:
            topic_data = json.load(f)
    except FileNotFoundError:
        topic_data = []
    try:
        blogs = pd.read_csv("blogs.csv")
    except Exception:
        blogs = pd.DataFrame()
    return topics, topic_labels, topic_data, blogs

def _build_topic_matrix(topic_data):
    vocab = sorted({kw for item in topic_data for kw, _ in item.get("keywords", [])})
    if not vocab:
        return np.zeros((0, 0), dtype=float), [], []
    idx = {kw: i for i, kw in enumerate(vocab)}

    rows, topic_ids, top5 = [], [], []
    for item in topic_data:
        t = item.get("topic_number")
        if t is None:
            continue
        vec = np.zeros(len(vocab), dtype=float)
        kws = item.get("keywords", [])
        for kw, score in kws:
            if kw in idx:
                try:
                    vec[idx[kw]] = float(score)
                except Exception:
                    vec[idx[kw]] = 0.0
        rows.append(vec)
        topic_ids.append(int(t))
        top5.append(", ".join([kw for kw, _ in kws[:5]]) if kws else "")

    X = np.vstack(rows) if rows else np.zeros((0, len(vocab)))
    return X, topic_ids, top5

def _topic_sizes(topic_ids, topics_df, blogs_df, labels_map):
    if not topics_df.empty:
        count_col = "Frequency" if "Frequency" in topics_df.columns else topics_df.columns[-1]
        totals = topics_df.groupby("Topic")[count_col].sum()
        raw = [float(totals.get(t, 1.0)) for t in topic_ids]
    elif not blogs_df.empty and "topic_label" in blogs_df.columns:
        per_label = blogs_df["topic_label"].value_counts()
        raw = [float(per_label.get(labels_map.get(str(t), str(t)), 1.0)) for t in topic_ids]
    else:
        raw = [1.0 for _ in topic_ids]

    sizes = MinMaxScaler((8, 28)).fit_transform(np.array(raw).reshape(-1, 1)).ravel()
    return sizes

def _color_map(labels):
    green_palette = ['#2ecc40', '#27ae60', '#16a085', '#229954', '#1e8449', '#239b56', '#28b463', '#58d68d']
    cats = pd.Series(labels).astype(str).unique().tolist()
    return {lab: green_palette[i % len(green_palette)] for i, lab in enumerate(cats)}

def show():
    # --- Intro Section ---
    st.markdown("<h1 style='color:green;'>SEEDS Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("""
    **Welcome to the SEEDS (Sustainable, Efficient, and Eco-Friendly Development Strategies) Dashboard!**  
    This project explores *Green Software Engineering* trends by analyzing a wide range of developer-written blog posts  

    By processing this data using **Topic Modeling** and advanced dimensionality-reduction techniques,  
    we can uncover patterns in how GSE topics are discussed in software development.
    """)

    st.markdown("""
    ### About the visual below  
    What you see here is a **3D Topic Map**:  
    - **Each Bubble** represents a **blog post**, and the clustering (closeness) of the bubbles illustrates their relationship within a Topic.  
    - **Position** in 3D space is determined by reducing high-dimensional text data down to three components using UMAP.  
    - **Size** reflects how prominent that topic is in the dataset.  
    - **Color** represents different topic groups.  

    You can **rotate, zoom, and hover** to explore which topics are close together and discover  the blogs associated.
    """)

    st.markdown("""
    > For a deeper dive into specific topics, head over to the **Topics** section using the navigation bar.
    """)

    # --- 1) Preferred path: precomputed positions ---
    docs3d = load_docs3d()
    if docs3d is not None:
        df = docs3d.copy()
        rename_map = {}
        if 'topic' in df.columns and 'label' not in df.columns:
            rename_map['topic'] = 'label'
        if 'Topic' in df.columns and 'label' not in df.columns:
            rename_map['Topic'] = 'label'
        if 'title' in df.columns and 'Title' not in df.columns:
            rename_map['title'] = 'Title'
        df.rename(columns=rename_map, inplace=True)

        required = {'x','y','z'}
        if not required.issubset(df.columns):
            st.error("`docs_3d.csv` must include columns x, y, z (and optionally size, label, Title).")
            return

        cmap = _color_map(df['label'] if 'label' in df.columns else [])
        hover_cols = {}
        if 'Title' in df.columns:
            hover_cols['Title'] = True
        if 'label' in df.columns:
            hover_cols['label'] = True

        fig = px.scatter_3d(
            df,
            x='x', y='y', z='z',
            size=df['size'] if 'size' in df.columns else None,
            color='label' if 'label' in df.columns else None,
            hover_data=hover_cols,
            color_discrete_map=cmap if 'label' in df.columns else None,
            labels={'label': 'Topic'}
        )
        fig.update_traces(marker=dict(line=dict(width=0.5, color='black')))
        fig.update_layout(showlegend=True, margin=dict(l=0, r=0, b=0, t=40), height=640)
        st.plotly_chart(fig, use_container_width=True)
        return

    # --- 2) Fallback: Build from keyword weights ---
    topics_df, labels_map, topic_data, blogs_df = load_sources()
    if not topic_data:
        st.error("No 3D data available. Provide `docs_3d.csv` (preferred) or include `topic_data.json`.")
        return

    X, topic_ids, top5 = _build_topic_matrix(topic_data)
    if X.shape[0] == 0:
        st.error("No keyword vectors could be built from `topic_data.json`.")
        return

    if _USE_UMAP:
        reducer = UMAP(n_neighbors=5, n_components=3, min_dist=0.0, metric="cosine", random_state=42)
        reduced = reducer.fit_transform(X)
    else:
        reducer = PCA(n_components=3, random_state=42)
        reduced = reducer.fit_transform(X)

    sizes = _topic_sizes(topic_ids, topics_df, blogs_df, labels_map)
    labels = [labels_map.get(str(t), str(t)) for t in topic_ids]

    df = pd.DataFrame({
        "Topic_ID": topic_ids,
        "label": labels,
        "x": reduced[:, 0],
        "y": reduced[:, 1],
        "z": reduced[:, 2],
        "size": sizes,
        "TopKeywords": top5,
    })

    cmap = _color_map(df['label'])
    fig = px.scatter_3d(
        df,
        x="x", y="y", z="z",
        size="size",
        color="label",
        hover_data={"label": True, "TopKeywords": True, "Topic_ID": True},
        color_discrete_map=cmap,
        title="🌿 3D Topic Map from Keyword Weights",
        labels={"label": "Topic", "size": "Number of Blogs Associated"}
    )
    fig.update_traces(marker=dict(line=dict(width=0.5, color="black")))
    fig.update_layout(showlegend=True, margin=dict(l=0, r=0, b=0, t=40), height=640)
    st.plotly_chart(fig, use_container_width=True)

