from fastapi import FastAPI
from pydantic import BaseModel
from typing import Annotated, List, Dict, Literal,Optional

app = FastAPI()

class Ppt(BaseModel):
    feedback: Optional[str]
    num_slide: Optional[int]
    topic: Optional[str]
    




@app.post("/")
def read_root(ppt: Ppt):
    if ppt.get('feedback'):
        pass


