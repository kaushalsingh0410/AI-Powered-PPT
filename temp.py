# as you Know I'm working on ppt genration using gen ai
# 1. My first step is to genrate lot of content for the ppt
# 2. then second step genrate detail text of each slide

# can you help me to achive this 
# this is my code 


# from langchain_ai21.chat_models import ChatAI21
# from langchain_community.tools.tavily_search import TavilySearchResults
# from langchain_core.messages import SystemMessage,BaseMessage,HumanMessage
# from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
# from huggingface_hub import InferenceClient
# from langgraph.graph import StateGraph,START,END
# from langgraph.graph.message import add_messages
# from langgraph.prebuilt import ToolNode, tools_condition
# from typing import TypedDict,Annotated
# from dotenv import load_dotenv

# load_dotenv()

# model = ChatAI21(model = 'jamba-mini-1.7-2025-07')
# searchTool = TavilySearchResults(max_results=3)
# tools = [searchTool]
# model_with_tools = model.bind_tools(tools)

# SYSTEM_PROMPT = SystemMessage(
#     content="""
# You are a knowledgeable, reliable, and structured AI research assistant.

# Your goals:
# - Produce high-quality, accurate, and well-organized information on ANY topic.
# - Think step-by-step before answering.
# - Decide intelligently whether external tools are needed.

# Tool usage rules:
# - Use tools ONLY when the information is:
#   • Unknown to you
#   • Requires up-to-date data
#   • Needs real-world examples, statistics, or references
# - NEVER return raw tool output.
# - ALWAYS analyze, summarize, and rewrite tool results in your own words.

# Answer quality rules:
# - Be clear, concise, and logically structured.
# - Prefer explanation over listing.
# - Adapt depth based on topic complexity.
# - Use examples, analogies, or code ONLY when relevant.
# - Avoid hallucination. If unsure, say so.

# Default answer structure:
# 1. Clear definition or overview
# 2. Core explanation (how / why it works)
# 3. Practical examples (if applicable)
# 4. Common misconceptions or pitfalls
# 5. When and why this topic is useful

# Respond like a knowledgeable teacher and researcher, not a search engine.
# """
# )

# class PptTestState(TypedDict):
#     messages: Annotated[list[BaseMessage],add_messages]


# def chat_node(state: PptTestState):
#     message = state['messages']
#     result = model_with_tools.invoke(message)
#     return {'messages':result}

# tool_node = ToolNode(tools)

# graph = StateGraph(PptTestState)
# graph.add_node("chat_node",chat_node)
# graph.add_node("tools",tool_node)

# graph.add_edge(START,'chat_node')
# graph.add_conditional_edges('chat_node',tools_condition)
# graph.add_edge('tools','chat_node')

# chatbot = graph.compile()

# result = chatbot.invoke({'messages':[
# SYSTEM_PROMPT,
# HumanMessage(content='Create a 5 page ppt on photosynthesis in plants')]})

# this is the output

# {'messages': [SystemMessage(content='\nYou are a knowledgeable, reliable, and structured AI research assistant.\n\nYour goals:\n- Produce high-quality, accurate, and well-organized information on ANY topic.\n- Think step-by-step before answering.\n- Decide intelligently whether external tools are needed.\n\nTool usage rules:\n- Use tools ONLY when the information is:\n  • Unknown to you\n  • Requires up-to-date data\n  • Needs real-world examples, statistics, or references\n- NEVER return raw tool output.\n- ALWAYS analyze, summarize, and rewrite tool results in your own words.\n\nAnswer quality rules:\n- Be clear, concise, and logically structured.\n- Prefer explanation over listing.\n- Adapt depth based on topic complexity.\n- Use examples, analogies, or code ONLY when relevant.\n- Avoid hallucination. If unsure, say so.\n\nDefault answer structure:\n1. Clear definition or overview\n2. Core explanation (how / why it works)\n3. Practical examples (if applicable)\n4. Common misconceptions or pitfalls\n5. When and why this topic is useful\n\nRespond like a knowledgeable teacher and researcher, not a search engine.\n', additional_kwargs={}, response_metadata={}, id='10d1412a-3fa8-4522-8a05-817c64a6b7b5'),
#   HumanMessage(content='Create a 5 page ppt on photosynthesis in plants', additional_kwargs={}, response_metadata={}, id='b4118f41-e53a-4bb1-bec9-f93b6409e44d'),
#   AIMessage(content="Creating a PowerPoint presentation on photosynthesis in plants involves organizing the content into clear, concise slides with relevant visuals and examples. Here's a step-by-step guide to creating a 5-page PowerPoint presentation on the topic:\n\n### Slide 1: Title Slide\n\n* **Title**: Photosynthesis in Plants\n* **Subtitle**: Understanding the Process of Life\n* **Visuals**: A large image of a plant with sunlight, water, and carbon dioxide.\n* **Footer**: Your name, date, and course.\n\n### Slide 2: Introduction to Photosynthesis\n\n* **Heading**: What is Photosynthesis?\n* **Content**:\n  + Definition of photosynthesis.\n  + Importance of photosynthesis for plants and the ecosystem.\n  + Basic equation: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂.\n* **Visuals**: Diagram showing the basic process of photosynthesis.\n\n### Slide 3: The Process of Photosynthesis\n\n* **Heading**: Step-by-Step Process\n* **Content**:\n  + Light absorption by chlorophyll.\n  + Splitting of water molecules (photolysis).\n  + Reduction phase and formation of glucose.\n  + Release of oxygen as a byproduct.\n* **Visuals**: Flowchart detailing the stages of photosynthesis.\n\n### Slide 4: Key Components and Conditions\n\n* **Heading**: Key Components and Conditions\n* **Content**:\n  + Key components: chlorophyll, water, carbon dioxide, sunlight.\n  + Ideal conditions: temperature, light intensity, and carbon dioxide concentration.\n  + Factors affecting photosynthesis: temperature, light, and CO₂ levels.\n* **Visuals**: Images of chloroplasts and a graph showing the effect of light intensity on photosynthesis.\n\n### Slide 5: Applications and Conclusion\n\n* **Heading**: Applications and Conclusion\n* **Content**:\n  + Applications: food production, oxygen generation, and biofuel development.\n  + Conclusion: Importance of photosynthesis in sustaining life on Earth.\n* **Visuals**: Summary diagram showing the global impact of photosynthesis.\n\n### Additional Notes:\n\n* **Design Tips**: Use consistent font styles and sizes, and choose colors that enhance readability.\n* **Content Tips**: Keep text concise and use bullet points.\n", additional_kwargs={}, response_metadata={}, id='run--054313a8-68ea-4b62-83e9-6b5df42589e6-0')]}
