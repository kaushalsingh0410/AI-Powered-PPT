import streamlit as st

col1, col2 = st.columns(2)
with col1:
    if st.button('Continue to slide'):
        print('button')
        st.write('button')
        # state = {"action":"continue_slide"}
        # state = requests.post(f'{API_URL}/states/',json=state)
        # state = state.json()
        # st.session_state.state = state
        

with col2:
    feedback = st.text_input("Enter you feedback")
    # print('feedback',feedback)
    # st.write('feedback',feedback)
    if feedback:
        print('feed',feedback)
        st.write('feed',feedback)
    # state = {"action":"update_outline","feedback":feedback}
    # state = requests.post(f'{API_URL}/states/',json=state)
    # state = state.json()
    # st.session_state.state = state
    # 