from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from pydantic import BaseModel
from typing import Optional
from graph import graph

app = FastAPI()

class Ppt(BaseModel):
    feedback: Optional[str] = None
    num_slide: Optional[int] = None
    topic: Optional[str] = None
    action: Optional[str] = None
    thread_id: str

@app.post("/")
def read_root(ppt: Ppt):
    config = {'configurable':{'thread_id':ppt.thread_id}}
    if ppt.topic and ppt.num_slide:
        print('ritu inside if')
        state = {
            "messages": [HumanMessage(content=f"Create a {ppt.num_slide}-slide presentation outline on: {ppt.topic}")],
            "outline": {},
            "detailed_slides": [],
            "current_slide_index": 0,
            "feedback": "",
            "action": "",
            "tool_caller": "generate_outline",
        }
        print('state',state)
        result =  graph.invoke(state,config = config)['outline']
        print('result',result)
        return result
        # return f'topic {ppt.topic} and num_slide {ppt.num_slide}'
    if ppt.feedback:
        print('Ritu inside feedback')
        state = Command(resume={
            "action": ppt.action,
            "feedback":ppt.feedback
        })
        print('ritu this is input_data ',state)
        result =  graph.invoke(state,config = config)['messages'][-1]['content']
        print('ritu this is feedback ',result)
        return result
    if ppt.action == 'continue_slide':
        print('Ritu inside continue_slide')
        state = Command(resume={
            "action": ppt.action,
        })
        print('ritu this is input_data ',state)
        # result =  graph.invoke(state,config = config)['messages'][-1]['content']
        result =  graph.invoke(state,config = config)
        print('ritu this is action ',result)
        print('Ritu\n'*5,'type',type(result))
        print('Ritu\n'*5,'messages',result['messages'])
        print('Ritu\n'*5,'-1',result['messages'][-1])
        print('Ritu\n'*5,'content',result['messages'][-1].content)
        return result
