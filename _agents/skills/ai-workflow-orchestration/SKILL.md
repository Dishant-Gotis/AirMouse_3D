---
skill_name: ai-workflow-orchestration
description: AI workflows: LangGraph, CrewAI, AutoGen — state machines, human-in-loop
category: AI & LLM
version: 1.0.0
---

# Workflow Orchestration: State Machines & Automation

## LangGraph Basics

```python
from langgraph.graph import Graph
from langchain.llms import ChatOpenAI

graph = Graph()

# Define nodes
def node_plan(state):
    """Planning node."""
    plan = llm.predict("Create plan for: " + state["goal"])
    return {"plan": plan, "goal": state["goal"]}

def node_execute(state):
    """Execution node."""
    result = execute_plan(state["plan"])
    return {"result": result}

def node_review(state):
    """Review node."""
    review = llm.predict(f"Review result: {state['result']}")
    return {"review": review}

# Add nodes
graph.add_node("planner", node_plan)
graph.add_node("executor", node_execute)
graph.add_node("reviewer", node_review)

# Add edges
graph.add_edge("planner", "executor")
graph.add_edge("executor", "reviewer")

# Conditional edge
def should_revise(state):
    return "revise" in state["review"].lower()

graph.add_conditional_edges(
    "reviewer",
    should_revise,
    {True: "planner", False: "end"}
)

graph.add_edge("reviewer", "end")

# Execute
runnable = graph.compile()
result = runnable.invoke({"goal": "Write a report"})
```

## CrewAI Pattern

```python
from crewai import Agent, Task, Crew

# Define agents with specialized roles
research_agent = Agent(
    role="Research Analyst",
    goal="Gather and analyze information",
    backstory="Expert at finding relevant data"
)

writing_agent = Agent(
    role="Technical Writer",
    goal="Create clear documentation",
    backstory="Writes for technical audiences"
)

# Define tasks
research_task = Task(
    description="Research AI trends in 2024",
    agent=research_agent
)

writing_task = Task(
    description="Write summary of findings",
    agent=writing_agent,
    context=[research_task]  # Depends on research
)

# Create crew
crew = Crew(
    agents=[research_agent, writing_agent],
    tasks=[research_task, writing_task],
    verbose=True
)

# Execute
result = crew.kickoff()
```

## AutoGen Pattern

```python
import autogen

# Define agents
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS"
)

coder = autogen.AssistantAgent(
    name="Coder",
    llm_config={"model": "gpt-4"},
    system_message="You are an expert programmer"
)

analyst = autogen.AssistantAgent(
    name="Analyst",
    llm_config={"model": "gpt-4"},
    system_message="You are a data analyst"
)

# Create conversation group
group_chat = autogen.GroupChat(
    agents=[user_proxy, coder, analyst],
    messages=[],
    max_round=10
)

# Manager orchestrates
manager = autogen.GroupChatManager(
    groupchat=group_chat,
    llm_config={"model": "gpt-4"}
)

# Start conversation
user_proxy.initiate_chat(
    manager,
    message="Analyze this dataset and write code to visualize it"
)
```

## State Machines

```python
from enum import Enum
from typing import Dict, Callable

class State(Enum):
    INIT = 1
    PROCESSING = 2
    COMPLETED = 3
    ERROR = 4

class StateMachine:
    def __init__(self):
        self.state = State.INIT
        self.handlers: Dict[State, Callable] = {}
        self.transitions: Dict[State, Dict[str, State]] = {}

    def register_handler(self, state: State, handler: Callable):
        """Register handler for state."""
        self.handlers[state] = handler

    def register_transition(self, from_state: State, event: str, to_state: State):
        """Register state transition."""
        if from_state not in self.transitions:
            self.transitions[from_state] = {}
        self.transitions[from_state][event] = to_state

    def transition(self, event: str) -> bool:
        """Attempt state transition."""
        if self.state not in self.transitions:
            return False

        if event not in self.transitions[self.state]:
            return False

        self.state = self.transitions[self.state][event]
        return True

    def handle(self, data):
        """Handle current state."""
        if self.state in self.handlers:
            return self.handlers[self.state](data)

# Configure workflow
sm = StateMachine()

sm.register_handler(State.INIT, lambda data: print("Starting..."))
sm.register_handler(State.PROCESSING, lambda data: print(f"Processing {data}"))
sm.register_handler(State.COMPLETED, lambda data: print("Done!"))

sm.register_transition(State.INIT, "start", State.PROCESSING)
sm.register_transition(State.PROCESSING, "finish", State.COMPLETED)
sm.register_transition(State.PROCESSING, "error", State.ERROR)

sm.handle(None)
sm.transition("start")
sm.handle("task data")
sm.transition("finish")
```

## Human-in-the-Loop

```python
class HumanInLoopWorkflow:
    def __init__(self, llm):
        self.llm = llm
        self.approval_required_steps = ["delete", "transfer_funds"]

    def execute_step(self, step_name: str, step_input: str) -> str:
        """Execute with human approval if needed."""
        # Generate action
        action = self.llm.predict(f"Execute: {step_input}")

        # Check if approval required
        if any(keyword in step_name.lower() for keyword in self.approval_required_steps):
            print(f"Proposed action: {action}")
            approval = input("Approve? (yes/no): ")

            if approval.lower() != "yes":
                return "Action cancelled by user"

        # Execute
        return execute_action(action)

class ApprovalQueue:
    def __init__(self):
        self.pending = []

    def submit_for_approval(self, action: str, priority: str = "normal"):
        """Submit action for approval."""
        self.pending.append({
            "action": action,
            "priority": priority,
            "status": "pending"
        })

    def approve(self, action_id: int):
        """Approve action."""
        self.pending[action_id]["status"] = "approved"
        return execute_action(self.pending[action_id]["action"])

    def get_pending(self) -> list:
        """Get pending approvals."""
        return [a for a in self.pending if a["status"] == "pending"]

workflow = HumanInLoopWorkflow(llm)
workflow.execute_step("transfer_funds", "Move 1000 to account X")

queue = ApprovalQueue()
queue.submit_for_approval("Delete database", priority="high")
pending = queue.get_pending()
```

## Error Handling & Retries

```python
class RobustWorkflow:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.execution_log = []

    def execute_with_fallback(self, primary: Callable, fallback: Callable, input_data):
        """Execute primary, fallback on failure."""
        try:
            result = primary(input_data)
            self.log_execution("primary", True, input_data)
            return result
        except Exception as e:
            print(f"Primary failed: {e}")
            try:
                result = fallback(input_data)
                self.log_execution("fallback", True, input_data)
                return result
            except Exception as e2:
                self.log_execution("fallback", False, input_data)
                raise

    def execute_with_retry(self, func: Callable, input_data, backoff_factor: int = 2):
        """Retry with exponential backoff."""
        import time

        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = func(input_data)
                self.log_execution(f"attempt_{attempt}", True, input_data)
                return result
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    print(f"Retry in {wait_time}s")
                    time.sleep(wait_time)

        raise last_error

    def log_execution(self, phase: str, success: bool, input_data):
        """Log for auditing."""
        self.execution_log.append({
            "phase": phase,
            "success": success,
            "input": input_data
        })

workflow = RobustWorkflow()
result = workflow.execute_with_retry(process_data, input_data)
```

## Async Workflows

```python
import asyncio
from typing import Coroutine

class AsyncWorkflow:
    async def parallel_tasks(self, tasks: list[Coroutine]):
        """Execute tasks in parallel."""
        results = await asyncio.gather(*tasks)
        return results

    async def sequential_tasks(self, tasks: list[Coroutine]):
        """Execute sequentially."""
        results = []
        for task in tasks:
            result = await task
            results.append(result)
        return results

    async def with_timeout(self, coro: Coroutine, timeout_seconds: int):
        """Execute with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            return None

async def task1():
    await asyncio.sleep(1)
    return "Task 1 done"

async def task2():
    await asyncio.sleep(2)
    return "Task 2 done"

workflow = AsyncWorkflow()
results = asyncio.run(workflow.parallel_tasks([task1(), task2()]))
```

## Key Takeaways

- LangGraph provides state machines for workflows
- CrewAI enables agent collaboration
- AutoGen creates group conversations
- State machines formalize state transitions
- Human-in-loop adds approval gates
- Error handling ensures robustness
- Async execution improves efficiency
