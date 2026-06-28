"""Run a stronger local-only real-model envelope audit.

This script is intentionally outside default CI. It requires optional Hugging
Face dependencies and a local model path or an already cached Pythia-70M model.
It does not download, save, train, or mutate model weights.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from css_probes.hooks.base import ActivationSurgeryConfig, PromptCase, PromptSuite
from css_probes.probes.real_activation_surgery import run_real_activation_surgery
from css_probes.report import default_operator_cards_path, write_json_report, write_operator_cards


TARGET_CASES = [
    {"label": "france_basic", "prompt": "The capital of France is", "target_token": " Paris"},
    {"label": "france_possessive", "prompt": "France's capital city is", "target_token": " Paris"},
    {"label": "france_location", "prompt": "In France, the capital is", "target_token": " Paris"},
    {"label": "france_question", "prompt": "Q: What is the capital of France? A:", "target_token": " Paris"},
]

OFF_TARGET_CASES = [
    {"label": "arithmetic", "prompt": "2 + 2 =", "target_token": " 4"},
    {"label": "germany", "prompt": "The capital of Germany is", "target_token": " Berlin"},
    {"label": "spain", "prompt": "The capital of Spain is", "target_token": " Madrid"},
    {"label": "italy", "prompt": "The capital of Italy is", "target_token": " Rome"},
    {"label": "japan", "prompt": "The capital of Japan is", "target_token": " Tokyo"},
    {"label": "opposite_hot", "prompt": "The opposite of hot is", "target_token": " cold"},
]

FORBIDDEN_PARIS_CASES = [
    {"label": "germany_paris_leak", "prompt": "The capital of Germany is", "target_token": " Paris"},
    {"label": "spain_paris_leak", "prompt": "The capital of Spain is", "target_token": " Paris"},
    {"label": "italy_paris_leak", "prompt": "The capital of Italy is", "target_token": " Paris"},
    {"label": "japan_paris_leak", "prompt": "The capital of Japan is", "target_token": " Paris"},
]

ALPHAS = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.96, 0.99]
STREAM = "gpt_neox.final_layer_norm"
LEAKAGE_MAX = 0.02


@dataclass(frozen=True)
class Runtime:
    torch: Any
    tokenizer: Any
    model: Any
    module: Any
    output_embeddings: Any


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.environ.get("CSS_HF_MODEL_PATH", ""))
    parser.add_argument("--out-dir", default="reports")
    parser.add_argument("--prefix", default="real_envelope")
    args = parser.parse_args()

    model_path = Path(args.model) if args.model else prepare_local_pythia_from_cache()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt_suite_path = out_dir / f"{args.prefix}_prompt_suite.json"
    forbidden_suite_path = out_dir / f"{args.prefix}_forbidden_paris_suite.json"
    vector_path = out_dir / f"{args.prefix}_vector_constrained.json"
    sweep_path = out_dir / f"{args.prefix}_sweep.json"
    certified_report_path = out_dir / f"{args.prefix}_certified_report.json"
    visual_path = out_dir / f"{args.prefix}_summary.svg"
    assessment_path = out_dir / "REAL_MODEL_ENVELOPE_ASSESSMENT.md"

    prompt_suite_payload = {
        "description": "Envelope suite: France/Paris target prompts plus non-France and non-geography guards.",
        "target": TARGET_CASES,
        "off_target": OFF_TARGET_CASES,
        "forbidden": FORBIDDEN_PARIS_CASES,
    }
    forbidden_suite_payload = {
        "description": "Forbidden leakage checks: Paris should not rise on non-France capital prompts.",
        "forbidden": FORBIDDEN_PARIS_CASES,
    }
    prompt_suite_path.write_text(json.dumps(prompt_suite_payload, indent=2, sort_keys=True), encoding="utf-8")
    forbidden_suite_path.write_text(json.dumps(forbidden_suite_payload, indent=2, sort_keys=True), encoding="utf-8")

    runtime = load_runtime(model_path)
    vector, vector_meta = build_constrained_vector(runtime, TARGET_CASES, OFF_TARGET_CASES, FORBIDDEN_PARIS_CASES)
    before = baseline_logprobs(runtime, TARGET_CASES, OFF_TARGET_CASES, FORBIDDEN_PARIS_CASES)
    rows = [evaluate_alpha(runtime, vector, before, alpha) for alpha in ALPHAS]
    chosen = choose_row(rows)

    vector_payload = {
        "description": "Constrained no-grad final-stream vector: improve France/Paris, preserve guard answers, suppress Paris leakage on non-France prompts.",
        "backend": "huggingface",
        "model_name_or_path": str(model_path),
        "stream": STREAM,
        "prompt_suite": str(prompt_suite_path),
        "forbidden_suite": str(forbidden_suite_path),
        "recommended_alpha": chosen["alpha"],
        **vector_meta,
        "vector": [float(value) for value in vector.tolist()],
    }
    vector_path.write_text(json.dumps(vector_payload, indent=2, sort_keys=True), encoding="utf-8")

    suite = PromptSuite(
        description=prompt_suite_payload["description"],
        target=[PromptCase(**case) for case in TARGET_CASES],
        off_target=[PromptCase(**case) for case in OFF_TARGET_CASES],
        forbidden=[PromptCase(**case) for case in FORBIDDEN_PARIS_CASES],
    )
    certified = run_real_activation_surgery(
        ActivationSurgeryConfig(
            backend="huggingface",
            model_name_or_path=str(model_path),
            prompt_suite=suite,
            layer=0,
            stream=STREAM,
            alpha=float(chosen["alpha"]),
            vector=[float(value) for value in vector.tolist()],
            local_files_only=True,
        )
    )
    write_json_report(certified, certified_report_path)
    write_operator_cards(certified, default_operator_cards_path(certified_report_path))

    audit_payload = {
        "model_path": str(model_path),
        "stream": STREAM,
        "thresholds": {
            "target_token_logprob_delta_min": 1e-9,
            "off_target_degradation_max": 0.02,
            "forbidden_paris_leakage_max": LEAKAGE_MAX,
            "norm_delta_max": 1.0,
            "cosine_drift_min": 0.98,
            "rollback_residue_max": 1e-9,
        },
        "chosen": chosen,
        "official_certificate": {
            "accepted": certified.accepted,
            "status": certified.status,
            "warnings": certified.warnings,
            "metrics": certified.to_dict()["metrics"],
        },
        "rows": rows,
    }
    sweep_path.write_text(json.dumps(audit_payload, indent=2, sort_keys=True), encoding="utf-8")
    write_visual(visual_path, audit_payload)
    write_assessment(assessment_path, audit_payload, prompt_suite_path, forbidden_suite_path, vector_path, sweep_path, certified_report_path, visual_path)

    print(f"model_path={model_path}")
    print(f"chosen_alpha={chosen['alpha']}")
    print(f"certified_accepted={certified.accepted}")
    print(f"target_delta={certified.metrics['target_token_logprob_delta']}")
    print(f"off_target_degradation={certified.metrics['off_target_degradation_max']}")
    print(f"forbidden_paris_leakage_max={chosen['forbidden_paris_leakage_max']}")
    print(f"strict_envelope_accepted={chosen['strict_envelope_accepted']}")
    print(f"wrote={certified_report_path}")
    print(f"wrote={visual_path}")
    print(f"wrote={assessment_path}")
    return 0 if certified.accepted and chosen["strict_envelope_accepted"] else 1


def prepare_local_pythia_from_cache() -> Path:
    target = Path(tempfile.gettempdir()) / "css_hf_pythia70m_local"
    if all((target / name).exists() for name in ["config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json"]):
        return target

    snapshots = Path.home() / ".cache" / "huggingface" / "hub" / "models--EleutherAI--pythia-70m-deduped" / "snapshots"
    if not snapshots.exists():
        raise SystemExit("CSS_HF_MODEL_PATH is unset and cached EleutherAI/pythia-70m-deduped snapshots were not found")

    weight_snapshot = None
    tokenizer_snapshot = None
    for snapshot in sorted(snapshots.iterdir()):
        if (snapshot / "model.safetensors").exists() and (snapshot / "config.json").exists():
            weight_snapshot = weight_snapshot or snapshot
        if (snapshot / "tokenizer.json").exists() and (snapshot / "tokenizer_config.json").exists():
            tokenizer_snapshot = tokenizer_snapshot or snapshot
    if weight_snapshot is None or tokenizer_snapshot is None:
        raise SystemExit("cached Pythia snapshots are incomplete; set CSS_HF_MODEL_PATH to a complete local model")

    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(weight_snapshot / "config.json", target / "config.json")
    for name in ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]:
        src = tokenizer_snapshot / name
        if src.exists():
            shutil.copy2(src, target / name)
    dst = target / "model.safetensors"
    if dst.exists():
        dst.unlink()
    os.link(weight_snapshot / "model.safetensors", dst)
    return target


def load_runtime(model_path: Path) -> Runtime:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(str(model_path), local_files_only=True)
    model.eval()
    module = model.get_submodule(STREAM)
    embeddings = model.get_output_embeddings().weight.detach().float().cpu()
    return Runtime(torch=torch, tokenizer=tokenizer, model=model, module=module, output_embeddings=embeddings)


def token_ids(runtime: Runtime, text: str) -> list[int]:
    ids = runtime.tokenizer.encode(text, add_special_tokens=False)
    if not ids:
        raise ValueError(f"{text!r} tokenized to no ids")
    return ids


def logprob_gradient(runtime: Runtime, case: dict[str, str]):
    torch = runtime.torch
    prompt_ids = token_ids(runtime, case["prompt"])
    target_ids = token_ids(runtime, case["target_token"])
    input_ids = torch.tensor([prompt_ids + target_ids], dtype=torch.long)
    with torch.inference_mode():
        logits = runtime.model(input_ids).logits.detach().float().cpu()
    grads = []
    start = len(prompt_ids) - 1
    for offset, token_id in enumerate(target_ids):
        probs = torch.softmax(logits[0, start + offset], dim=-1)
        expected_embedding = probs @ runtime.output_embeddings
        grads.append(runtime.output_embeddings[token_id] - expected_embedding)
    return torch.stack(grads).mean(dim=0)


def build_constrained_vector(runtime: Runtime, target_cases: list[dict[str, str]], off_cases: list[dict[str, str]], forbidden_cases: list[dict[str, str]]):
    torch = runtime.torch
    target_grads = [logprob_gradient(runtime, case) for case in target_cases]
    off_grads = [logprob_gradient(runtime, case) for case in off_cases]
    forbidden_grads = [logprob_gradient(runtime, case) for case in forbidden_cases]
    vector = torch.stack(target_grads).mean(dim=0) + 0.20 * torch.stack(off_grads).mean(dim=0) - 0.25 * torch.stack(forbidden_grads).mean(dim=0)
    vector = normalize_torch(torch, vector)

    target_margin = 0.025
    forbidden_max = 0.005
    for _ in range(220):
        for grad in target_grads:
            dot = torch.dot(vector, grad)
            if float(dot) <= target_margin:
                vector = vector + (target_margin - dot) * grad / (torch.dot(grad, grad) + 1e-12)
        for grad in off_grads:
            dot = torch.dot(vector, grad)
            if float(dot) < 0:
                vector = vector - dot * grad / (torch.dot(grad, grad) + 1e-12)
        for grad in forbidden_grads:
            dot = torch.dot(vector, grad)
            if float(dot) > forbidden_max:
                vector = vector - (dot - forbidden_max) * grad / (torch.dot(grad, grad) + 1e-12)
        vector = normalize_torch(torch, vector)

    meta = {
        "first_order_target_dots": [float(torch.dot(vector, grad)) for grad in target_grads],
        "first_order_off_target_dots": [float(torch.dot(vector, grad)) for grad in off_grads],
        "first_order_forbidden_paris_dots": [float(torch.dot(vector, grad)) for grad in forbidden_grads],
    }
    return vector.detach().cpu().numpy().astype(float), meta


def normalize_torch(torch: Any, vector: Any) -> Any:
    return vector / (torch.linalg.vector_norm(vector) + 1e-12)


def baseline_logprobs(runtime: Runtime, target_cases: list[dict[str, str]], off_cases: list[dict[str, str]], forbidden_cases: list[dict[str, str]]) -> dict[str, list[float]]:
    return {
        "target": [case_logprob(runtime, case, None, False)[0] for case in target_cases],
        "off_target": [case_logprob(runtime, case, None, False)[0] for case in off_cases],
        "forbidden": [case_logprob(runtime, case, None, False)[0] for case in forbidden_cases],
    }


def case_logprob(runtime: Runtime, case: dict[str, str], vector: np.ndarray | None, capture: bool, alpha: float = 0.0) -> tuple[float, list[tuple[np.ndarray, np.ndarray]]]:
    torch = runtime.torch
    prompt_ids = token_ids(runtime, case["prompt"])
    target_ids = token_ids(runtime, case["target_token"])
    input_ids = torch.tensor([prompt_ids + target_ids], dtype=torch.long)
    captured: list[tuple[np.ndarray, np.ndarray]] = []
    handle = None
    if vector is not None:
        vector_tensor = torch.tensor(vector, dtype=next(runtime.model.parameters()).dtype)

        def hook(_module: Any, _inputs: Any, output: Any) -> Any:
            tensor = output[0] if isinstance(output, tuple) else output
            patch = vector_tensor.to(device=tensor.device, dtype=tensor.dtype).view(*([1] * (tensor.ndim - 1)), -1)
            patched = tensor + float(alpha) * patch
            if capture:
                captured.append(
                    (
                        tensor.detach().float().cpu().reshape(-1, tensor.shape[-1]).numpy(),
                        patched.detach().float().cpu().reshape(-1, tensor.shape[-1]).numpy(),
                    )
                )
            if isinstance(output, tuple):
                return (patched, *output[1:])
            return patched

        handle = runtime.module.register_forward_hook(hook)
    try:
        with torch.inference_mode():
            logits = runtime.model(input_ids).logits
            log_probs = torch.log_softmax(logits, dim=-1)
            start = len(prompt_ids) - 1
            total = 0.0
            for offset, token_id in enumerate(target_ids):
                total += float(log_probs[0, start + offset, token_id].detach().cpu())
    finally:
        if handle is not None:
            handle.remove()
    return total / len(target_ids), captured


def evaluate_alpha(runtime: Runtime, vector: np.ndarray, before: dict[str, list[float]], alpha: float) -> dict[str, Any]:
    target_after, off_after, forbidden_after = [], [], []
    before_chunks: list[np.ndarray] = []
    after_chunks: list[np.ndarray] = []
    for case in TARGET_CASES:
        value, captured = case_logprob(runtime, case, vector, True, alpha)
        target_after.append(value)
        collect_chunks(captured, before_chunks, after_chunks)
    for case in OFF_TARGET_CASES:
        value, captured = case_logprob(runtime, case, vector, True, alpha)
        off_after.append(value)
        collect_chunks(captured, before_chunks, after_chunks)
    for case in FORBIDDEN_PARIS_CASES:
        value, _captured = case_logprob(runtime, case, vector, False, alpha)
        forbidden_after.append(value)

    target_deltas = [float(after - base) for after, base in zip(target_after, before["target"])]
    off_deltas = [float(after - base) for after, base in zip(off_after, before["off_target"])]
    forbidden_deltas = [float(after - base) for after, base in zip(forbidden_after, before["forbidden"])]
    before_array = np.concatenate(before_chunks, axis=0)
    after_array = np.concatenate(after_chunks, axis=0)
    delta_norm = np.linalg.norm(after_array - before_array, axis=-1)
    cosine = cosine_similarity(before_array, after_array, axis=-1)
    rollback_value = case_logprob(runtime, TARGET_CASES[0], None, False)[0]
    rollback_residue = abs(rollback_value - before["target"][0])

    row = {
        "alpha": alpha,
        "target_token_logprob_delta": float(np.mean(target_deltas)),
        "target_case_deltas": labeled(TARGET_CASES, target_deltas),
        "target_case_delta_min": float(min(target_deltas)),
        "off_target_delta": float(np.mean(off_deltas)),
        "off_target_case_deltas": labeled(OFF_TARGET_CASES, off_deltas),
        "off_target_degradation_max": float(max(0.0, -np.mean(off_deltas))),
        "off_target_case_degradation_max": float(max([0.0] + [-delta for delta in off_deltas])),
        "forbidden_paris_case_deltas": labeled(FORBIDDEN_PARIS_CASES, forbidden_deltas),
        "forbidden_paris_leakage_max": float(max([0.0] + forbidden_deltas)),
        "norm_delta_max": float(np.max(delta_norm)),
        "cosine_drift_min": float(np.min(cosine)),
        "rollback_residue": float(rollback_residue),
    }
    row["gate_preview_accepted"] = (
        row["target_token_logprob_delta"] > 1e-9
        and row["off_target_degradation_max"] <= 0.02
        and row["norm_delta_max"] <= 1.0
        and row["cosine_drift_min"] >= 0.98
        and row["rollback_residue"] <= 1e-9
    )
    row["strict_envelope_accepted"] = (
        row["gate_preview_accepted"]
        and row["target_case_delta_min"] > 1e-9
        and row["off_target_case_degradation_max"] <= 0.02
        and row["forbidden_paris_leakage_max"] <= LEAKAGE_MAX
    )
    return row


def collect_chunks(captured: list[tuple[np.ndarray, np.ndarray]], before_chunks: list[np.ndarray], after_chunks: list[np.ndarray]) -> None:
    for before, after in captured:
        before_chunks.append(before)
        after_chunks.append(after)


def labeled(cases: list[dict[str, str]], deltas: list[float]) -> dict[str, float]:
    return {case["label"]: float(delta) for case, delta in zip(cases, deltas)}


def cosine_similarity(before: np.ndarray, after: np.ndarray, axis: int = -1) -> np.ndarray:
    numerator = np.sum(before * after, axis=axis)
    denominator = np.linalg.norm(before, axis=axis) * np.linalg.norm(after, axis=axis)
    return numerator / np.maximum(denominator, 1e-12)


def choose_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    strict = [row for row in rows if row["strict_envelope_accepted"]]
    if strict:
        return max(strict, key=lambda row: row["target_token_logprob_delta"])
    gate = [row for row in rows if row["gate_preview_accepted"]]
    if gate:
        return max(gate, key=lambda row: row["target_token_logprob_delta"])
    return max(rows, key=lambda row: row["target_token_logprob_delta"])


def write_visual(path: Path, audit: dict[str, Any]) -> None:
    rows = audit["rows"]
    chosen = audit["chosen"]
    metrics = audit["official_certificate"]["metrics"]
    width, height = 1160, 690
    ml, mt = 82, 84
    plot_w, plot_h = 660, 380
    max_alpha = max(row["alpha"] for row in rows)
    max_delta = max(row["target_token_logprob_delta"] for row in rows) * 1.14 or 1.0

    def x(alpha: float) -> float:
        return ml + alpha / max_alpha * plot_w

    def y(delta: float) -> float:
        return mt + plot_h - delta / max_delta * plot_h

    points = " ".join(f"{x(row['alpha']):.1f},{y(row['target_token_logprob_delta']):.1f}" for row in rows)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f6f6f2"/>',
        '<text x="44" y="40" font-family="Arial, sans-serif" font-size="25" font-weight="700" fill="#1a1a1a">Envelope-pushed real-model audit</text>',
        '<text x="44" y="64" font-family="Arial, sans-serif" font-size="13" fill="#555">Certified France/Paris steering plus guard preservation and forbidden Paris-leakage checks.</text>',
        f'<rect x="{ml}" y="{mt}" width="{plot_w}" height="{plot_h}" fill="#fff" stroke="#d0d0c8"/>',
    ]
    for i in range(6):
        yy = mt + i * plot_h / 5
        value = max_delta * (1 - i / 5)
        svg.append(f'<line x1="{ml}" y1="{yy:.1f}" x2="{ml + plot_w}" y2="{yy:.1f}" stroke="#e9e9e2"/>')
        svg.append(f'<text x="{ml - 10}" y="{yy + 4:.1f}" text-anchor="end" font-family="Arial, sans-serif" font-size="11" fill="#666">{value:.2f}</text>')
    svg.append(f'<polyline points="{points}" fill="none" stroke="#185f8d" stroke-width="3"/>')
    for row in rows:
        color = "#218a3b" if row["strict_envelope_accepted"] else ("#d28a19" if row["gate_preview_accepted"] else "#999")
        svg.append(f'<circle cx="{x(row["alpha"]):.1f}" cy="{y(row["target_token_logprob_delta"]):.1f}" r="5" fill="{color}" stroke="#fff" stroke-width="1.5"/>')
    svg.append(f'<circle cx="{x(chosen["alpha"]):.1f}" cy="{y(chosen["target_token_logprob_delta"]):.1f}" r="10" fill="none" stroke="#c43d2b" stroke-width="3"/>')
    svg.append(f'<text x="{ml + plot_w / 2:.1f}" y="{height - 48}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#333">alpha sweep, selected alpha {chosen["alpha"]}</text>')
    svg.append(f'<text transform="translate(26 {mt + plot_h / 2:.1f}) rotate(-90)" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#333">mean target token log-prob delta</text>')

    panel_x, panel_y = 790, 94
    svg.append(f'<rect x="{panel_x}" y="{panel_y}" width="320" height="258" rx="6" fill="#eff5ef" stroke="#c5d4c3"/>')
    svg.append(f'<text x="{panel_x + 18}" y="{panel_y + 30}" font-family="Arial, sans-serif" font-size="16" font-weight="700" fill="#1a1a1a">Official packet metrics</text>')
    summary = [
        ("Accepted", str(audit["official_certificate"]["accepted"])),
        ("Target delta", f"{metrics['target_token_logprob_delta']:.6g}"),
        ("Off-target degradation", f"{metrics['off_target_degradation_max']:.6g}"),
        ("Forbidden Paris leak max", f"{chosen['forbidden_paris_leakage_max']:.6g}"),
        ("Norm max", f"{metrics['norm_delta_max']:.6g}"),
        ("Cosine min", f"{metrics['cosine_drift_min']:.6g}"),
        ("Rollback residue", f"{metrics['rollback_residue']:.6g}"),
        ("Weights changed", str(metrics["weight_fingerprint_changed"])),
    ]
    yy = panel_y + 60
    for label, value in summary:
        svg.append(f'<text x="{panel_x + 18}" y="{yy}" font-family="Arial, sans-serif" font-size="12" fill="#555">{label}</text>')
        svg.append(f'<text x="{panel_x + 296}" y="{yy}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="#1a1a1a">{value}</text>')
        yy += 24

    bar_x, bar_y = 790, 390
    svg.append(f'<text x="{bar_x}" y="{bar_y}" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#1a1a1a">Chosen run per-case deltas</text>')
    items = []
    items.extend((label, value, "#218a3b") for label, value in chosen["target_case_deltas"].items())
    items.extend((label, value, "#6f7f8f") for label, value in chosen["off_target_case_deltas"].items())
    items.extend((label, value, "#c43d2b") for label, value in chosen["forbidden_paris_case_deltas"].items())
    max_abs = max(abs(value) for _label, value, _color in items) or 1.0
    zero = bar_x + 142
    svg.append(f'<line x1="{zero}" y1="{bar_y + 18}" x2="{zero}" y2="{bar_y + 250}" stroke="#888"/>')
    yy = bar_y + 38
    for label, value, color in items:
        bar_width = abs(value) / max_abs * 136
        x0 = zero if value >= 0 else zero - bar_width
        svg.append(f'<text x="{bar_x}" y="{yy + 4}" font-family="Arial, sans-serif" font-size="10.5" fill="#555">{label}</text>')
        svg.append(f'<rect x="{x0:.1f}" y="{yy - 9}" width="{bar_width:.1f}" height="14" fill="{color}"/>')
        svg.append(f'<text x="{zero + 145}" y="{yy + 4}" font-family="Arial, sans-serif" font-size="10.5" fill="#222">{value:.4g}</text>')
        yy += 17
    svg.append('<text x="44" y="650" font-family="Arial, sans-serif" font-size="12" fill="#555">Green points satisfy the stricter envelope gate. Red forbidden bars should stay at or below zero, with leakage threshold 0.02.</text>')
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def write_assessment(
    path: Path,
    audit: dict[str, Any],
    prompt_suite_path: Path,
    forbidden_suite_path: Path,
    vector_path: Path,
    sweep_path: Path,
    certified_report_path: Path,
    visual_path: Path,
) -> None:
    chosen = audit["chosen"]
    metrics = audit["official_certificate"]["metrics"]
    strict_status = "passed" if chosen["strict_envelope_accepted"] else "failed"
    interpretation = (
        "The envelope-pushed run shows a stronger and more specific real-model activation effect than the previous packet. "
        "It improved the France/Paris prompts, preserved the measured guard answers, and kept forbidden Paris leakage within "
        "the stricter audit threshold, while still passing the unchanged packet/certificate gate."
        if chosen["strict_envelope_accepted"]
        else "The envelope-pushed run found the current boundary. The official packet/certificate gate accepted the aggregate "
        "behavior, but the stricter per-case audit rejected the result. The same final-stream vector could not simultaneously "
        "maximize France/Paris uplift, preserve every individual guard answer, and suppress Paris leakage on non-France capital "
        "prompts. This is exactly the kind of blast-radius finding the certification protocol is meant to expose."
    )
    text = f"""# Real-Model Envelope Assessment

## Spec Review

- The governing rule remains: typed packet, bounded intervention, behavior check, rollback check, and human-auditable report.
- The real-model phase remains optional and local-only. No downloads, training, optimizer state, `save_pretrained`, persistent weight edits, or production deployment paths are used.
- The current certified real-model work reaches Levels 1, 2, 3, and 6 for this local model. It does not yet claim causal Level 4, spectral Level 5 on real transformer dynamics, or cross-model Level 7.

## Progress

- Synthetic Phase 0 suite remains the baseline certificate path.
- Hugging Face real-model adapter is functional on a local cached Pythia-70M assembly.
- TransformerLens remains unavailable in this environment, so that backend is not yet smoke-tested locally.
- Prior single-prompt and multi-prompt Paris steering packets were accepted with clean rollback and unchanged weight fingerprints.

## Envelope Push

This run tightened the audit by adding forbidden Paris-leakage checks. The vector was derived under no-grad math from final-stream log-prob directions, with three simultaneous aims:

- improve France prompts whose target token is ` Paris`;
- preserve correct off-target answers such as ` Berlin`, ` Madrid`, ` Rome`, ` Tokyo`, ` 4`, and ` cold`;
- avoid raising ` Paris` on non-France capital prompts beyond the leakage threshold.

## Result

- Official certificate accepted: `{audit["official_certificate"]["accepted"]}`
- Strict envelope audit: `{strict_status}`
- Selected alpha: `{chosen["alpha"]}`
- Mean target token log-prob delta: `{metrics["target_token_logprob_delta"]}`
- Minimum target-case delta: `{chosen["target_case_delta_min"]}`
- Off-target degradation: `{metrics["off_target_degradation_max"]}`
- Max per-case off-target degradation: `{chosen["off_target_case_degradation_max"]}`
- Max forbidden Paris leakage: `{chosen["forbidden_paris_leakage_max"]}`
- Norm delta max: `{metrics["norm_delta_max"]}`
- Cosine drift min: `{metrics["cosine_drift_min"]}`
- Rollback residue: `{metrics["rollback_residue"]}`
- Weight fingerprint changed: `{metrics["weight_fingerprint_changed"]}`
- Hook cleanup: `{metrics["hook_cleanup_ok"]}`

## Interpretation

{interpretation}

The remaining limitation is important: this is still a final-stream token-level intervention on one local checkpoint. It is not production semantic surgery and does not prove cross-model generalization or deep causal locality.

## Artifacts

- Prompt suite: `{prompt_suite_path.as_posix()}`
- Forbidden suite: `{forbidden_suite_path.as_posix()}`
- Vector: `{vector_path.as_posix()}`
- Sweep: `{sweep_path.as_posix()}`
- Certified report: `{certified_report_path.as_posix()}`
- Visual: `{visual_path.as_posix()}`
"""
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
