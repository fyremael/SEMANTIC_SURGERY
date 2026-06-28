"""Shared primitives for optional real-model adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Protocol


class BackendUnavailableError(RuntimeError):
    """Raised when an optional real-model backend is not installed."""


@dataclass(frozen=True)
class AdapterAvailability:
    name: str
    available: bool
    install_hint: str
    detail: str = ""


@dataclass(frozen=True)
class PromptCase:
    prompt: str
    target_token: str
    label: str = ""


@dataclass(frozen=True)
class PromptSuite:
    target: list[PromptCase]
    off_target: list[PromptCase]
    description: str = ""

    def validate(self) -> None:
        if not self.target:
            raise ValueError("prompt suite must include at least one target case")
        if not self.off_target:
            raise ValueError("prompt suite must include at least one off_target case")
        for group_name, cases in (("target", self.target), ("off_target", self.off_target)):
            for idx, case in enumerate(cases):
                if not case.prompt:
                    raise ValueError(f"{group_name}[{idx}] missing prompt")
                if not case.target_token:
                    raise ValueError(f"{group_name}[{idx}] missing target_token")


@dataclass(frozen=True)
class ActivationSurgeryConfig:
    backend: str
    model_name_or_path: str
    prompt_suite: PromptSuite
    layer: int
    stream: str
    alpha: float = 0.0
    vector: list[float] | None = None
    seed: int = 0
    local_files_only: bool = True


@dataclass(frozen=True)
class RealActivationResult:
    backend: str
    model_family: str
    model_name_or_path: str
    layer: int
    stream: str
    shape: list[int]
    metrics: dict[str, float | int | bool | str]
    operator: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class RealModelAdapter(Protocol):
    name: str

    @classmethod
    def availability(cls) -> AdapterAvailability:
        ...

    def run_activation_surgery(self, config: ActivationSurgeryConfig) -> RealActivationResult:
        ...


def load_prompt_suite(path: str | Path) -> PromptSuite:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    suite = PromptSuite(
        description=str(payload.get("description", "")),
        target=[_case_from_payload(item) for item in payload.get("target", [])],
        off_target=[_case_from_payload(item) for item in payload.get("off_target", [])],
    )
    suite.validate()
    return suite


def _case_from_payload(payload: dict[str, Any]) -> PromptCase:
    return PromptCase(
        prompt=str(payload.get("prompt", "")),
        target_token=str(payload.get("target_token", "")),
        label=str(payload.get("label", "")),
    )
