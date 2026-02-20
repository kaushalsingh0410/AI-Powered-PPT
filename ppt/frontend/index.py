import streamlit as st
from datetime import datetime
import requests
import os
import json
from dotenv import load_dotenv
from streamlit_logger import setup_streamlit_logger
logger = setup_streamlit_logger()

load_dotenv()
API_URL = os.getenv('API_URL')

# Page config
st.set_page_config(page_title="Ritey PPT", layout="wide")
# logger.info("Streamlit App Started")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "topic" not in st.session_state:
    st.session_state.topic = False
if "num_slide" not in st.session_state:
    st.session_state.num_slide = False
if "state" not in st.session_state:
    st.session_state.state = False
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0




# ============ API Function ===============
def get_session_from_backend():
    """Fetch all session or state or thread form backen checkpointer"""
    try:
        response = requests.get(f'{API_URL}/threads/')
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error('This is get_session_from_backend %s',e)
        return []
    
def get_session_state(thread_id):
    try:
        response = requests.get(f'{API_URL}/threads/{thread_id}')
        if response.status_code == 200:
            data = response.json()
            # return {"outline":data.get('outline',{}),
            #         "detailed_slides":data.get('detailed_slides',[])
            #         }
            return data
    except Exception as e:
        logger.error('get_session_state error %s',e)
        return None


# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("### Activity")
    
    # New PPT Button
    if st.button("New PPT", use_container_width=True, key="new_ppt_btn"):
        st.session_state.show_form = True
    
    st.divider()
    
    # Display existing sessions
    sessions = get_session_from_backend()
    if sessions:
        st.markdown("**Recent Sessions**")
        for idx, session in enumerate(sessions):
            if st.button(
                f" {session['topic'][:30].capitalize()}...",
                key=f"session_{idx}",
                use_container_width=True,
            ):
                st.session_state.thread_id = session['thread_id']
                st.session_state.show_form = False
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
            thread = requests.post(f'{API_URL}/threads/',json={"topic":topic})
            thread = thread.json()
            thread_id = thread['thread_id']
            st.session_state.thread_id = thread_id
            st.session_state.topic = topic
            st.session_state.num_slide = num_slides
            st.session_state.show_form = False
            st.session_state.active_tab = 0
            st.success(f"✨ Session created! Thread ID: `{thread_id}`")
            st.info(f"📋 Topic: **{topic}** | Slides: **{num_slides}**")
            
            st.rerun()

# Show current session
elif st.session_state.thread_id is not None:

    if st.session_state.topic and st.session_state.num_slide:
        state = {
            "topic": st.session_state.topic,
            "num_slide": st.session_state.num_slide,
            "thread_id": st.session_state.thread_id,
                }
        state = requests.post(f'{API_URL}/states/',json=state)
        st.session_state.num_slide = False
        st.session_state.topic = False
        state = state.json()
        st.session_state.state = state
        
    
    session = get_session_state(st.session_state.thread_id)
    print('st.session_state.thread_id',st.session_state.thread_id)
    print('session',session)

    last_update = session['thread']['last_update']
    topic = session.get('thread',{'topic':'No Title'}).get('topic','No Title')
    st.title(f"🎯 {topic}")
    
    st.divider()
    
    # tab1, tab2, tab3 = st.tabs(["📊 Outline", "🎨 Slides", "📥 Download"])
    tab_names = ["📊 Outline", "🎨 Slides", "📥 Download"]

    selected_tab = st.radio(
        "Navigation",
        tab_names,
        index=st.session_state.active_tab,
        horizontal=True
    )

    st.session_state.active_tab = tab_names.index(selected_tab)
 
    # with tab1:
    if selected_tab == "📊 Outline":
        st.subheader("Presentation Outline")
        if session['outline']:
            st.json(session['outline'])
            # if "__interrupt__" in st.session_state.state:
            if int(last_update) == 1:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button('Continue to slide'):
                        state = {"action":"continue_slide","thread_id":st.session_state.thread_id,'last_update':'2'}
                        state = requests.post(f'{API_URL}/states/',json=state)
                        st.session_state.active_tab = 1
                        st.rerun()

                with col2:
                    feedback = st.text_input("Enter your feedback")
                    if st.button("Submit Feedback"):
                        state = {"action": "update_outline", "feedback": feedback,"thread_id":st.session_state.thread_id}
                        state = requests.post(f'{API_URL}/states/', json=state)
                        st.rerun()
    
    # with tab2:
    elif selected_tab == "🎨 Slides":
        st.subheader("Slide Details")
        if session['detailed_slides']:
            for idx, slide in enumerate(session['detailed_slides']):
                with st.expander(f"Slide {idx + 1}: {slide.get('slide_title', 'Untitled')}"):
                    st.write(slide)
        if int(last_update) == 2:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button('Next'):
                        state = {"action":"continue_slide","thread_id":st.session_state.thread_id}
                        state = requests.post(f'{API_URL}/states/',json=state)
                        # print(state.json())
                        st.session_state.active_tab = 1
                        st.rerun()

                with col2:
                    feedback = st.text_input("Enter your feedback")
                    if st.button("Submit Feedback"):
                        state = {"action": "update_slide", "feedback": feedback,"thread_id":st.session_state.thread_id}
                        state = requests.post(f'{API_URL}/states/', json=state)
                        st.rerun()
    
    # with tab3:
        # if int(last_update) == 3 and session['thread']['img_path'] is None:
    
    elif selected_tab == "📥 Download":
        st.subheader("Download Presentation")
        if int(last_update) == 3 and session['thread']['img_path'] is None:
            if st.button("📥 Generate & Download  PPT", use_container_width=True):
                st.warning("🔄 Generating PowerPoint... (Connected to backend)")
                res = requests.post(f'{API_URL}/ppt/', json={"thread_id": st.session_state.thread_id})
                st.rerun()
                # if res.status_code == 200:
                #     st.success("PPT generated. Refreshing...")
                    
                #     st.download_button(
                #     label="⬇️ Click here to Download PPT",
                #     data=res.content,
                #     file_name=session['thread']['topic'],
                #     mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                # )
        # print("session['thread']['img_path']",session['thread']['img_path'])
        # print("type",type(session['thread']['img_path']))
        if session['thread']['img_path']:
            st.download_button(
                    label="⬇️ Click here to Download PPT",
                    data=requests.post(f'{API_URL}/ppt/', json={"thread_id": st.session_state.thread_id}).content,
                    file_name=session['thread']['topic']+'.pptx',
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )
            
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
