"""Property cover for the CV-005 pull-request closure.

The named cases pin one chain and one fan-out. The closure's claim is wider:
over any graph of local calls, including branches, cycles and self-calls, it
returns exactly the workflows reachable from one a pull request starts. These
properties generate small call graphs, write each as real workflow YAML with a
randomly chosen call spelling, and compare the closure with an independent
reachability computed on the adjacency matrix.
"""

from __future__ import annotations

import dataclasses as dc

from codescene_contract import reader
from hypothesis import given, settings
from hypothesis import strategies as st

MAX_WORKFLOWS = 6
CALL_PREFIXES = ("./", "$/", "")


@dc.dataclass(frozen=True)
class CallGraph:
    """Which workflows a pull request starts, and which calls which, how."""

    starts: tuple[bool, ...]
    calls: tuple[tuple[bool, ...], ...]
    spellings: tuple[tuple[int, ...], ...]

    def workflow(self, i: int) -> str:
        """Render workflow ``i`` as YAML."""
        trigger = "pull_request" if self.starts[i] else "workflow_call"
        jobs = "".join(
            f"  call_{j}:\n    uses: "
            f"{CALL_PREFIXES[self.spellings[i][j]]}.github/workflows/w{j}.yml\n"
            for j, called in enumerate(self.calls[i])
            if called
        )
        return (
            f"on: {trigger}\njobs:\n{jobs}" if jobs else f"on: {trigger}\njobs: {{}}\n"
        )

    def expected_closure(self) -> set[str]:
        """Return the reachable set by transitive closure, not by search."""
        size = len(self.starts)
        reach = [[i == j or self.calls[i][j] for j in range(size)] for i in range(size)]
        for k in range(size):
            for i in range(size):
                if reach[i][k]:
                    reach[i] = [a or b for a, b in zip(reach[i], reach[k], strict=True)]
        return {
            f"w{j}.yml"
            for j in range(size)
            if any(self.starts[i] and reach[i][j] for i in range(size))
        }


@st.composite
def call_graphs(draw: st.DrawFn) -> CallGraph:
    """Generate a call graph of one to ``MAX_WORKFLOWS`` workflows."""
    size = draw(st.integers(min_value=1, max_value=MAX_WORKFLOWS))
    square = st.lists(st.booleans(), min_size=size, max_size=size)
    return CallGraph(
        starts=tuple(draw(square)),
        calls=tuple(tuple(draw(square)) for _ in range(size)),
        spellings=tuple(
            tuple(
                draw(
                    st.lists(
                        st.integers(0, len(CALL_PREFIXES) - 1),
                        min_size=size,
                        max_size=size,
                    )
                )
            )
            for _ in range(size)
        ),
    )


@settings(max_examples=256, deadline=None)
@given(graph=call_graphs())
def test_the_closure_is_exactly_what_a_pull_request_can_reach(graph: CallGraph) -> None:
    """Scenario: an arbitrary graph of local calls, in any spelling.

    Invariant: the closure is exactly the set reachable from a workflow a pull
    request starts, cycles and self-calls included.
    """
    all_workflows = {
        f"w{i}.yml": reader.parse(f"w{i}.yml", graph.workflow(i))
        for i in range(len(graph.starts))
    }
    assert reader.pull_request_closure(all_workflows) == graph.expected_closure()
