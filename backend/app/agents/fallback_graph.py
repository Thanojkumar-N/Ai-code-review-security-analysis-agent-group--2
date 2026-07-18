from typing import Dict, Any, Callable, Optional, Union

# Define the constant END indicator matching LangGraph API
END = "END"

class StateGraph:
    """A drop-in high-fidelity fallback for LangGraph's StateGraph orchestration.
    
    Manages workflow nodes, static transitions (edges), and conditional routing.
    """
    def __init__(self, state_schema: Any):
        self.state_schema = state_schema
        self.nodes: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, tuple] = {}
        self.entry_point: Optional[str] = None

    def add_node(self, name: str, action: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """Register a node with an execution function."""
        if name in self.nodes:
            raise ValueError(f"Node '{name}' is already defined in this graph")
        self.nodes[name] = action

    def add_edge(self, start_key: str, end_key: str) -> None:
        """Register a static edge between two nodes."""
        self.edges[start_key] = end_key

    def add_conditional_edges(
        self, 
        source: str, 
        path: Callable[[Dict[str, Any]], str], 
        path_map: Optional[Dict[str, str]] = None
    ) -> None:
        """Register a conditional routing path map determined by a routing function."""
        self.conditional_edges[source] = (path, path_map)

    def set_entry_point(self, key: str) -> None:
        """Define the initial start node of the graph execution loop."""
        self.entry_point = key

    def compile(self):
        """Compile graph definitions into an executable CompiledGraph object."""
        if not self.entry_point:
            raise ValueError("Cannot compile graph: Entry point node is not set")
        return CompiledGraph(self)

class CompiledGraph:
    """An executable instance of the StateGraph, mimicking LangGraph's CompiledGraph."""
    def __init__(self, graph: StateGraph):
        self.graph = graph

    def invoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the state transitions loop sequentially, updating state and routing."""
        # Deep copy state dict
        state = dict(initial_state)
        current_node = self.graph.entry_point

        while current_node and current_node != END:
            # 1. Execute current node
            node_action = self.graph.nodes.get(current_node)
            if not node_action:
                raise KeyError(f"Graph execution failed: Node '{current_node}' is registered as a target but has no action function")

            # Execute action and update state with output updates
            node_output = node_action(state)
            if node_output:
                state.update(node_output)

            # 2. Determine next node target
            if current_node in self.graph.conditional_edges:
                routing_func, path_map = self.graph.conditional_edges[current_node]
                next_key = routing_func(state)
                if path_map:
                    current_node = path_map.get(next_key, next_key)
                else:
                    current_node = next_key
            else:
                current_node = self.graph.edges.get(current_node, END)

        return state
