"""Backend registry for optional real-model adapters."""

from __future__ import annotations

from .base import AdapterAvailability, BackendUnavailableError, RealModelAdapter

BACKEND_ALIASES = {
    "transformer-lens": "transformer_lens",
    "transformer_lens": "transformer_lens",
    "tl": "transformer_lens",
    "huggingface": "huggingface",
    "hugging-face": "huggingface",
    "hf": "huggingface",
}


def list_adapters() -> list[AdapterAvailability]:
    return [
        _transformer_lens_cls().availability(),
        _huggingface_cls().availability(),
    ]


def get_adapter(backend: str) -> RealModelAdapter:
    canonical = BACKEND_ALIASES.get(backend)
    if canonical == "transformer_lens":
        cls = _transformer_lens_cls()
    elif canonical == "huggingface":
        cls = _huggingface_cls()
    else:
        raise ValueError(f"unknown real-model backend: {backend}")
    availability = cls.availability()
    if not availability.available:
        raise BackendUnavailableError(f"{availability.name} backend unavailable: {availability.install_hint}")
    return cls()


def _transformer_lens_cls():
    from .transformer_lens_adapter import TransformerLensAdapter

    return TransformerLensAdapter


def _huggingface_cls():
    from .huggingface_adapter import HuggingFaceAdapter

    return HuggingFaceAdapter
