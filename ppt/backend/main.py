import os
from contextlib 
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .database import get_db
from .models import Thread
from .graph import graph
from .ppt_generator import PPTGenerator
from .schemas import Ppt, ThreadResponse, ThreadWithStateResponse
from typing import List
from uuid import uuid4
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

load_dotenv()

PPT_URL = os.getenv('PPT_URL')
pool = ConnectionPool(PPT_URL,max_size=20)
checkpointer = PostgresSaver(pool)

app = FastAPI()

@app.post("/")
def read_root(ppt: Ppt,db: Session = Depends(get_db)):
    config = {'configurable':{'thread_id':ppt.thread_id}}
    if ppt.topic and ppt.num_slide:
        # print('ritu inside if')
        state = {
            "messages": [HumanMessage(content=f"Create a {ppt.num_slide}-slide presentation outline on: {ppt.topic}")],
            "topic":ppt.topic,
            "outline": {},
            "detailed_slides": [],
            "current_slide_index": 0,
            "feedback": "",
            "action": "",
            "tool_caller": "generate_outline",
        }
        result =  graph.invoke(state,config = config)['messages'][-1].content
        return result
    if ppt.feedback:
        state = Command(resume={
            "action": ppt.action,
            "feedback":ppt.feedback
        })
        result =  graph.invoke(state,config = config)['messages'][-1].content
        return result
    if ppt.action == 'continue_slide':
        state = Command(resume={
            "action": ppt.action,
        })
        result =  graph.invoke(state,config = config)['messages'][-1].content
        return result

@app.post('/ppt/')
def generate_ppt(ppt: Ppt):
    config = {"configurable": {"thread_id":ppt.thread_id}}
    state = graph.get_state(config).values#['detailed_slides']
    ppt = PPTGenerator(state["messages"][0].content.split(':')[-1]+'.pptx')
    # print('ppt title',state["messages"][0].content.split(':')[-1])
    ppt.generate_from_list(state['detailed_slides'])
    ppt.save()
    # print('ritu state type',type(state.values))
    return state 


@app.post('/threads/',response_model=ThreadResponse)
def create_threads(ppt: Ppt,db: Session = Depends(get_db)):
    
    if (not db.query(Thread).filter(
        Thread.thread_id == ppt.thread_id
    ).first()):

        thread = Thread(thread_id = str(uuid4()),topic = ppt.topic,last_update = 'update')
        db.add(thread)
        db.commit()
        db.refresh(thread)
        return thread
    return 
 
@app.put('/threads/{thread_id}')
def update_threads(thread_id:str, ppt: Ppt, db: Session = Depends(get_db)):
    
    thread = db.query(Thread).filter(
        Thread.thread_id == thread_id
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')

    thread.topic = ppt.topic 
    db.commit()
    db.refresh(thread)
    return {
        "message":"Thread update successfully",
        "thread": thread
        }

@app.delete('/threads/{thread_id}')
def delete_threads(thread_id:str, db: Session = Depends(get_db)):
    
    thread = db.query(Thread).filter(
        Thread.thread_id == thread_id
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    
    try:
        graph.checkpointer.delete(thread_id)
    except Exception as e:
        print('delete_threads Exception: ',e)


    db.delete(thread)
    db.commit()
    return {
        "message":"Thread deleted successfully",
        }

@app.get('/threads/{thread_id}',response_model = ThreadWithStateResponse)
def get_threads(thread_id:str, db: Session = Depends(get_db)):
    
    thread = db.query(Thread).filter(
        Thread.thread_id == thread_id
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    config = {'configurable':{'thread_id':thread_id}}
    
    state = graph.get_state(config).values.get('messages',[])
    
    return {
        "thread": thread,
        "state": state
    }

@app.get('/threads/',response_model = List[ThreadResponse])
def list_threads(ppt: Ppt, db: Session = Depends(get_db)):
    return db.query(Thread).order_by(desc(Thread.updated_at)).all()

@app.get('/sessions/')
def list_sessions():
    checkpointers = list(checkpointer.list(config=None))
    thread_id = list({cp.config["configurable"]['thread_id'] for cp in checkpointers}) 
    
    state = "ritu"
    for i in thread_id:
        if i in ['121']:
            try:

                config = {"configurable": {"thread_id":i}}
                state = graph.get_state(config).values
                print('Ritu\n'*4)
                print(i)
                print(state)
                # topic = state["messages"][0].content.split(':')[-1]
                # threads.append({i:topic})
            except Exception as e:
                print('Exception',e)
                # threads.append({i:"No Topic"})
    # except Exception as e:
    #     print('Exception',e)
        
    return str(state)