"""Graph Pathfinding & Ambiguity Resolution for Federated Datasets."""

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from app.database.models.federation import DatasetRelationship, RelationshipStatus


class JoinHop:
    """Represents a single directed join hop between two datasets."""

    def __init__(
        self,
        from_dataset_id: str,
        to_dataset_id: str,
        from_field: str,
        to_field: str,
        relationship: DatasetRelationship,
        is_reverse: bool = False,
    ):
        self.from_dataset_id = from_dataset_id
        self.to_dataset_id = to_dataset_id
        self.from_field = from_field
        self.to_field = to_field
        self.relationship = relationship
        self.is_reverse = is_reverse

    def __repr__(self) -> str:
        return f"{self.from_dataset_id}.{self.from_field} -> {self.to_dataset_id}.{self.to_field}"


class FederationGraph:
    """Directed graph representing validated relationships between datasets."""

    MAX_JOIN_DEPTH = 3

    def __init__(self, relationships: List[DatasetRelationship]):
        self.relationships = [r for r in relationships if r.status == RelationshipStatus.VALIDATED]
        self.adj: Dict[str, List[JoinHop]] = {}
        self._build_graph()

    def _build_graph(self) -> None:
        for r in self.relationships:
            # Forward edge
            fwd_hop = JoinHop(
                from_dataset_id=r.source_dataset_id,
                to_dataset_id=r.target_dataset_id,
                from_field=r.source_field,
                to_field=r.target_field,
                relationship=r,
                is_reverse=False,
            )
            self.adj.setdefault(r.source_dataset_id, []).append(fwd_hop)

            # Reverse edge (symmetric join capability)
            rev_hop = JoinHop(
                from_dataset_id=r.target_dataset_id,
                to_dataset_id=r.source_dataset_id,
                from_field=r.target_field,
                to_field=r.source_field,
                relationship=r,
                is_reverse=True,
            )
            self.adj.setdefault(r.target_dataset_id, []).append(rev_hop)

    def find_path(self, start_id: str, end_id: str) -> Optional[List[JoinHop]]:
        """Find the shortest join path between two datasets using BFS."""
        if start_id == end_id:
            return []

        queue: deque[Tuple[str, List[JoinHop]]] = deque([(start_id, [])])
        visited: Set[str] = {start_id}

        while queue:
            curr_id, path = queue.popleft()

            if len(path) >= self.MAX_JOIN_DEPTH:
                continue

            for hop in self.adj.get(curr_id, []):
                next_id = hop.to_dataset_id
                if next_id == end_id:
                    return path + [hop]

                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [hop]))

        return None

    def find_all_paths(self, start_id: str, end_id: str) -> List[List[JoinHop]]:
        """Find all distinct join paths between two datasets within MAX_JOIN_DEPTH."""
        if start_id == end_id:
            return [[]]

        results: List[List[JoinHop]] = []
        queue: deque[Tuple[str, List[JoinHop], Set[str]]] = deque([(start_id, [], {start_id})])

        while queue:
            curr_id, path, visited = queue.popleft()

            if len(path) >= self.MAX_JOIN_DEPTH:
                continue

            for hop in self.adj.get(curr_id, []):
                next_id = hop.to_dataset_id
                if next_id == end_id:
                    results.append(path + [hop])
                elif next_id not in visited:
                    queue.append((next_id, path + [hop], visited | {next_id}))

        return results

    def resolve_join_tree(self, required_dataset_ids: List[str]) -> Tuple[str, List[JoinHop], List[str]]:
        """Resolve an optimal join tree covering all required datasets."""
        if not required_dataset_ids:
            raise ValueError("At least one dataset is required for federated analysis.")

        if len(required_dataset_ids) == 1:
            return required_dataset_ids[0], [], []

        # Find best root (the dataset with highest connectivity to other required datasets)
        best_root = required_dataset_ids[0]
        best_paths: Dict[str, List[JoinHop]] = {}
        min_total_hops = float("inf")

        for candidate_root in required_dataset_ids:
            paths_from_root: Dict[str, List[JoinHop]] = {}
            possible = True
            total_hops = 0

            for other_id in required_dataset_ids:
                if other_id == candidate_root:
                    continue
                path = self.find_path(candidate_root, other_id)
                if path is None:
                    possible = False
                    break
                paths_from_root[other_id] = path
                total_hops += len(path)

            if possible and total_hops < min_total_hops:
                min_total_hops = total_hops
                best_root = candidate_root
                best_paths = paths_from_root

        if not best_paths and len(required_dataset_ids) > 1:
            raise ValueError(
                f"No validated join path connects all required datasets: {', '.join(required_dataset_ids)}"
            )

        # Collect unique ordered hops
        ordered_hops: List[JoinHop] = []
        joined_datasets: Set[str] = {best_root}
        warnings: List[str] = []

        # Check for ambiguous paths
        for target_id in required_dataset_ids:
            if target_id == best_root:
                continue
            all_p = self.find_all_paths(best_root, target_id)
            if len(all_p) > 1 and len(all_p[0]) == len(all_p[1]):
                warnings.append(
                    f"Multiple join paths exist between {best_root} and {target_id}. Selected shortest deterministic path."
                )

        for target_id, path in best_paths.items():
            for hop in path:
                if hop.to_dataset_id not in joined_datasets:
                    ordered_hops.append(hop)
                    joined_datasets.add(hop.to_dataset_id)

        return best_root, ordered_hops, warnings
