import streamlit as st
import uuid
import requests
from datetime import datetime
import json

# Backend API config
BACKEND_URL = "http://localhost:8000"  # Update if needed

st.set_page_config(page_title="Ritey PPT", layout="wide")

# Initialize minimal session state (only UI flags)
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
if "show_form" not in st.session_state:
    st.session_state.show_form = False

# ============ API FUNCTIONS ============
def get_sessions_from_backend():
    """Fetch all user sessions from backend checkpointer"""
    try:
        response = requests.get(f"{BACKEND_URL}/sessions")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def create_session(topic, num_slides):
    """Create new session via backend"""
    thread_id = str(uuid.uuid4())
    try:
        response = requests.post(f"{BACKEND_URL}/", json={
            "topic": topic,
            "num_slide": num_slides,
            "thread_id": thread_id
        })
        if response.status_code == 200:
            return {
                "id": thread_id,
                "topic": topic,
                "num_slides": num_slides,
                "created_at": datetime.now().strftime("%b %d, %H:%M"),
                "status": "outline_generated",
                "outline": response.json()
            }
    except:
        pass
    return None

def get_session_state(thread_id):
    """Get full session state from backend"""
    try:
        response = requests.post(f"{BACKEND_URL}/ppt", json={"thread_id": thread_id})
        if response.status_code == 200:
            data = response.json()
            return {
                "outline": data.get("outline"),
                "detailed_slides": data.get("detailed_slides", []),
                "status": "slides_complete" if data.get("detailed_slides") else "outline_generated"
            }
    except:
        pass
    return None

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("### 📋 Activity")
    
    # New PPT Button
    if st.button("✨ New PPT", use_container_width=True):
        st.session_state.show_form = True
        st.rerun()
    
    st.divider()
    
    # Load sessions from BACKEND (persistent!)
    sessions = get_sessions_from_backend()
    
    if sessions:
        st.markdown("**Recent Sessions**")
        for session in sessions:
            col1, col2 = st.columns([0.85, 0.15])
            
            with col1:
                if st.button(
                    f"📌 {session['topic'][:25]}...",
                    key=f"session_{session['id']}",
                    use_container_width=True
                ):
                    st.session_state.current_thread_id = session['id']
                    st.session_state.show_form = False
                    st.rerun()
                
                st.caption(f"🔹 {session['num_slides']} slides • {session.get('created_at', 'Just now')}")
            
            with col2:
                if st.button("🗑️", key=f"delete_{session['id']}"):
                    # TODO: Add DELETE /sessions/{thread_id} endpoint
                    st.rerun()
    else:
        st.info("📭 No sessions yet. Create your first PPT!")

# ============ MAIN CONTENT ============
if st.session_state.show_form:
    st.title("🎨 Create New Presentation")
    
    with st.form("ppt_form"):
        col1, col2 = st.columns(2)
        with col1:
            topic = st.text_input("📝 Topic", placeholder="e.g., AI in Healthcare")
        with col2:
            num_slides = st.number_input("🔢 Slides", min_value=3, max_value=20, value=5)
        
        if st.form_submit_button("✅ Generate Outline"):
            if topic:
                with st.spinner("🚀 Creating presentation..."):
                    session = create_session(topic, num_slides)
                    if session:
                        st.session_state.current_thread_id = session['id']
                        st.session_state.show_form = False
                        st.success(f"✨ Outline generated! Thread ID: `{session['id'][:8]}...`")
                        st.rerun()
                    else:
                        st.error("❌ Failed to connect to backend")

elif st.session_state.current_thread_id:
    # Load session state from backend
    session_state = get_session_state(st.session_state.current_thread_id)
    
    # Session header
    st.title(f"🎯 {session_state.get('outline', {}).get('title', 'Loading...')}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Slides", len(session_state.get('detailed_slides', [])))
    col2.metric("Thread ID", st.session_state.current_thread_id[:8] + "...")
    col3.metric("Status", session_state.get('status', 'loading'))
    
    st.divider()
    
    # Workflow tabs
    tab1, tab2, tab3 = st.tabs(["📊 Outline", "🎨 Slides", "📥 Download"])
    
    with tab1:
        if session_state.get('outline'):
            st.json(session_state['outline'])
        else:
            st.warning("No outline found")
    
    with tab2:
        slides = session_state.get('detailed_slides', [])
        if slides:
            for i, slide in enumerate(slides):
                with st.expander(f"Slide {i+1}: {slide.get('slide_title', 'Untitled')}"):
                    st.json(slide)
                    
                    # Feedback buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        feedback = st.text_input("Feedback:", key=f"feedback_{i}")
                        if st.button("✏️ Update Slide", key=f"update_{i}"):
                            # TODO: POST feedback to backend
                            st.info("Updating slide...")
                    with col2:
                        if st.button("✅ Continue", key=f"continue_{i}"):
                            # TODO: POST continue_slide action
                            st.info("Generating next slide...")
        else:
            st.info("Generate outline first")
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Generate PPT", use_container_width=True):
                # Backend already generates PPT file
                st.success("✅ PPT generated! Check backend folder or add download endpoint")
        with col2:
            st.info("📂 File saved on server")

else:
    # Welcome screen
    st.title("Welcome to Ritey PPT")
    st.markdown("""
    **Build Easy, Build Fast, Build Smart**
    
    1. Click **"✨ New PPT"** in sidebar
    2. Enter topic & slide count  
    3. Review AI-generated outline
    4. Refine slides with feedback
    5. Download your PPT!
    """)
