import streamlit as st
from hindi_demo_hitl_1 import chatbot
from langgraph.types import interrupt,Command

st.set_page_config(page_title="Chatbot", layout="centered")
st.title("🤖 My Chatbot")
# st.title("🤖 My Ritu Chatbot")


if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = 'ritu-thread-1'

if "pending_interrupt" not in st.session_state:
    st.session_state.pending_interrupt = None

if "regen_feedback" not in st.session_state:
    st.session_state.regen_feedback = ''

for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.write(msg['content'])

# Chat input
# user_input = st.chat_input('Ritu Type hear...')
user_input = st.chat_input('Type hear...')


if user_input:
    # show user message
    st.session_state.messages.append({
        'role':'user',
        "content":user_input
    })
    with st.chat_message('user'):
        st.write(user_input)
     
    # invoke graph
    config = {"configurable":{"thread_id":st.session_state.thread_id}}
    result = chatbot.invoke(
        {'query':user_input},
        config=config
        )
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["definition"].content
    })

    with st.chat_message('assistant'):
        st.write(result["definition"].content)


    # INTERRUPT HANDLING
    if "__interrupt__" in result:
        interrupt_data = result['__interrupt__'][0].value
        st.session_state.pending_interrupt = interrupt_data

    
if st.session_state.pending_interrupt:
    st.divider()
    st.subheader("🤔 What would you like to do?")
    
    col1,col2 = st.columns(2)

    with col1:
        if st.button("✅ Continue to Hindi"):
            
            st.session_state.messages.append({
                "role": "user",
                "content": "Continue to Hindi"
            })
            
            result = chatbot.invoke(
                Command(resume={"action": "continue"}),
                config={"configurable": {"thread_id": st.session_state.thread_id}}
            )
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["hindi"].content
            })

            st.session_state.pending_interrupt = None
            st.rerun()
    with col2:
        feedback = st.text_input(
                "🔁 Regenerate with feedback",
                placeholder="Explain in simpler words...",
                value=st.session_state.regen_feedback,
                key="regen_feedback"
            )
        
        if feedback:
            print('inside feedback',feedback)
            result = chatbot.invoke(Command(
                resume={
                    "action": "regenerate",
                    "instruction": feedback
                }),
                config={"configurable": {"thread_id": st.session_state.thread_id}}
                )
            st.session_state.messages.append({
                    "role": "user",
                    "content": result['feedback'].content
                })
        
            st.session_state.messages.append({
                    "role": "assistant",
                    "content": result['definition'].content
                })

            if "__interrupt__" in result:
                interrupt_data = result["__interrupt__"][0].value
                st.session_state.pending_interrupt = interrupt_data
                # st.session_state.regen_feedback = ''
                
            
            else:
                st.session_state.pending_interrupt = None
            del st.session_state.regen_feedback    
            st.rerun()