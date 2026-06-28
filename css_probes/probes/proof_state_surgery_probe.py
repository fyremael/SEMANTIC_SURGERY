from __future__ import annotations

from dataclasses import dataclass

from css_probes.core import ProbeResult, status_from_acceptance


@dataclass(frozen=True)
class ProofState:
    goal: str


class ToyProofChecker:
    transitions = {
        ("prove n + 0 = n", "rewrite add_zero"): "proved",
        ("prove 0 + n = n", "rewrite zero_add"): "proved",
    }

    def apply(self, state: ProofState, tactic: str) -> ProofState:
        key = (state.goal, tactic)
        if key not in self.transitions:
            raise ValueError("checker_rejected_transition")
        return ProofState(goal=self.transitions[key])


def run(seed: int = 0) -> ProbeResult:
    checker = ToyProofChecker()
    state = ProofState(goal="prove n + 0 = n")
    tactic = "rewrite add_zero"
    warnings: list[str] = []
    try:
        after = checker.apply(state, tactic)
        accepted = after.goal == "proved"
    except ValueError as exc:
        after = state
        accepted = False
        warnings.append(str(exc))
    metrics = {"checker_accepted": bool(accepted), "proof_closed": bool(after.goal == "proved"), "steps": 1}
    thresholds = {"checker_accepted_required": True, "proof_closed_required": True}
    if not accepted:
        warnings.append("proof_state_transition_rejected")
    return ProbeResult(name="proof_state_surgery_probe", status=status_from_acceptance(accepted, warnings), seed=seed, metrics=metrics, thresholds=thresholds, accepted=accepted, warnings=warnings, operator={"operator_type": "proof_state_transition", "persistence": "ephemeral", "tactic": tactic})
