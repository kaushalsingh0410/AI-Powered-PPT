from typing import TypedDict,Annotated,List,Literal,Optional
from langchain_ai21.chat_models import ChatAI21
from langgraph.graph import StateGraph,START,END
from langgraph.types import interrupt,Command
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage,BaseMessage,HumanMessage,AIMessage
from dotenv import load_dotenv

# api_key = 'cc97c84e-8137-476c-8324-ce151112c72d'

# load_dotenv()
model = ChatAI21(model='jamba-mini-1.7-2025-07',api_key = 'cc97c84e-8137-476c-8324-ce151112c72d')

class State(TypedDict):
    messages: Annotated[List[BaseMessage],add_messages]
    query: str
    definition: str
    hindi: str
    action : Literal['continue','regenerate']
    feedback: Optional[str]

def chat(state: State):
    prompt = state['query']
    # result = AIMessage('THis is ai message')
    if state.get('feedback'):
      prompt = f"""
      Original question: {prompt}
      User feedback: {state['feedback']}
      Please regenerate the response considering feedback.
      """
      # result = AIMessage('This is ai feedback')

    result = model.invoke(prompt)

    output = {}
    if state.get('feedback'):
      messages = [HumanMessage(state['feedback']),result]
      output['feedback'] = HumanMessage(state.get('feedback'))
    else:
      messages = [HumanMessage(state['query']),result]
    
    output['messages'] = messages
    output['definition'] = result
    return output


def human_decision(state: State):
  decision = interrupt({
      "question":"What would you like to do?",
      "ai_output": state['definition'],
      "options":["continue","regenerate"],
      "instruction_note":"If regenerate, provide guidance for improvemet"
  })

  return {
      "action":decision['action'],
      "feedback":decision.get("instruction")
  }

def route_after_human(state: State):
  if state['action'] == 'continue':
    return "hindi_chat"
  else:
    return "chat"

def hindi_chat(state: State):
    message = state['definition'].content
    prompt = SystemMessage(content="""You are a expert and profesnal langauge translater your that is to translate english langauge snatence to Hindi language""")
    prompt1 = HumanMessage(content = f"""Convert this english sentance to hindi language
    Text: {message}
    """)
    result = model.invoke([prompt,prompt1])
    # result = AIMessage('This is hindi')
    return {
        "messages":result,
        "hindi":result
        }

graph = StateGraph(State)
graph.add_node('chat',chat)
graph.add_node('human_decision',human_decision)
graph.add_node('hindi_chat',hindi_chat)

graph.add_edge(START,'chat')
graph.add_edge('chat',"human_decision")
graph.add_conditional_edges("human_decision",
               route_after_human,{
                   "chat":"chat",
                   "hindi_chat":"hindi_chat",
               })
graph.add_edge('hindi_chat',END)
checkpointer = MemorySaver()
chatbot = graph.compile(checkpointer = checkpointer)
# chatbot


# thread_id = '128'
# config = {"configurable":{"thread_id":thread_id}}
# result = chatbot.invoke({
#     'query':'this is question'
# },
# config = config)

# print('User Query: ',result['query'])
# print('AI Response: ',result['definition'])
# print("--------------------------------------------------------------")
# print(result['__interrupt__'][0].value['question'])
# decision = int(input('Enter 1 for continue or 2 for regeneration: '))
# if decision ==2:
#   resume = {
#       "instruction" : input(f"""{result['__interrupt__'][0].value['instruction_note']}: """),
#       "action" : "regenerate"
#        }
# else:
#   resume ={
#   "action" : "continue"
#   }
# print('resume',resume)
# result = chatbot.invoke(Command(resume = resume),
#                config = config)



