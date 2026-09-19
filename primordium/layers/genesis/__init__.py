"""GENESIS: Self-replication layer.

This module tracks ancestry and phylogeny of scrolls.
"""

from typing import Any, Dict, List
import networkx as nx


class PhylogenyTracker:
    """Track the ancestry graph of scrolls."""

    def __init__(self, max_depth: int = 50):
        self.max_depth = max_depth
        self.graph = nx.DiGraph()
        self.node_counter = 0

    def add_replication(
        self,
        parent_id: str,
        child_id: str,
        parent_tape: bytes,
        child_tape: bytes,
    ) -> None:
        """Record a replication event.

        Args:
            parent_id: ID of parent scroll
            child_id: ID of child scroll
            parent_tape: Tape bytes of parent
            child_tape: Tape bytes of child
        """
        # Add nodes if they don't exist
        if parent_id not in self.graph:
            self.graph.add_node(parent_id, tape=parent_tape, generation=0)
        if child_id not in self.graph:
            self.graph.add_node(child_id, tape=child_tape, generation=0)

        # Add edge
        self.graph.add_edge(parent_id, child_id)

        parent_gen = self.graph.nodes[parent_id].get('generation', 0)
        child_gen = self.graph.nodes[child_id].get('generation', 0)
        self.graph.nodes[child_id]['generation'] = max(child_gen, parent_gen + 1)

    def get_ancestors(self, scroll_id: str, depth: int = None) -> List[str]:
        """Get ancestors of a scroll.

        Args:
            scroll_id: ID of scroll
            depth: Maximum depth to traverse

        Returns:
            List of ancestor IDs
        """
        if depth is None:
            depth = self.max_depth

        try:
            reverse_graph = self.graph.reverse(copy=False)
            reachable = nx.single_source_shortest_path_length(
                reverse_graph, scroll_id, cutoff=depth
            )
            return [n for n in reachable if n != scroll_id]
        except nx.NetworkXError:
            return []

    def get_lineage_depth(self, scroll_id: str) -> int:
        """Get the depth of a scroll's lineage.

        Args:
            scroll_id: ID of scroll

        Returns:
            Number of ancestors
        """
        return len(self.get_ancestors(scroll_id))

    def detect_symbiogenesis(self) -> List[Dict[str, Any]]:
        """Detect symbiogenesis events.

        A symbiogenesis event occurs when a scroll has ancestors from
        previously separate lineages.

        Returns:
            List of symbiogenesis events
        """
        events = []
        for node in self.graph.nodes():
            ancestors = self.get_ancestors(node)
            # Check for multiple distinct lineages
            # This is simplified - in reality would track lineages more carefully
            if len(ancestors) > 1:
                events.append({
                    'scroll_id': node,
                    'ancestor_count': len(ancestors),
                })
        return events

    def to_dict(self) -> Dict[str, Any]:
        """Export phylogeny as dictionary.

        Returns:
            Dictionary representation
        """
        return nx.node_link_data(self.graph)


class GenesisLayer:
    """GENESIS layer for self-replication and phylogeny tracking."""

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', True)
        self.track_phylogeny = config.get('track_phylogeny', True)
        self.phylogeny_depth = config.get('phylogeny_depth', 50)

        if self.track_phylogeny:
            self.tracker = PhylogenyTracker(max_depth=self.phylogeny_depth)
        else:
            self.tracker = None

        self._last_copy_counts: Dict[str, int] = {}

    def after_interaction(self, soup, i: int, j: int, steps: int) -> None:
        """After interaction, record replication lineage.

        In the APEIRON model, replication happens implicitly when bytes
        are copied from one scroll to another during interaction. A
        copy_count increase on scroll i means i's content was copied
        into j's tape, so j descends from i for this interaction.
        """
        if not self.enabled or not self.track_phylogeny:
            return

        scroll_i = soup.scrolls[i]
        scroll_j = soup.scrolls[j]

        last_i = self._last_copy_counts.get(scroll_i.id, scroll_i.copy_count)
        last_j = self._last_copy_counts.get(scroll_j.id, scroll_j.copy_count)

        if scroll_i.copy_count > last_i:
            self.tracker.add_replication(
                parent_id=scroll_i.id,
                child_id=scroll_j.id,
                parent_tape=scroll_i.tape.tobytes(),
                child_tape=scroll_j.tape.tobytes(),
            )
        if scroll_j.copy_count > last_j:
            self.tracker.add_replication(
                parent_id=scroll_j.id,
                child_id=scroll_i.id,
                parent_tape=scroll_j.tape.tobytes(),
                child_tape=scroll_i.tape.tobytes(),
            )

        self._last_copy_counts[scroll_i.id] = scroll_i.copy_count
        self._last_copy_counts[scroll_j.id] = scroll_j.copy_count

    def after_epoch(self, soup, epoch: int) -> Dict[str, Any]:
        """After epoch, return phylogeny statistics."""
        if not self.enabled or not self.track_phylogeny:
            return {}

        stats = {
            'total_nodes': self.tracker.graph.number_of_nodes(),
            'total_edges': self.tracker.graph.number_of_edges(),
            'max_lineage_depth': max(
                self.tracker.get_lineage_depth(n)
                for n in self.tracker.graph.nodes()
            ) if self.tracker.graph.nodes() else 0,
            'symbiogenesis_events': len(self.tracker.detect_symbiogenesis()),
        }

        return stats

    def get_phylogeny(self) -> Dict[str, Any]:
        """Get full phylogeny data."""
        if self.tracker:
            return self.tracker.to_dict()
        return {}
