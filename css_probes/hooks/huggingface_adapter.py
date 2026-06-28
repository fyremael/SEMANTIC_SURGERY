"""Hugging Face local-only activation adapter."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np

from css_probes.metrics import cosine_similarity
from css_probes.operators import array_sha256

from .base import ActivationSurgeryConfig, AdapterAvailability, BackendUnavailableError, PromptCase, RealActivationResult


class HuggingFaceAdapter:
    name = "huggingface"

    @classmethod
    def availability(cls) -> AdapterAvailability:
        available = importlib.util.find_spec("torch") is not None and importlib.util.find_spec("transformers") is not None
        return AdapterAvailability(
            name=cls.name,
            available=available,
            install_hint="install with: python -m pip install -e .[real-hf]",
            detail="" if available else "requires torch and transformers",
        )

    def run_activation_surgery(self, config: ActivationSurgeryConfig) -> RealActivationResult:
        availability = self.availability()
        if not availability.available:
            raise BackendUnavailableError(availability.install_hint)
        if not config.model_name_or_path:
            raise ValueError("missing --model path or local model id")
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(config.model_name_or_path, local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(config.model_name_or_path, local_files_only=True)
        model.eval()
        module_name = _resolve_hf_module_name(model, config.layer, config.stream)
        module = model.get_submodule(module_name)
        vector_values = config.vector
        vector_missing = vector_values is None
        first_param = next(model.parameters())
        before_fingerprint = _model_fingerprint(model)

        target_before = [_case_logprob(model, tokenizer, case, None, None, None) for case in config.prompt_suite.target]
        off_before = [_case_logprob(model, tokenizer, case, None, None, None) for case in config.prompt_suite.off_target]

        captured_before: list[np.ndarray] = []
        captured_after: list[np.ndarray] = []
        cleanup_ok = False

        def patch_hook(_module: Any, _inputs: Any, output: Any) -> Any:
            tensor = output[0] if isinstance(output, tuple) else output
            nonlocal vector_values
            if vector_values is None:
                vector_values = [0.0] * int(tensor.shape[-1])
            if len(vector_values) != int(tensor.shape[-1]):
                raise ValueError(f"vector length {len(vector_values)} does not match activation width {int(tensor.shape[-1])}")
            vector = torch.tensor(vector_values, device=tensor.device, dtype=tensor.dtype)
            vector = vector.view(*([1] * (tensor.ndim - 1)), -1)
            patched = tensor + float(config.alpha) * vector
            captured_before.append(tensor.detach().float().cpu().reshape(-1, tensor.shape[-1]).numpy())
            captured_after.append(patched.detach().float().cpu().reshape(-1, tensor.shape[-1]).numpy())
            if isinstance(output, tuple):
                return (patched, *output[1:])
            return patched

        handle = module.register_forward_hook(patch_hook)
        try:
            target_after = [_case_logprob(model, tokenizer, case, None, None, None) for case in config.prompt_suite.target]
            off_after = [_case_logprob(model, tokenizer, case, None, None, None) for case in config.prompt_suite.off_target]
        finally:
            handle.remove()
            cleanup_ok = True

        post_first = _case_logprob(model, tokenizer, config.prompt_suite.target[0], None, None, None)
        rollback_residue = abs(post_first - target_before[0])
        after_fingerprint = _model_fingerprint(model)
        vector_array = np.asarray(vector_values or [], dtype=float)
        drift = _activation_drift(captured_before, captured_after)
        target_delta = float(np.mean(target_after) - np.mean(target_before))
        off_delta = float(np.mean(off_after) - np.mean(off_before))
        metrics = {
            "target_token_logprob_delta": target_delta,
            "target_success_delta": target_delta,
            "off_target_delta": off_delta,
            "off_target_degradation_max": float(max(0.0, -off_delta)),
            "rollback_residue": float(rollback_residue),
            "weight_fingerprint_changed": before_fingerprint != after_fingerprint,
            "hook_cleanup_ok": cleanup_ok,
            "local_files_only": config.local_files_only,
            **drift,
        }
        return RealActivationResult(
            backend=self.name,
            model_family=type(model).__name__,
            model_name_or_path=config.model_name_or_path,
            layer=config.layer,
            stream=module_name,
            shape=[int(vector_array.size or first_param.shape[-1])],
            metrics=metrics,
            operator={
                "form": "h_prime = h + alpha * v",
                "rank": 1,
                "parameters_ref": "inline",
                "parameter_hash": array_sha256(vector_array),
                "alpha": float(config.alpha),
            },
            warnings=["missing_vector_zero_patch"] if vector_missing else [],
            notes=["Hugging Face execution used local_files_only=True and forward hooks scoped to verifier calls."],
        )


def _case_logprob(model: Any, tokenizer: Any, case: PromptCase, *_unused: Any) -> float:
    import torch

    prompt_ids = tokenizer.encode(case.prompt, add_special_tokens=False)
    target_ids = tokenizer.encode(case.target_token, add_special_tokens=False)
    if not prompt_ids or not target_ids:
        raise ValueError("prompt and target_token must tokenize to at least one id")
    input_ids = torch.tensor([prompt_ids + target_ids], dtype=torch.long, device=next(model.parameters()).device)
    with torch.inference_mode():
        logits = model(input_ids).logits
        log_probs = torch.log_softmax(logits, dim=-1)
        total = 0.0
        start = len(prompt_ids) - 1
        for offset, token_id in enumerate(target_ids):
            total += float(log_probs[0, start + offset, token_id].detach().cpu())
    return total / len(target_ids)


def _resolve_hf_module_name(model: Any, layer: int, stream: str) -> str:
    candidates = []
    if "{layer}" in stream:
        candidates.append(stream.format(layer=layer))
    candidates.append(stream)
    if stream in {"residual", "hidden", "hidden_states", "block"}:
        candidates.extend(
            [
                f"transformer.h.{layer}",
                f"model.layers.{layer}",
                f"gpt_neox.layers.{layer}",
                f"decoder.layers.{layer}",
            ]
        )
    for candidate in candidates:
        try:
            model.get_submodule(candidate)
            return candidate
        except AttributeError:
            continue
    raise ValueError(f"could not resolve Hugging Face hook module for layer={layer} stream={stream}")


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
