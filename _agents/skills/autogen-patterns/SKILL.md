---
skill_name: autogen-patterns
description: AutoGen: ConversableAgent, GroupChat, code execution, human-in-loop patterns
category: AI & LLM
version: 1.0.0
---

# AutoGen: Multi-Agent Conversations

## ConversableAgent

```python
import autogen

# Define two conversable agents
agent_a = autogen.ConversableAgent(
    name="Alice",
    system_message="You are helpful assistant",
    llm_config={"config_list": [{"model": "gpt-4"}]}
)

agent_b = autogen.ConversableAgent(
    name="Bob",
    system_message="You are expert analyst",
    llm_config={"config_list": [{"model": "gpt-4"}]}
)

# Simple two-agent conversation
chat_result = agent_a.initiate_chat(
    agent_b,
    message="What are the best practices for AI deployment?"
)

print(f"Result: {chat_result.summary}")
```

## GroupChat

```python
# Create multiple agents
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="TERMINATE",
    is_termination_msg=lambda x: "APPROVED" in x.get("content", "")
)

programmer = autogen.AssistantAgent(
    name="Programmer",
    system_message="You write Python code",
    llm_config={"config_list": [{"model": "gpt-4"}]}
)

scientist = autogen.AssistantAgent(
    name="Scientist",
    system_message="You conduct scientific analysis",
    llm_config={"config_list": [{"model": "gpt-4"}]}
)

# Create group chat
group_chat = autogen.GroupChat(
    agents=[user_proxy, programmer, scientist],
    messages=[],
    max_round=10,
    speaker_selection_method="round_robin"
)

# Manager orchestrates conversation
manager = autogen.GroupChatManager(
    groupchat=group_chat,
    llm_config={"config_list": [{"model": "gpt-4"}]}
)

# Start conversation
user_proxy.initiate_chat(
    manager,
    message="Analyze this data and create visualizations"
)
```

## Code Execution

```python
# Agent that can execute code
code_executor = autogen.ConversableAgent(
    name="CodeExecutor",
    system_message="Execute Python code",
    llm_config=False,  # Don't use LLM
    code_execution_config={"work_dir": "code_output"},
    is_termination_msg=lambda x: True
)

programmer = autogen.AssistantAgent(
    name="Programmer",
    system_message="Write Python code to solve problems",
    llm_config={"config_list": [{"model": "gpt-4"}]},
    code_execution_config={"work_dir": "code_output"}
)

# Programmer writes code, executor runs it
programmer.initiate_chat(
    code_executor,
    message="Write code to calculate fibonacci numbers"
)
```

## Human-in-the-Loop

```python
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS",  # Always ask for input
    max_consecutive_auto_reply=1  # Max auto-replies before asking
)

assistant = autogen.AssistantAgent(
    name="Assistant",
    system_message="Helpful assistant",
    llm_config={"config_list": [{"model": "gpt-4"}]}
)

# Requires human approval at each step
user_proxy.initiate_chat(
    assistant,
    message="Help me write a script"
)
```

## Custom Agents

```python
class ManagerAgent(autogen.ConversableAgent):
    """Custom manager agent."""

    def _generate_reply(self, messages, sender, **kwargs):
        # Custom logic
        return ("Manager response", True)

class WorkerAgent(autogen.ConversableAgent):
    """Custom worker agent."""

    def _generate_reply(self, messages, sender, **kwargs):
        # Execute tasks
        return ("Task completed", True)

# Use custom agents
manager = ManagerAgent(name="Manager", llm_config={"config_list": [{"model": "gpt-4"}]})
worker = WorkerAgent(name="Worker", llm_config=False)
```

## Function Calling

```python
def search_web(query: str) -> str:
    """Search the web."""
    return f"Results for {query}"

def calculate(expression: str) -> str:
    """Calculate expression."""
    return str(eval(expression))

# Define callable functions
functions = [
    {
        "name": "search_web",
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    }
]

agent = autogen.AssistantAgent(
    name="FunctionCaller",
    system_message="Use available functions to help",
    llm_config={"config_list": [{"model": "gpt-4"}]},
    function_map={"search_web": search_web}
)

# Agent calls functions as needed
agent.initiate_chat(
    autogen.UserProxyAgent(name="User"),
    message="Search for latest AI news"
)
```

## Dynamic Conversation Flow

```python
class ConversationManager:
    def __init__(self):
        self.agents = {}
        self.conversation_history = []

    def add_agent(self, name: str, agent):
        self.agents[name] = agent

    def route_conversation(self, topic: str):
        """Route to appropriate agent."""
        if "coding" in topic:
            return self.agents["programmer"]
        elif "analysis" in topic:
            return self.agents["analyst"]
        else:
            return self.agents["general"]

    def multi_round_conversation(self, initial_msg: str, rounds: int = 3):
        """Multiple rounds of conversation."""
        current_msg = initial_msg

        for round_num in range(rounds):
            agent = self.route_conversation(current_msg)
            response = agent._generate_reply([{"content": current_msg}], None)
            current_msg = response[0]
            self.conversation_history.append(current_msg)

        return current_msg

manager = ConversationManager()
manager.add_agent("programmer", programmer_agent)
manager.add_agent("analyst", analyst_agent)
manager.add_agent("general", general_agent)

result = manager.multi_round_conversation("Help me solve this problem")
```

## Error Handling

```python
def safe_chat(agent1, agent2, message: str, max_retries: int = 3):
    """Safely run chat with error handling."""
    for attempt in range(max_retries):
        try:
            result = agent1.initiate_chat(agent2, message=message)
            return result
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                raise

# Usage
result = safe_chat(agent1, agent2, "Your message")
```

## Key Takeaways

- ConversableAgent enables flexible conversations
- GroupChat orchestrates multiple agents
- Code execution agents run generated code
- Human-in-the-loop adds approval gates
- Custom agents allow specialized behavior
- Function calling enables tool use
- Dynamic routing directs conversations
- Error handling improves robustness
