import streamlit as st
import uuid
from datetime import datetime
from dotenv import load_dotenv
import requests
import os
load_dotenv()
API_URL = os.getenv('API_URL')

# Page config
st.set_page_config(page_title="Ritey PPT", layout="wide")

# Initialize session state
if "sessions" not in st.session_state:
    st.session_state.sessions = []
if "current_session" not in st.session_state:
    st.session_state.current_session = None
if "show_form" not in st.session_state:
    st.session_state.show_form = False

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("### Activity")
    
    # New PPT Button
    if st.button("New PPT", use_container_width=True, key="new_ppt_btn"):
        st.session_state.show_form = True
    
    st.divider()
    
    # Display existing sessions
    if st.session_state.sessions:
        st.markdown("**Recent Sessions**")
        
        for idx, session in enumerate(st.session_state.sessions):
            col1, col2 = st.columns([0.85, 0.15])
            
            with col1:
                # Click to switch session
                if st.button(
                    f" {session['topic'][:20].capitalize()}...",
                    key=f"session_{idx}",
                    use_container_width=True,
                ):
                    st.session_state.current_session = idx
                    st.session_state.show_form = False
                    st.rerun()
                
                # Display metadata
                st.caption(f"🔹 {session['num_slides']} slides • {session['created_at']}")
            
            with col2:
                # Delete button
                if st.button("🗑️", key=f"delete_{idx}", help="Delete session"):
                    st.session_state.sessions.pop(idx)
                    if st.session_state.current_session == idx:
                        st.session_state.current_session = None
                    st.rerun()
    else:
        st.info("📭 No sessions yet. Create your first PPT!")

# ============ MAIN CONTENT ============

# Show form when "New PPT" clicked
if st.session_state.show_form:
    st.title(" Create New Presentation")
    
    with st.form("ppt_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            topic = st.text_input(
                "📝 Presentation Topic",
                placeholder="e.g., Introduction to AI, Climate Change...",
                help="What should your presentation be about?"
            )
        
        with col2:
            num_slides = st.number_input(
                "🔢 Number of Slides",
                min_value=3,
                max_value=50,
                value=5,
                step=1,
                help="How many slides do you want?"
            )
        
        submitted = st.form_submit_button("✅ Create Presentation", use_container_width=True)
        
        if submitted and topic and num_slides:
            # Generate UUID for checkpoint
            thread_id = str(uuid.uuid4())
            
            # Create session
            new_session = {
                "id": thread_id,
                "topic": topic,
                "num_slides": num_slides,
                "created_at": datetime.now().strftime("%b %d, %H:%M"),
                "status": "outline_generated",
                "outline": None,
                "detailed_slides": [],
            }
            
            # Add to sessions and set as current
            st.session_state.sessions.insert(0, new_session)
            st.session_state.current_session = 0
            st.session_state.show_form = False
            
            # Show success message
            st.success(f"✨ Session created! Thread ID: `{thread_id}`")
            st.info(f"📋 Topic: **{topic}** | Slides: **{num_slides}**")
            
            st.rerun()

# Show current session
elif st.session_state.current_session is not None:
    session = st.session_state.sessions[st.session_state.current_session]
    
    st.title(f"🎯 {session['topic']}")
    
    # Session info
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Slides", session['num_slides'])
    col2.metric("Thread ID", session['id'][:8] + "...")
    col3.metric("Created", session['created_at'])
    col4.metric("Status", session['status'])
    
    st.divider()
    
    # Tabs for workflow
    tab1, tab2, tab3 = st.tabs(["📊 Outline", "🎨 Slides", "📥 Download"])
    
    with tab1:
        st.subheader("Presentation Outline")
        if session['outline']:
            st.json(session['outline'])
        else:
            st.info("Click 'Generate Outline' to create your outline")
            if st.button("🚀 Generate Outline"):
                st.warning("🔄 Generating outline... (Connected to backend)")
                # TODO: Call /api/outline endpoint with:
                # {
                #     "topic": session['topic'],
                #     "num_slide": session['num_slides'],
                #     "thread_id": session['id']
                # }
    
    with tab2:
        st.subheader("Slide Details")
        if session['detailed_slides']:
            for idx, slide in enumerate(session['detailed_slides']):
                with st.expander(f"Slide {idx + 1}: {slide.get('title', 'Untitled')}"):
                    st.write(slide)
        else:
            st.info("Generate outline first, then create slide details")
    
    with tab3:
        st.subheader("Download Presentation")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Generate PPT", use_container_width=True):
                st.warning("🔄 Generating PowerPoint... (Connected to backend)")
                # TODO: Call /ppt endpoint with: {"thread_id": session['id']}
        
        with col2:
            st.button("📂 Open Folder", use_container_width=True, disabled=True)

else:
    # Welcome screen
    st.title("Welcome to Ritey PPT")
    st.subheader('Build Easy, Build Fast, Build Smart')
    
    st.markdown("""
    ### 🚀 Get Started
    
    Click **"✨ New PPT"** in the sidebar to:
    1. Enter your presentation topic
    2. Choose number of slides
    3. Start building your presentation!
    
    ---
    
    ### ✨ Features
    - 🤖 **AI-Powered Outlines**: Automatic content generation
    - ✏️ **Interactive Editing**: Review and revise each slide
    - 📊 **Smart Formatting**: Beautiful slide layouts
    - 💾 **Session Persistence**: Your work is always saved
    
    ---
    
    ### 📖 How It Works
    1. **Create** → Describe your topic
    2. **Review** → Check AI-generated outline
    3. **Refine** → Provide feedback on slides
    4. **Download** → Get your PPT file
    """)
    
    # Example cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📌 **Business**\nCreate pitches & reports")
    with col2:
        st.info("🎓 **Education**\nBuild lesson slides")
    with col3:
        st.info("🎨 **Creative**\nDesign portfolios")