from __future__ import annotations

from dataclasses import dataclass
import hashlib

from css_probes.core import ProbeResult, status_from_acceptance


@dataclass(frozen=True)
class ProofState:
    goal: str
    context: tuple[str, ...] = ()


class ToyProofChecker:
    transitions = {
        ("prove A -> A", (), "intro"): ProofState(goal="prove A", context=("A",)),
        ("prove A", ("A",), "exact assumption"): ProofState(goal="proved", context=("A",)),
    }

    def apply(self, state: ProofState, tactic: str) -> ProofState:
        key = (state.goal, state.context, tactic)
        if key not in self.transitions:
            raise ValueError("checker_rejected_transition")
        return self.transitions[key]


def run(seed: int = 0) -> ProbeResult:
    checker = ToyProofChecker()
    state = ProofState(goal="prove A -> A")
    tactics = ["intro", "exact assumption"]
    warnings: list[str] = []
    after = state
    try:
        for tactic in tactics:
            after = checker.apply(after, tactic)
        accepted = after.goal == "proved"
    except ValueError as exc:
        accepted = False
        warnings.append(str(exc))
    metrics = {"checker_accepted": bool(accepted), "proof_closed": bool(after.goal == "proved"), "steps": len(tactics)}
    thresholds = {"checker_accepted_required": True, "proof_closed_required": True}
    if not accepted:
        warnings.append("proof_state_transition_rejected")
    tactic_text = "; ".join(tactics)
    tactic_hash = f"sha256:{hashlib.sha256(tactic_text.encode('utf-8')).hexdigest()}"
    return ProbeResult(
        name="proof_state_surgery_probe",
        status=status_from_acceptance(accepted, warnings),
        seed=seed,
        metrics=metrics,
        thresholds=thresholds,
        accepted=accepted,
        warnings=warnings,
        operator={
            "operator_type": "proof_state_transition",
            "persistence": "ephemeral",
            "form": "intro; exact assumption",
            "state_type": "proof_state",
            "stream": "proof_stack",
            "target_shape": [1],
            "parameters_ref": "inline",
            "parameter_hash": tactic_hash,
            "tactic": tactic_text,
        },
    )
