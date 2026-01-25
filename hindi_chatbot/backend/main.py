from fastapi import FastAPI,HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from graph import chatbot
from langgraph.types import Command
from typing import Optional,Literal

app = FastAPI()

class ChatRequest(BaseModel):
    thread_id: str
    query: Optional[str] = None
    feedback: Optional[str] = None
    action: Optional[Literal['continue','regenerate']] = None
@app.post('/chat')
def chat(req:ChatRequest):
    print('req',req,type(req))
    if req.query:
        # NEW MESSAGE
        input_data = {
            "messages": [HumanMessage(content=req.query)],
            "query": req.query
        }
    else:
        # RESUME INTERRUPT
        input_data = Command(
            resume={
                "action": req.action,
                "instruction": req.feedback,
                "messages": []  # REQUIRED
            }
        )
    result = chatbot.invoke(
        input_data,
        config={"configurable":{'thread_id':req.thread_id}}
    )
    return result 

@app.get("/history/{thread_id}")
def get_history(thread_id: str):
    try:
        # Get conversation history
        state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
        return {
            "thread_id": thread_id,
            "messages": [msg.content for msg in state.values.get('messages', [])],
            "current_state": state.values
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# {
#     "thread_id":"Ritu1",
#     "action":"regenerate",
#     "feedback":"update this"
# }

# {
#     "thread_id":"Ritu1",
#     "query":"Hi ritu"
# }