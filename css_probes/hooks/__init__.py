"""Optional real-model adapter support.

Importing this package must not import optional ML backends.
"""

from .base import (
    ActivationSurgeryConfig,
    AdapterAvailability,
    BackendUnavailableError,
    PromptCase,
    PromptSuite,
    RealActivationResult,
    RealModelAdapter,
    load_prompt_suite,
)

__all__ = [
    "ActivationSurgeryConfig",
    "AdapterAvailability",
    "BackendUnavailableError",
    "PromptCase",
    "PromptSuite",
    "RealActivationResult",
    "RealModelAdapter",
    "load_prompt_suite",
]
