import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from uuid import uuid4
from datetime import datetime
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.checkpoint.postgres import PostgresSaver
from fastapi.responses import FileResponse
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv
import os
from .database import get_db
from .models import Thread
from .graph import create_ckeckpointer_and_graph
from .ppt_generator import PPTGenerator
from .schemas import Ppt, ThreadResponse, ThreadWithStateResponse

load_dotenv()

BASE_DIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_DIT,"media")
os.makedirs(MEDIA_DIR,exist_ok=True)

PPT_URL = os.getenv('PPT_URL')

app_state = {
    "checkpointer":None,
    "graph":None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # print('inside lifespan')
    try:
        app_state["checkpointer"], app_state['graph'] = create_ckeckpointer_and_graph(PPT_URL)
        # print('lifespan try',app_state)
        yield
    finally:
        try:
            if app_state["checkpointer"]:
                pool = app_state["checkpointer"].pool
                if pool:
                    pool.close()
        except Exception as e:
            print(f'Error closing pool: {e}')

def get_graph_deps():
    # print('inside get_graph_deps')

    if not app_state["graph"]:
        raise RuntimeError("Graph not initialized. Check startup logs.")
    if not app_state["checkpointer"]:
        raise RuntimeError("Checkpointer not initialized. Check startup logs.")
    return app_state["checkpointer"], app_state["graph"]

app = FastAPI(lifespan = lifespan)

@app.post("/states/")
def read_root(ppt: Ppt,db: Session = Depends(get_db), deps: tuple = Depends(get_graph_deps)):
    
    checkpointer, graph = deps
    config = {'configurable':{'thread_id':ppt.thread_id}}

    print('inside read_root')
    print('ppt.topic',ppt.topic)
    print('ppt.num_slide',ppt.num_slide)
    print('ppt.thread_id',ppt.thread_id)
    print('ppt.feedback',ppt.feedback)
    print('ppt.action',ppt.action)
    print('ppt.last_update',ppt.last_update)
    if ppt.topic and ppt.num_slide and ppt.thread_id:
        print('ritu generate_outline')
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

        thread = db.query(Thread).filter(Thread.thread_id == ppt.thread_id).first()
        thread.last_update = '1' 
        db.commit() 
        db.refresh(thread)

        return result
    if ppt.feedback:
        print('ritu feedback')
        state = Command(resume={
            "action": ppt.action,
            "feedback":ppt.feedback
        })
        print('state',state)
        result =  graph.invoke(state,config = config)['messages'][-1].content
        return result
    if ppt.action == 'continue_slide':
        print('ritu action')
        state = Command(resume={
            "action": ppt.action,
        })
        # print('ritu state',state)

        result = graph.invoke(state,config = config)

        if ppt.last_update or result['action'] == "complete":
            thread = db.query(Thread).filter(Thread.thread_id == ppt.thread_id).first()
            thread.last_update = ppt.last_update if ppt.last_update else '3' 
            db.commit() 
            db.refresh(thread) 
        return result['messages'][-1].content

@app.post('/ppt/')
def generate_ppt(ppt: Ppt, deps: tuple = Depends(get_graph_deps),db: Session = Depends(get_db)):
    checkpointer, graph = deps
    try:
        thread = db.query(Thread).filter( Thread.thread_id == ppt.thread_id ).first()
        if not thread.img_path :
            print('inside if')
            config = {"configurable": {"thread_id":ppt.thread_id}}
            
            state = graph.get_state(config).values
            if not state:
                raise HTTPException(state_code = 404,detail="State not found")

            slides = state.get("detailed_slides",[])
            if not slides:
                raise HTTPException(state_code = 404,detail="No slide data available.")
            
            title = state["messages"][0].content.split(':')[-1]
            filename = state["messages"][0].content.split(':')[-1]+f'-{int(datetime.now().timestamp())}.pptx'
            output_path = os.path.join(MEDIA_DIR,filename)
            
            ppt_obj = PPTGenerator(output_path,title)
            ppt_obj.generate_from_list(slides)
            ppt_obj.save()

            thread.img_path = output_path
            db.commit()
            db.refresh(thread)

        return FileResponse(
            path=thread.img_path,
            filename=thread.img_path.split('\\')[-1],
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=500,detail=(e))


@app.post('/threads/',response_model=ThreadResponse)
def create_threads(ppt: Ppt,db: Session = Depends(get_db)):
    thread = Thread(thread_id = str(uuid4()),topic = ppt.topic,last_update = 'update')
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread
 
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
def delete_threads(thread_id:str, db: Session = Depends(get_db),deps: tuple = Depends(get_graph_deps)):
    
    checkpointer, graph = deps
    thread = db.query(Thread).filter(
        Thread.thread_id == thread_id
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    
    try:
        checkpointer.delete_thread(thread_id)
    except Exception as e:
        print('delete_threads Exception: ',e)


    db.delete(thread)
    db.commit()
    return {
        "message":"Thread deleted successfully",
        }

@app.get('/threads/{thread_id}',response_model = ThreadWithStateResponse)
# @app.get('/threads/{thread_id}')
def get_threads(thread_id:str, db: Session = Depends(get_db),deps: tuple = Depends(get_graph_deps)):
    checkpointer, graph = deps
    print('thread_id',thread_id)
    thread = db.query(Thread).filter(
        Thread.thread_id == thread_id
    ).first()
    print('thread',thread)

    if not thread:
        raise HTTPException(status_code=404, detail='Thread not found')
    config = {'configurable':{'thread_id':thread_id}}
    print('config',config)
    
    state = graph.get_state(config).values
    print('outline',state['outline'])
    print('Ritu\n'*4)
    print('outline',state['detailed_slides'])
    # print('state',state)
    return {
        "thread": thread,
        "outline": state.get('outline',{}),
        "detailed_slides": state.get('detailed_slides',[]),
    }

@app.get('/threads/',response_model = List[ThreadResponse])
def list_threads(db: Session = Depends(get_db)):
    return db.query(Thread).order_by(desc(Thread.updated_at)).all()

@app.get('/sessions/')
def list_sessions(deps: tuple = Depends(get_graph_deps)):
    checkpointer, graph = deps
    checkpointers = list(checkpointer.list(config=None))
    thread_id = list({cp.config["configurable"]['thread_id'] for cp in checkpointers})     
    return thread_id


