from langchain_ai21.chat_models import ChatAI21
from langchain_groq import ChatGroq
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import SystemMessage,BaseMessage,HumanMessage,AIMessage,ToolMessage
from langgraph.types import interrupt,Command 
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing import TypedDict,Annotated, List, Dict, Literal,Optional
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from pydantic import BaseModel
from json_repair import repair_json
import re
from typing import List
from dotenv import load_dotenv
import json
import os
load_dotenv()


class PptState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    outline: Dict
    detailed_slides: List[Dict]
    current_slide_index: int
    feedback: str
    topic: str
    research_data: Dict
    action: Literal[ "continue_slide", "update_outline", "update_slide", "complete", '' ]
    tool_caller: Literal["generate_outline","generate_slide_detail"]
class OutlineSlide(BaseModel):
    slide_number: int
    slide_title: str
class OutlineOutput(BaseModel):
    title: str
    total_slides: int
    slides: List[OutlineSlide]
class DetailedPoint(BaseModel):
    key_point: str
    explanation: str
class DetailedSlideOutput(BaseModel):
    slide_number: int
    slide_title: str
    layout: Literal[
        "bullets",
        "bullets_with_text",
        "paragraph",
        "two_column",
        "mixed"
    ]
    intro_line: Optional[str] = None
    bullet_points: Optional[List[str]] = None
    supporting_text: Optional[str] = None
    paragraphs: Optional[List[str]] = None

model = ChatGroq(model="llama-3.3-70b-versatile")

searchTool = TavilySearchResults(max_results=5)
tools = [searchTool]
model_with_tools = model.bind_tools(tools)
outline_parser = PydanticOutputParser(pydantic_object= OutlineOutput)
# outline_parser = PydanticOutputParser(pydantic_object= OutlineSlide)
detailed_parser = PydanticOutputParser(pydantic_object= DetailedSlideOutput)

OUTLINE_SYSTEM_PROMPT = SystemMessage(
    content=f"""You are an expert presentation designer.

Your task:
Generate ONLY the presentation title and slide titles.
    
{outline_parser.get_format_instructions()} 

MANDATORY: For each slide, identify 1-2 specific research sources/statistics needed.
Include in your reasoning: "Research needed: [specific query]".

Strict Rules:
- Generate EXACTLY the number of slides requested by the user.
- Do NOT generate key points.
- Do NOT generate slide content.
- Only generate slide_number and slide_title.
- Slide numbers must start from 1 and increment sequentially.
- Ensure logical flow from introduction to conclusion.
- Keep slide titles concise but descriptive.
- Use tools only if factual accuracy is required.
- Return ONLY valid JSON.
- No markdown.
- No explanations.
""")


DETAIL_SYSTEM_PROMPT = SystemMessage(
content=f"""
You are a professional presentation designer.

Your job is to generate visually balanced slide content for a PowerPoint presentation.

For each slide choose the most appropriate layout or a mix of layouts  and generate structured content.

Available layouts:
- bullets
- bullets_with_text
- paragraph
- mixed


{detailed_parser.get_format_instructions()}

CRITICAL REQUIREMENTS:
- EVERY slide must include AT LEAST ONE statistic or research finding
- Cite source: "According to [Organization/Study], [specific fact]"
- Include exact numbers, dates, percentages
- Use search tool to find: "[topic] + statistics 2025" or "[topic] + latest research"

General Principles:
Slides should be informative but not crowded.
A good slide often combines short explanations with bullet points.

Content Elements:
Slides may contain combination of:
- intro_line (a introductory sentence)
- bullet_points (key ideas)
- supporting_text (a short insight or explanation)
- paragraphs (short explanation text)


Layout Guidelines:

bullets
- 6-8 bullet points
- each bullet 6–12 words
- may optionally include a intro_line before bullets
- Some bullet slides should include a short explanation sentence before or after the bullets.

bullets_with_text
- 5-8 bullet points
- include supporting_text (1 short explanation sentence)
- may optionally include intro_line
- Some bullet slides should include a short explanation sentence before or after the bullets.

paragraph
- 3-5 short paragraphs
- each paragraph max 40 words
- optionally include a short intro_line

Slides may contain a combination of:

- intro_line (1 explanation sentence)
- bullet_points (3–5 bullets)
- paragraphs (1 short paragraph)
- supporting_text (1 insight sentence)

Good slides often combine elements.
Example structure:

intro_line
bullet_points
supporting_text


Layout Distribution Rules:

- 40–50% slides → bullets
- 20–30% slides → bullets_with_text
- 10–20% slides → paragraph

Variation Rules:
Do NOT generate the same layout repeatedly.
Use different content styles across slides.


Content Density Rules:
Slides should contain roughly 80-120 words total.
Content must fit comfortably on a PowerPoint slide.

Quality Rules:
- Bullet points should be concise and informative.
- Avoid repeating the same wording.
- Ensure the slide content is clear when presented visually.
Return JSON only.
"""
)

def generate_outline_node(state: PptState):
    """Step 1: Generate presentation outline"""
    messages = state["messages"] + [OUTLINE_SYSTEM_PROMPT]
    result = model_with_tools.invoke(messages)
    output = {
        'messages':[result],
        'current_slide_index':0,
        "tool_caller": "generate_outline",
            } 
    if result.content:
        try:
            output['outline'] = outline_parser.parse(repair_json(str(result.content))).model_dump()
            print("output['outline']",output['outline'])
        except json.JSONDecodeError as e:
            print('generate_outline_node',e)
    return output

def generate_slide_detail_node(state: PptState):
    """Generate detailed content using research data"""
    outline = state['outline']
    current_index = state['current_slide_index']
    detailed_slides = state.get('detailed_slides', [])
    total_slides = len(outline['slides'])
    current_slide = outline['slides'][current_index]
    
    if current_index >= total_slides:
        return {"action": "complete"}
    
    # Get research data for this slide
    research = state.get('research_data', {}).get(current_slide['slide_title'], [])
    
    output = {
        "tool_caller": "generate_slide_detail",
        "current_slide_index": current_index
    }
    
    if state['action'] == "update_slide":
        # Handle feedback case (existing logic)
        feedback = state['feedback']
        last_slide = detailed_slides.pop()
        prompt = HumanMessage(content=f"""
Update this slide with research data:
Research: {research}
Current Content: {last_slide}
Feedback: {feedback}
        """)
    else:
        prompt = HumanMessage(content=f"""
Generate slide using this research data:
Presentation: {outline['title']}
Slide: {current_slide['slide_title']} (#{current_slide['slide_number']})
RESEARCH RESULTS: {research}

MANDATORY: Include 2-3 specific statistics with sources in bullets/intro/supporting_text
Format: "X million tons annually (Source 2026)"
        """)
    
    messages = [DETAIL_SYSTEM_PROMPT, prompt]
    result = model_with_tools.invoke(messages)
    
    if result.content:
        try:
            new_slide = detailed_parser.parse(repair_json(str(result.content))).model_dump()
            detailed_slides.append(new_slide)
            output['detailed_slides'] = detailed_slides
            output['current_slide_index'] = current_index + 1
        except json.JSONDecodeError:
            pass
    
    if output['current_slide_index'] == total_slides:
        output["action"] = "complete"
    output['messages'] = [result]
    return output



def research_slide_node(state: PptState):
    """Research current slide before content generation"""
    current_slide = state['outline']['slides'][state['current_slide_index']]
    slide_title = current_slide['slide_title']
    
    # Use search tool to get real data
    research_query = f"{slide_title} statistics 2026 research report"
    research_result = searchTool.invoke({"query": research_query})
    
    return {
        "research_data": {slide_title: research_result},
        "messages": [ToolMessage(content=str(research_result), tool_call_id="research")],
        "tool_caller": "generate_slide_detail"
    }



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


def tools_condition(state: PptState):
    """Route to tools if last message has tool calls"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "__end__"

DB_URL = os.getenv("PPT_URL")



def build_workflow():
    workflow = StateGraph(PptState)
    workflow.add_node("generate_outline", generate_outline_node)
    workflow.add_node("research_slide", research_slide_node)
    workflow.add_node("generate_slide_detail", generate_slide_detail_node)
    workflow.add_node("human_decision", human_decision)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.add_edge(START, "generate_outline")

    workflow.add_conditional_edges( #done
        "generate_outline",
        tools_condition,
        {
            "tools": "tools",
            "__end__": "human_decision",
        },
    )

    workflow.add_conditional_edges(
        "human_decision",
        route_after_human,
        {
            "generate_outline": "generate_outline",
            "generate_slide_detail": "research_slide",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "research_slide",
        tools_condition,
        {"tools": "tools", "__end__": "generate_slide_detail"},
    )

    workflow.add_conditional_edges(
        "generate_slide_detail",
        tools_condition,
        {
            "tools": "tools",
            "__end__": "human_decision",
        },
    )
    workflow.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "generate_outline": "generate_outline",
            "generate_slide_detail": "generate_slide_detail",
        },
    )

    return workflow

def create_ckeckpointer_and_graph(db_url: str):
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
    return checkpointer, graph
