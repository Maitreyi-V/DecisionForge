from collections import Counter

from core.simulation_models import SimulationLLMResponse


class InvalidSimulationGraphError(ValueError):
    pass


def validate_simulation_graph(simulation: SimulationLLMResponse) -> None:
    errors: list[str] = []

    node_keys = [node.node_key for node in simulation.nodes]
    node_key_counts = Counter(node_keys)
    node_key_set = set(node_keys)

    duplicate_keys = [
        key
        for key, count in node_key_counts.items()
        if count > 1
    ]

    if duplicate_keys:
        errors.append(
            f"Duplicate node keys: {duplicate_keys}"
        )

    root_nodes = [
        node for node in simulation.nodes
        if node.is_root
    ]

    if len(root_nodes) != 1:
        errors.append(
            f"Expected exactly one root node, found {len(root_nodes)}"
        )

    ending_nodes = [
        node for node in simulation.nodes
        if node.is_ending
    ]

    if not ending_nodes:
        errors.append("The simulation must contain at least one ending node")

    for node in simulation.nodes:
        if node.is_ending:
            if node.options:
                errors.append(
                    f"Ending node '{node.node_key}' cannot have options"
                )

            if not (
                node.outcome_summary
                and node.outcome_summary.strip()
            ):
                errors.append(
                    f"Ending node '{node.node_key}' requires an outcome summary"
                )

        elif len(node.options) < 2:
            errors.append(
                f"Non-ending node '{node.node_key}' must have at least two options"
            )

        for option in node.options:
            if option.target_node_key not in node_key_set:
                errors.append(
                    f"Option in '{node.node_key}' points to missing node "
                    f"'{option.target_node_key}'"
                )

    if len(root_nodes) == 1 and root_nodes[0].is_ending:
        errors.append("The root node cannot also be an ending node")

    if not duplicate_keys and len(root_nodes) == 1:
        node_by_key = {
            node.node_key: node
            for node in simulation.nodes
        }

        reachable: set[str] = set()
        active_path: set[str] = set()
        cycle_detected = False

        def dfs(node_key: str) -> None:
            nonlocal cycle_detected

            if node_key in active_path:
                cycle_detected = True
                return

            if node_key in reachable:
                return

            reachable.add(node_key)
            active_path.add(node_key)

            node = node_by_key[node_key]

            for option in node.options:
                if option.target_node_key in node_by_key:
                    dfs(option.target_node_key)

            active_path.remove(node_key)

        dfs(root_nodes[0].node_key)

        unreachable_nodes = node_key_set - reachable

        if unreachable_nodes:
            errors.append(
                f"Unreachable nodes: {sorted(unreachable_nodes)}"
            )

        if cycle_detected:
            errors.append("The simulation graph cannot contain cycles")

    if errors:
        raise InvalidSimulationGraphError("; ".join(errors))