import sys
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

model = sys.argv[1]
llm = ChatOpenAI(
    openai_api_key="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",
    openai_api_base="https://integrate.api.nvidia.com/v1/chat/completions",
    model_name=model,
    temperature=0.0
)

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="Hello"),
    AIMessage(content="Hi"),
    SystemMessage(content="Another system rule: be brief.")
]
try:
    print(f"Testing {model}...")
    res = llm.invoke(messages)
    print("Success!")
except Exception as e:
    print("Failed:", str(e))
