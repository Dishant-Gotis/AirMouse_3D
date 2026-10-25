---
skill_name: ai-agent-architecture
description: Agent architecture: planning, memory, tools, reflection, multi-agent coordination
category: AI & LLM
version: 1.0.0
---

# Agent Architecture: Building Autonomous Systems

## Agent Loop

```python
class Agent:
    def __init__(self, llm, tools: dict, memory):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.step_count = 0

    def run(self, goal: str, max_steps: int = 10):
        """Execute agent loop toward goal."""
        self.memory.save_goal(goal)
        state = {"goal": goal, "observations": []}

        for step in range(max_steps):
            self.step_count += 1

            # Think: Plan next action
            plan = self._think(state)

            # Act: Execute action
            observation = self._act(plan)
            state["observations"].append(observation)

            # Observe: Process result
            is_done = self._is_done(state)
            if is_done:
                return state

        return state

    def _think(self, state: dict) -> str:
        """Generate plan based on goal and history."""
        prompt = f"""
Goal: {state['goal']}
History: {state['observations'][-3:]}  # Last 3 steps

Available tools: {list(self.tools.keys())}

What is your next action?
"""
        return self.llm.predict(prompt)

    def _act(self, plan: str) -> str:
        """Execute action from plan."""
        tool_name = self._extract_tool(plan)
        args = self._extract_args(plan)

        if tool_name in self.tools:
            return self.tools[tool_name](**args)
        return "Unknown tool"

    def _is_done(self, state: dict) -> bool:
        """Check if goal achieved."""
        return "DONE" in state["observations"][-1].upper()

    def _extract_tool(self, plan: str) -> str:
        return "search"  # Placeholder

    def _extract_args(self, plan: str) -> dict:
        return {}  # Placeholder
```

## Planning Agent

```python
class PlanningAgent:
    """Decompose goal into plan before execution."""

    def __init__(self, llm, tools: dict):
        self.llm = llm
        self.tools = tools

    def create_plan(self, goal: str) -> list[str]:
        """Decompose goal into steps."""
        prompt = f"""
Break down this goal into concrete steps:
{goal}

Steps:
1.
2.
3.
"""
        response = self.llm.predict(prompt)
        steps = [s.strip() for s in response.split('\n') if s.strip() and s[0].isdigit()]
        return steps

    def execute_plan(self, plan: list[str]):
        """Execute plan steps sequentially."""
        results = {}

        for i, step in enumerate(plan):
            tool = self._select_tool(step)
            result = self.tools[tool](step)
            results[f"step_{i}"] = result

        return results

    def _select_tool(self, step: str) -> str:
        """Select best tool for step."""
        keywords = {
            "search": ["search", "find", "lookup"],
            "analyze": ["analyze", "evaluate", "assess"],
            "summarize": ["summarize", "brief", "overview"]
        }

        for tool, keywords_list in keywords.items():
            if any(kw in step.lower() for kw in keywords_list):
                return tool

        return "search"

agent = PlanningAgent(llm, tools)
plan = agent.create_plan("Research AI trends and create summary")
results = agent.execute_plan(plan)
```

## Memory in Agents

```python
class AgentMemory:
    def __init__(self):
        self.working_memory = []  # Current task
        self.episodic_memory = []  # Past experiences
        self.semantic_memory = {}  # Facts

    def remember(self, observation: str, type: str = "episodic"):
        """Store memory."""
        if type == "working":
            self.working_memory.append(observation)
        elif type == "episodic":
            self.episodic_memory.append({
                "timestamp": time.time(),
                "observation": observation
            })
        else:
            self.semantic_memory[observation] = True

    def recall(self, query: str, num_results: int = 3) -> list:
        """Retrieve relevant memories."""
        # Semantic search
        relevant = []
        for mem in self.episodic_memory[-10:]:  # Recent only
            if query.lower() in mem["observation"].lower():
                relevant.append(mem["observation"])

        return relevant[:num_results]

    def get_context(self) -> str:
        """Get current context."""
        recent = [m["observation"] for m in self.episodic_memory[-5:]]
        return "\n".join(recent)

memory = AgentMemory()
memory.remember("Task: Find AI papers", type="working")
memory.remember("Found 3 papers on transformers", type="episodic")
context = memory.get_context()
```

## Reflection

```python
class ReflectionAgent:
    def __init__(self, llm, tools: dict):
        self.llm = llm
        self.tools = tools

    def execute_with_reflection(self, goal: str):
        """Execute, then reflect on success."""
        observations = []

        for attempt in range(3):
            action = self._plan_action(goal, observations)
            result = self.tools["execute"](action)
            observations.append(result)

            # Reflect: Did we make progress?
            reflection = self._reflect(goal, observations)

            if "GOAL_ACHIEVED" in reflection:
                return observations

            elif "STUCK" in reflection:
                # Adjust strategy
                goal = self._adjust_goal(goal, reflection)

        return observations

    def _plan_action(self, goal: str, history: list) -> str:
        """Plan action based on history."""
        return f"Action toward {goal}"

    def _reflect(self, goal: str, observations: list) -> str:
        """Reflect on progress."""
        prompt = f"""
Goal: {goal}
Actions taken: {observations}

Are we making progress? Should we adjust strategy?
"""
        return self.llm.predict(prompt)

    def _adjust_goal(self, goal: str, reflection: str) -> str:
        """Adjust goal based on reflection."""
        return goal  # Placeholder
```

## Tool Selection

```python
class ToolSelector:
    def __init__(self, tools: dict):
        self.tools = tools
        self.tool_descriptions = {
            "search": "Find information online",
            "analyze": "Analyze data",
            "calculate": "Perform calculations",
            "visualize": "Create visualizations"
        }

    def select_best_tool(self, task: str) -> str:
        """Select best tool for task using LLM."""
        from langchain.output_parsers import PydanticOutputParser
        from pydantic import BaseModel

        class ToolSelection(BaseModel):
            tool: str
            confidence: float

        prompt = f"""
Task: {task}

Available tools:
{json.dumps(self.tool_descriptions, indent=2)}

Select the best tool and confidence (0-1).
"""

        response = llm.predict(prompt)
        return response  # Parse tool name

    def execute_task(self, task: str):
        """Select tool and execute."""
        tool_name = self.select_best_tool(task)
        return self.tools[tool_name](task)
```

## Error Recovery

```python
class ResilientAgent:
    def execute_with_recovery(self, goal: str):
        """Execute with error recovery strategies."""
        recovery_strategies = [
            self._retry,
            self._simplify,
            self._delegate,
            self._fail_gracefully
        ]

        for strategy in recovery_strategies:
            try:
                return strategy(goal)
            except Exception as e:
                print(f"Strategy failed: {e}")
                continue

        return {"status": "failed", "goal": goal}

    def _retry(self, goal: str, max_attempts: int = 3):
        """Retry the same action."""
        for attempt in range(max_attempts):
            try:
                return self._execute(goal)
            except Exception:
                if attempt == max_attempts - 1:
                    raise

    def _simplify(self, goal: str):
        """Simplify the goal."""
        simpler_goal = f"Simpler version of: {goal}"
        return self._execute(simpler_goal)

    def _delegate(self, goal: str):
        """Delegate to another agent/tool."""
        return {"delegated": True, "goal": goal}

    def _fail_gracefully(self, goal: str):
        """Return best-effort result."""
        return {"status": "partial_completion", "goal": goal}

    def _execute(self, goal: str):
        """Execute goal."""
        return {"status": "success"}
```

## Coordination

```python
class MultiAgentCoordinator:
    def __init__(self, agents: dict):
        self.agents = agents

    def coordinate(self, goal: str):
        """Coordinate multiple agents."""
        # Assign subgoals
        subgoals = self._decompose(goal)

        results = {}
        for subgoal, agent_name in subgoals:
            agent = self.agents[agent_name]
            result = agent.run(subgoal)
            results[subgoal] = result

        # Synthesize results
        return self._synthesize(results)

    def _decompose(self, goal: str) -> list[tuple]:
        """Decompose into subgoals for different agents."""
        return [
            ("Find data", "research_agent"),
            ("Analyze data", "analysis_agent"),
            ("Create report", "writing_agent")
        ]

    def _synthesize(self, results: dict) -> str:
        """Combine agent outputs."""
        return json.dumps(results)

coordinator = MultiAgentCoordinator({
    "research": agent1,
    "analysis": agent2,
    "writing": agent3
})

result = coordinator.coordinate("Produce market analysis report")
```

## Key Takeaways

- Agent loop: think → act → observe
- Planning decomposes goals before execution
- Memory enables learning and context
- Reflection improves strategy over time
- Tool selection matches task to capability
- Error recovery prevents agent failure
- Coordination enables multi-agent systems
