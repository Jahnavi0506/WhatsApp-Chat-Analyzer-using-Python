import streamlit as st
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud, STOPWORDS
from collections import Counter
import datetime
import emoji
from io import StringIO

# Page configuration
st.set_page_config(
    page_title="WhatsApp Chat Analyzer",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #25D366;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">📱 WhatsApp Chat Analyzer</h1>', unsafe_allow_html=True)

# Sidebar
st.sidebar.title("📊 Analysis Options")
st.sidebar.markdown("---")

# Parsing Functions
def startswithDateandTimeAndroid(s):
    pattern = r'^\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?: [apAP][mM])? -'
    return re.match(pattern, s) is not None

def startswithDateandTimeiOS(s):
    pattern = r'^\[\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}:\d{2}(?: [apAP][mM])?\]'
    return re.match(pattern, s) is not None

def FindAuthor(s):
    s = s.split(":", 1)
    if len(s) == 2:
        return True
    else:
        return False

def getDataPointAndroid(line):
    splitline = line.split(' - ', 1)
    if len(splitline) < 2:
        return None, None, None, line

    dateTime = splitline[0].strip()
    message = splitline[1].strip()

    if ',' in dateTime:
        date, time = dateTime.split(',', 1)
    else:
        date, time = dateTime, ""

    author = None
    if ':' in message:
        splitMessage = message.split(':', 1)
        author = splitMessage[0].strip()
        message = splitMessage[1].strip()
    
    return date.strip(), time.strip(), author, message

def getDataPointsiOS(line):
    splitLine = line.split(']', 1)
    dateTime = splitLine[0].strip('[').strip()

    if ',' in dateTime:
        date, time = dateTime.split(',', 1)
    else:
        parts = dateTime.split(' ', 1)
        date = parts[0]
        time = parts[1] if len(parts) > 1 else ""

    message = splitLine[1].strip() if len(splitLine) > 1 else ""

    author = None
    if FindAuthor(message):
        splitMessage = message.split(':', 1)
        author = splitMessage[0].strip()
        message = splitMessage[1].strip()

    return date.strip(), time.strip(), author, message

def parse_chat_file(uploaded_file):
    """Parse WhatsApp chat file and return DataFrame"""
    try:
        # Read file content
        content = uploaded_file.read().decode("utf-8")
        lines = content.split('\n')
        
        # Detect device type
        first_line = lines[0] if lines else ""
        device = 'ios' if '[' in first_line else 'android'
        
        parsedData = []
        messageBuffer = []
        date, time, author = None, None, None
        
        # Skip first two lines (header)
        for i, line in enumerate(lines[2:], start=2):
            line = line.strip()
            
            if device == 'ios':
                if startswithDateandTimeiOS(line):
                    if len(messageBuffer) > 0:
                        parsedData.append([date, time, author, ' '.join(messageBuffer)])
                    messageBuffer.clear()
                    date, time, author, message = getDataPointsiOS(line)
                    messageBuffer.append(message)
                else:
                    messageBuffer.append(line)
            else:  # android
                if startswithDateandTimeAndroid(line):
                    if len(messageBuffer) > 0:
                        parsedData.append([date, time, author, ' '.join(messageBuffer)])
                    messageBuffer.clear()
                    date, time, author, message = getDataPointAndroid(line)
                    messageBuffer.append(message)
                else:
                    messageBuffer.append(line)
        
        # Add last message buffer
        if len(messageBuffer) > 0:
            parsedData.append([date, time, author, ' '.join(messageBuffer)])
        
        # Create DataFrame
        df = pd.DataFrame(parsedData, columns=['Date', 'Time', 'Author', 'Message'])
        
        # Clean and process data
        df = df.dropna(subset=['Message'])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Add additional columns
        df['Letter_Count'] = df['Message'].apply(lambda s: len(s))
        df['Word_Count'] = df['Message'].apply(lambda s: len(s.split(' ')))
        df['MessageCount'] = 1
        
        # URL pattern
        URLPATTERN = r'(https?://\S+)'
        df['urlcount'] = df['Message'].apply(lambda x: re.findall(URLPATTERN, x)).str.len()
        
        return df, device
        
    except Exception as e:
        st.error(f"Error parsing file: {str(e)}")
        return None, None

def extract_emojis(text):
    """Extract emojis from text"""
    return [ch for ch in text if emoji.is_emoji(ch)]

def generate_wordcloud(text, title="Word Cloud"):
    """Generate word cloud"""
    if not text.strip():
        return None
    
    wordcloud = WordCloud(
        stopwords=STOPWORDS,
        background_color="white",
        max_words=200,
        width=800,
        height=400
    ).generate(text)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    ax.set_title(title, fontsize=16, pad=20)
    return fig

# Main App
uploaded_file = st.file_uploader(
    "📁 Upload WhatsApp Chat Export (.txt file)",
    type=["txt"],
    help="Export your WhatsApp chat and upload the .txt file here"
)

if uploaded_file is not None:
    # Parse the chat file
    with st.spinner("🔄 Parsing chat file..."):
        df, device_type = parse_chat_file(uploaded_file)
    
    if df is not None and not df.empty:
        st.success(f"✅ Successfully parsed {len(df)} messages from {device_type.upper()} device")
        
        # Sidebar filters
        st.sidebar.subheader("🔍 Filters")
        
        # Author filter
        authors = df['Author'].dropna().unique()
        if len(authors) > 0:
            selected_authors = st.sidebar.multiselect(
                "Select Authors",
                options=authors,
                default=authors
            )
            df_filtered = df[df['Author'].isin(selected_authors)]
        else:
            df_filtered = df
            selected_authors = []
        
        # Date range filter
        if not df['Date'].isna().all():
            min_date = df['Date'].min()
            max_date = df['Date'].max()
            
            date_range = st.sidebar.date_input(
                "Select Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                df_filtered = df_filtered[
                    (df_filtered['Date'] >= pd.Timestamp(date_range[0])) &
                    (df_filtered['Date'] <= pd.Timestamp(date_range[1]))
                ]
        
        # Main content tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", "👥 Authors", "📈 Timeline", "☁️ Word Analysis", "📱 Raw Data"
        ])
        
        with tab1:
            st.subheader("📊 Chat Overview")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Messages", len(df_filtered))
            
            with col2:
                unique_authors = df_filtered['Author'].nunique()
                st.metric("Unique Authors", unique_authors)
            
            with col3:
                total_words = df_filtered['Word_Count'].sum()
                st.metric("Total Words", f"{total_words:,}")
            
            with col4:
                avg_words = df_filtered['Word_Count'].mean()
                st.metric("Avg Words/Message", f"{avg_words:.1f}")
            
            # Message distribution
            if len(selected_authors) > 0:
                st.subheader("📈 Message Distribution by Author")
                
                author_counts = df_filtered['Author'].value_counts()
                
                # Bar chart
                fig_bar = px.bar(
                    x=author_counts.values,
                    y=author_counts.index,
                    orientation='h',
                    title="Messages per Author",
                    labels={'x': 'Number of Messages', 'y': 'Author'}
                )
                fig_bar.update_layout(height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
                
                # Pie chart
                fig_pie = px.pie(
                    values=author_counts.values,
                    names=author_counts.index,
                    title="Message Distribution"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with tab2:
            st.subheader("👥 Author Analysis")
            
            if len(selected_authors) > 0:
                for author in selected_authors:
                    author_df = df_filtered[df_filtered['Author'] == author]
                    
                    with st.expander(f"📊 {author} - {len(author_df)} messages"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Messages", len(author_df))
                        
                        with col2:
                            avg_words = author_df['Word_Count'].mean()
                            st.metric("Avg Words/Message", f"{avg_words:.1f}")
                        
                        with col3:
                            total_chars = author_df['Letter_Count'].sum()
                            st.metric("Total Characters", f"{total_chars:,}")
                        
                        # Word cloud for this author
                        author_text = " ".join(author_df['Message'].astype(str))
                        if author_text.strip():
                            fig = generate_wordcloud(author_text, f"Word Cloud - {author}")
                            if fig:
                                st.pyplot(fig)
            else:
                st.info("No authors found in the filtered data.")
        
        with tab3:
            st.subheader("📈 Timeline Analysis")
            
            if not df_filtered['Date'].isna().all():
                # Daily message count
                daily_counts = df_filtered.groupby(df_filtered['Date'].dt.date).size()
                
                fig_timeline = px.line(
                    x=daily_counts.index,
                    y=daily_counts.values,
                    title="Messages Over Time",
                    labels={'x': 'Date', 'y': 'Number of Messages'}
                )
                fig_timeline.update_layout(height=400)
                st.plotly_chart(fig_timeline, use_container_width=True)
                
                # Monthly analysis
                df_filtered['Month'] = df_filtered['Date'].dt.to_period('M')
                monthly_counts = df_filtered.groupby('Month').size()
                
                fig_monthly = px.bar(
                    x=[str(month) for month in monthly_counts.index],
                    y=monthly_counts.values,
                    title="Messages by Month",
                    labels={'x': 'Month', 'y': 'Number of Messages'}
                )
                fig_monthly.update_layout(height=400)
                st.plotly_chart(fig_monthly, use_container_width=True)
            else:
                st.info("No date information available for timeline analysis.")
        
        with tab4:
            st.subheader("☁️ Word Analysis")
            
            # Overall word cloud
            all_text = " ".join(df_filtered['Message'].astype(str))
            if all_text.strip():
                st.subheader("Overall Word Cloud")
                fig = generate_wordcloud(all_text, "All Messages")
                if fig:
                    st.pyplot(fig)
            
            # Most common words
            st.subheader("🔤 Most Common Words")
            all_words = " ".join(df_filtered['Message'].astype(str)).lower()
            words = re.findall(r'\b\w+\b', all_words)
            word_counts = Counter(words)
            
            # Remove common stopwords
            stopwords = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'])
            
            filtered_words = {word: count for word, count in word_counts.items() 
                            if word not in stopwords and len(word) > 2}
            
            top_words = Counter(filtered_words).most_common(20)
            
            if top_words:
                words_df = pd.DataFrame(top_words, columns=['Word', 'Count'])
                fig_words = px.bar(
                    words_df,
                    x='Count',
                    y='Word',
                    orientation='h',
                    title="Top 20 Most Used Words"
                )
                fig_words.update_layout(height=500)
                st.plotly_chart(fig_words, use_container_width=True)
            
            # Emoji analysis
            st.subheader("😀 Emoji Analysis")
            all_emojis = []
            for message in df_filtered['Message']:
                all_emojis.extend(extract_emojis(str(message)))
            
            if all_emojis:
                emoji_counts = Counter(all_emojis)
                top_emojis = emoji_counts.most_common(10)
                
                emoji_df = pd.DataFrame(top_emojis, columns=['Emoji', 'Count'])
                fig_emojis = px.bar(
                    emoji_df,
                    x='Count',
                    y='Emoji',
                    orientation='h',
                    title="Top 10 Most Used Emojis"
                )
                fig_emojis.update_layout(height=400)
                st.plotly_chart(fig_emojis, use_container_width=True)
            else:
                st.info("No emojis found in the messages.")
        
        with tab5:
            st.subheader("📱 Raw Data")
            
            # Data summary
            st.write(f"**Total Records:** {len(df_filtered)}")
            st.write(f"**Columns:** {list(df_filtered.columns)}")
            
            # Display data
            st.dataframe(df_filtered.head(100), use_container_width=True)
            
            # Download option
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Download Processed Data as CSV",
                data=csv,
                file_name="whatsapp_chat_analysis.csv",
                mime="text/csv"
            )
    
    else:
        st.error("❌ Failed to parse the chat file. Please check the file format.")

else:
    # Instructions
    st.markdown("""
    ## 📱 Welcome to WhatsApp Chat Analyzer!
    
    This app helps you analyze your WhatsApp chat exports with comprehensive insights.
    
    ### 🚀 How to Use:
    
    1. **Export your WhatsApp chat:**
       - Open WhatsApp → Select Chat → Menu (3 dots) → More → Export Chat
       - Choose "Without Media" to get a .txt file
    
    2. **Upload the file:**
       - Click "Browse files" above
       - Select your exported .txt file
    
    3. **Explore the analysis:**
       - View overview statistics
       - Analyze individual authors
       - See timeline patterns
       - Generate word clouds
       - Download processed data
    
    ### 📊 Features:
    - ✅ Message statistics and metrics
    - ✅ Author-wise analysis
    - ✅ Timeline visualization
    - ✅ Word cloud generation
    - ✅ Emoji analysis
    - ✅ Most common words
    - ✅ Data filtering and export
    
    ### 📁 Supported Formats:
    - WhatsApp Android exports
    - WhatsApp iOS exports
    - Text files (.txt)
    """)
    
    # Sample data preview
    st.subheader("📋 Sample Data Format")
    st.code("""
    Android Format:
    18/10/2025, 9:30 PM - John Doe: Hello! How are you?
    18/10/2025, 9:31 PM - Jane Smith: I'm good, thanks!
    
    iOS Format:
    [18/10/2025, 9:30:00 PM] John Doe: Hello! How are you?
    [18/10/2025, 9:31:00 PM] Jane Smith: I'm good, thanks!
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>📱 WhatsApp Chat Analyzer | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
