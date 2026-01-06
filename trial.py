print('Ritu')

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv

load_dotenv()

llm = HuggingFaceEndpoint(
    repo_id = 'meta-llama/Llama-3.2-3B-Instruct',
    task = 'text-generation',
)

model = ChatHuggingFace(llm = llm)
searchTool = DuckDuckGoSearchRun()
model = model.bind_tools([searchTool])
result = model.invoke('What is the ASN in Warehouse Management System')
print('Ritu: ',result)