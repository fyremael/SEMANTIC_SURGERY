"""TransformerLens local-only activation adapter."""

from __future__ import annotations

import importlib.util
from typing import Any

import numpy as np

from css_probes.metrics import cosine_similarity
from css_probes.operators import array_sha256

from .base import ActivationSurgeryConfig, AdapterAvailability, BackendUnavailableError, PromptCase, RealActivationResult


class TransformerLensAdapter:
    name = "transformer-lens"

    @classmethod
    def availability(cls) -> AdapterAvailability:
        available = importlib.util.find_spec("torch") is not None and importlib.util.find_spec("transformer_lens") is not None
        return AdapterAvailability(
            name=cls.name,
            available=available,
            install_hint="install with: python -m pip install -e .[real-tl]",
            detail="" if available else "requires torch and transformer-lens",
        )

    def run_activation_surgery(self, config: ActivationSurgeryConfig) -> RealActivationResult:
        availability = self.availability()
        if not availability.available:
            raise BackendUnavailableError(availability.install_hint)
        if not config.model_name_or_path:
            raise ValueError("missing --model path or local model id")
        import torch
        from transformer_lens import HookedTransformer

        try:
            model = HookedTransformer.from_pretrained(config.model_name_or_path, local_files_only=True)
        except TypeError as exc:
            raise ValueError("TransformerLens backend must support local_files_only=True for this phase") from exc
        model.eval()
        hook_name = _resolve_tl_hook_name(config.layer, config.stream)
        before_fingerprint = _model_fingerprint(model)
        target_before = [_case_logprob(model, case, None) for case in config.prompt_suite.target]
        off_before = [_case_logprob(model, case, None) for case in config.prompt_suite.off_target]
        vector_values = config.vector
        vector_missing = vector_values is None
        captured_before: list[np.ndarray] = []
        captured_after: list[np.ndarray] = []

        def patch_hook(activation: Any, _hook: Any) -> Any:
            nonlocal vector_values
            if vector_values is None:
                vector_values = [0.0] * int(activation.shape[-1])
            if len(vector_values) != int(activation.shape[-1]):
                raise ValueError(f"vector length {len(vector_values)} does not match activation width {int(activation.shape[-1])}")
            vector = torch.tensor(vector_values, device=activation.device, dtype=activation.dtype)
            vector = vector.view(*([1] * (activation.ndim - 1)), -1)
            patched = activation + float(config.alpha) * vector
            captured_before.append(activation.detach().float().cpu().reshape(-1, activation.shape[-1]).numpy())
            captured_after.append(patched.detach().float().cpu().reshape(-1, activation.shape[-1]).numpy())
            return patched

        target_after = [_case_logprob(model, case, (hook_name, patch_hook)) for case in config.prompt_suite.target]
        off_after = [_case_logprob(model, case, (hook_name, patch_hook)) for case in config.prompt_suite.off_target]
        post_first = _case_logprob(model, config.prompt_suite.target[0], None)
        rollback_residue = abs(post_first - target_before[0])
        after_fingerprint = _model_fingerprint(model)
        vector_array = np.asarray(vector_values or [], dtype=float)
        drift = _activation_drift(captured_before, captured_after)
        target_delta = float(np.mean(target_after) - np.mean(target_before))
        off_delta = float(np.mean(off_after) - np.mean(off_before))
        return RealActivationResult(
            backend=self.name,
            model_family=type(model).__name__,
            model_name_or_path=config.model_name_or_path,
            layer=config.layer,
            stream=hook_name,
            shape=[int(vector_array.size or model.cfg.d_model)],
            metrics={
                "target_token_logprob_delta": target_delta,
                "target_success_delta": target_delta,
                "off_target_delta": off_delta,
                "off_target_degradation_max": float(max(0.0, -off_delta)),
                "rollback_residue": float(rollback_residue),
                "weight_fingerprint_changed": before_fingerprint != after_fingerprint,
                "hook_cleanup_ok": True,
                "local_files_only": config.local_files_only,
                **drift,
            },
            operator={
                "form": "h_prime = h + alpha * v",
                "rank": 1,
                "parameters_ref": "inline",
                "parameter_hash": array_sha256(vector_array),
                "alpha": float(config.alpha),
            },
            warnings=["missing_vector_zero_patch"] if vector_missing else [],
            notes=["TransformerLens execution used run_with_hooks scoped to verifier calls."],
        )


def _case_logprob(model: Any, case: PromptCase, hook: tuple[str, Any] | None) -> float:
    import torch

    prompt_tokens = model.to_tokens(case.prompt, prepend_bos=False)
    target_tokens = model.to_tokens(case.target_token, prepend_bos=False)
    if prompt_tokens.numel() == 0 or target_tokens.numel() == 0:
        raise ValueError("prompt and target_token must tokenize to at least one id")
    tokens = torch.cat([prompt_tokens, target_tokens], dim=-1)
    with torch.inference_mode():
        if hook is None:
            logits = model(tokens)
        else:
            logits = model.run_with_hooks(tokens, fwd_hooks=[hook])
        log_probs = torch.log_softmax(logits, dim=-1)
        total = 0.0
        start = prompt_tokens.shape[-1] - 1
        for offset, token_id in enumerate(target_tokens[0].tolist()):
            total += float(log_probs[0, start + offset, token_id].detach().cpu())
    return total / target_tokens.shape[-1]


def _resolve_tl_hook_name(layer: int, stream: str) -> str:
    if "{layer}" in stream:
        return stream.format(layer=layer)
    if stream in {"residual", "resid_post", "hidden", "block"}:
        return f"blocks.{layer}.hook_resid_post"
    return stream


def _model_fingerprint(model: Any) -> str:
    for name, parameter in model.named_parameters():
        sample = parameter.detach().float().cpu().flatten()[:1024].numpy()
        return array_sha256(np.asarray([len(name), *sample], dtype=float))
    return array_sha256(np.asarray([], dtype=float))


def _activation_drift(before_chunks: list[np.ndarray], after_chunks: list[np.ndarray]) -> dict[str, float]:
    if not before_chunks or not after_chunks:
        return {"norm_delta_mean": 0.0, "norm_delta_max": 0.0, "cosine_drift_mean": 1.0, "cosine_drift_min": 1.0}
    before = np.concatenate(before_chunks, axis=0)
    after = np.concatenate(after_chunks, axis=0)
    delta_norm = np.linalg.norm(after - before, axis=-1)
    cosine = np.asarray(cosine_similarity(before, after, axis=-1))
    return {
        "norm_delta_mean": float(np.mean(delta_norm)),
        "norm_delta_max": float(np.max(delta_norm)),
        "cosine_drift_mean": float(np.mean(cosine)),
        "cosine_drift_min": float(np.min(cosine)),
    }
