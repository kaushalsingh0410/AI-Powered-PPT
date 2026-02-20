from langchain_ai21.chat_models import ChatAI21
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import SystemMessage,BaseMessage,HumanMessage,AIMessage
from langgraph.types import interrupt 
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode,tools_condition
from typing import TypedDict,Annotated, List, Dict, Literal
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import json
import os

load_dotenv()


class DetailedPoint(BaseModel):
    key_point: str
    example: str

class DetailedSlideOutput(BaseModel):
    slide_number: int
    slide_title: str
    detailed_content: List[DetailedPoint]


class OutlineOutput(BaseModel):
    title: str
    total_slides: int
    slides: List[DetailedSlideOutput]


model = ChatAI21(model = 'jamba-mini-2-2026-01')
searchTool = TavilySearchResults(max_results=3)
tools = [searchTool]
# model_with_tools = model.bind_tools(tools)




models_with_outline = model.bind_tools(tools).with_structured_output(OutlineOutput)
models_with_detailed = model.bind_tools(tools).with_structured_output(DetailedSlideOutput)
# structured_detail_model = model.with_structured_output()




class PptState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    outline: Dict
    detailed_slides: List[Dict]
    current_slide_index: int
    feedback: str
    topic: str
    action: Literal[
        "continue_slide",
        # "continue_next",
        "update_outline",
        "update_slide",
        "complete",
        ''
    ]
    tool_caller: Literal[
        "generate_outline",
        "generate_slide_detail"
    ]


OUTLINE_SYSTEM_PROMPT = SystemMessage(
    content="""
You are an expert presentation designer and content strategist.

Your task: Create a STRUCTURED OUTLINE for a PowerPoint presentation.

Output format (JSON):
{
    "title":"Main presentation title",
    "total_slides": number,
    "slides":[
        { 
            "slide_number":1,
            "slide_title": "Title of the slide"
            "key_points": ["Point 1","Point 2","Point 3",...]
            "content_type": "introduction/explanation/comparison/conclusion"
        }
    ]
}

Rules:
- Create a logical flow from introduction to conclusion
- Each slide should have 3-5 key points
- Be specific about what each slide will cover
- Ensure comprehensive coverage of the topic
- Use tools to research if needed for accuracy
- Return ONLY valid JSON, no additional text
"""
)


DETAIL_SYSTEM_PROMPT = SystemMessage(
    content="""
You are an expert content writer for presentations.

Your task: Generate DETAILED, ENGAGING content for a specific slide.

For each key point:
- Provide 2-3 sentences of explanation
- Include relevant examples, statistics, or facts
- Make it clear, concise, and presentation-ready
- Use simple language that's easy to understand

Output format:
{
    "slide_number": number,
    "slide_title": "Title",
    "detailed_content": [
        {
            "key_point":
        }
    ]
}

"""
)

def is_valid_brackets(s: str):
     if s == '':
          return
     stack = []
     bracket_map = {
         '(' : ')',
         '{' : '}',
         '[' : ']',
     }

     if s[0] != '{':
         s = '{' +s

     for char in s:
        if char in bracket_map:
            stack.append(char)

        elif char in bracket_map.values():
                stack.pop()

     if s[-1] not in ['"',']','}']:
         s = s+'"'
     for char in stack[::-1]:
         s += bracket_map[char]
     return s

def json_to_python(fixed_text):
    if "```json" in fixed_text:
        fixed_text = fixed_text.replace("```json", "").replace("```", "").strip()
    elif "```" in fixed_text:
        fixed_text = fixed_text.replace("```", "").strip()
    return fixed_text


def generate_outline_node(state: PptState):
    """Step 1: Generate presentation outline"""
    print('inside generate_outline_node')
    messages = state["messages"] + [OUTLINE_SYSTEM_PROMPT]
    result = models_with_outline.invoke(messages)
    print('result',result)
    output = {
        'messages':[result],
        'current_slide_index':0,
        "tool_caller": "generate_outline",
            } 

    if result.content:
        try:
            # outline = json_to_python(result.content)
            # outline = json.loads(outline)
            outline = result.model_dump()
        except json.JSONDecodeError as e:
            # try:
            #     outline = json.loads(is_valid_brackets(outline))
            #     print('outline 3',outline)
            # except json.JSONDecodeError as e:
            #     print('generate_outline_node',e)
            print('generate_outline_node',e)
            # print(result.content)
        output['outline'] = outline
        
    # print("state before ",state)
    return output


# def generate_outline_node(state: PptState):
#     """Step 1: Generate presentation outline"""

#     messages = state["messages"] + [OUTLINE_SYSTEM_PROMPT]

#     # Step 1: allow tool usage
#     tool_response = model_with_tools.invoke(messages)

#     # If model called tool → let LangGraph route
#     if tool_response.tool_calls:
#         return {
#             "messages": [tool_response],
#             "tool_caller": "generate_outline"
#         }

#     # Step 2: After tools resolved → enforce structure
#     structured_result = structured_outline_model.invoke(messages)

#     return {
#         "outline": structured_result.model_dump(),
#         "current_slide_index": 0,
#         "tool_caller": "generate_outline"
#     }


def generate_slide_detail_node(state: PptState):
    """Step 2: Generate detailed content for current Slide"""

    print('inside generate_slide_detail_node')

    outline = state['outline']
    current_index = state['current_slide_index']
    detailed_slides = state.get('detailed_slides',[])
    total_slides = len(state.get('outline',{}).get('slides',[]))
    # if current_index > state['num_slides']:
    #     return
    if current_index >= total_slides:
        print('inside complete return')
        return {"action": "complete"}
    
    output = {
        "tool_caller": "generate_slide_detail",
    }

    if state['action'] == "update_slide":
        feedback = state['action']
        last_slide = detailed_slides.pop()
        last_outline = outline['slides'][current_index-1]
        output['feedback'] = ''
        output['action'] = ''

        prompt = HumanMessage(
            content=f"""
You are updating a single slide in a PowerPoint presentation.
Presentation Title:
{state['outline']['title']}

Outline of the slide:
{last_outline}

Current Slide Content:
{last_slide}

User Feedback:
{feedback}
"""
        )
    else:
        print('current_index',current_index)
        current_slide = outline['slides'][int(current_index)]
        output['current_slide_index'] = current_index +1
        print('first output',output)

        prompt = HumanMessage(
            content=f"""Generate detailede content for this slide:
Slide Number: {current_slide['slide_title']}
Key Points: {', '.join(current_slide['key_points'])}
Content Type: {current_slide['content_type']}

Provide comprehensive, presentation-ready content."""
    )

    messages = [DETAIL_SYSTEM_PROMPT,prompt]
    result = models_with_detailed.invoke(messages)
    print('result.content',result)

    try:
        # print('inside first try')
        # detailed_slide = json_to_python(result.content)
        # detailed_slide = json.loads(detailed_slide)
        detailed_slide = result.model_dump()
        
    except json.JSONDecodeError as e:
        # print('before is_valid_brackets',detailed_slide)
        # print('after is_valid_brackets',is_valid_brackets(detailed_slide))
        # try:
        #     detailed_slide = json.loads(is_valid_brackets(detailed_slide))
        # except json.JSONDecodeError as e:
        #     print('generate_slide_detail_node inside',e)
        #     detailed_slide = is_valid_brackets(detailed_slide)
        print('generate_slide_detail_node inside',e)
            
    detailed_slides.append(detailed_slide)
    output['messages'] = [result]
    output['detailed_slides'] = detailed_slides
    print('first output',output)

    return output


def route_after_tools(state: PptState):
    return state["tool_caller"]


def human_decision(state: PptState):
    decision = interrupt({})
    print('inside human_decision')
    print('decision',decision)
    # print('state',state)

    if decision['action'] == "update_outline":
        print('inside human_decision update_outline')

        return {
            'action': "update_outline",
            "messages":[decision['feedback']]
            }
        
    elif decision['action'] == 'continue_slide':
        print('inside human_decision continue_slide')
        return {'action':'continue_slide'}
    
    elif decision['action'] == 'update_slide':
        print('inside human_decision update_slide')
        return {'action':'update_slide'}
    

    
def route_after_human(state: PptState):
    action = state['action']
    if action == 'update_outline':
        return "generate_outline"

    elif action in ('continue_slide', 'update_slide'):
        return "generate_slide_detail"
    elif action == 'complete':  
        return END
    return END

DB_URL = os.getenv("PPT_URL")



def build_workflow():

    workflow = StateGraph(PptState)

    # --------------------
    # Nodes
    # --------------------
    workflow.add_node("generate_outline", generate_outline_node)
    workflow.add_node("generate_slide_detail", generate_slide_detail_node)
    workflow.add_node("human_decision", human_decision)
    workflow.add_node("tools", ToolNode(tools))

    # --------------------
    # Start
    # --------------------
    workflow.add_edge(START, "generate_outline")

    # --------------------
    # Outline → tools OR human
    # --------------------
    workflow.add_conditional_edges(
        "generate_outline",
        tools_condition,
        {
            "tools": "tools",
            "__end__": "human_decision",
        },
    )

    # --------------------
    # Slide → tools OR human
    # --------------------
    workflow.add_conditional_edges(
        "generate_slide_detail",
        tools_condition,
        {
            "tools": "tools",
            "__end__": "human_decision",
        },
    )

    # --------------------
    # Tools → SAME caller
    # --------------------
    workflow.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "generate_outline": "generate_outline",
            "generate_slide_detail": "generate_slide_detail",
        },
    )

    # --------------------
    # Human decides next
    # --------------------
    workflow.add_conditional_edges(
        "human_decision",
        route_after_human,
        {
            "generate_outline": "generate_outline",
            "generate_slide_detail": "generate_slide_detail",
            END: END,
        },
    )
    return workflow


def create_ckeckpointer_and_graph(db_url: str):
    # print('inside create_ckeckpointer_and_graph')
    # print('db_url',db_url)

    if not db_url:
        raise ValueError('Database Url environment variable not set')
    
    connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
        }

    pool = ConnectionPool(
        conninfo=db_url,
            max_size=20,
            kwargs=connection_kwargs,
    )

    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    workflow = build_workflow()
    graph = workflow.compile(checkpointer=checkpointer)
    # print('return checkpointer, graph',checkpointer, graph)
    
    return checkpointer, graph
