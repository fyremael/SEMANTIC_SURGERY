import json
import importlib.util
import subprocess
import sys
from pathlib import Path

from css_probes.core import ProbeResult
from css_probes.hooks.base import ActivationSurgeryConfig, PromptCase, PromptSuite, RealActivationResult
from css_probes.packets import packet_from_result, verify_packet_shape
from css_probes.probes.real_activation_surgery import run_real_activation_surgery


ROOT = Path(__file__).resolve().parents[1]


class FakeAdapter:
    name = "fake"

    def run_activation_surgery(self, config):
        return RealActivationResult(
            backend="fake",
            model_family="FakeCausalLM",
            model_name_or_path=config.model_name_or_path,
            layer=config.layer,
            stream=config.stream,
            shape=[3],
            metrics={
                "target_token_logprob_delta": 0.125,
                "target_success_delta": 0.125,
                "off_target_delta": 0.0,
                "off_target_degradation_max": 0.0,
                "norm_delta_mean": 0.1,
                "norm_delta_max": 0.1,
                "cosine_drift_mean": 0.995,
                "cosine_drift_min": 0.995,
                "rollback_residue": 0.0,
                "weight_fingerprint_changed": False,
                "hook_cleanup_ok": True,
                "local_files_only": True,
            },
            operator={
                "form": "h_prime = h + alpha * v",
                "rank": 1,
                "parameters_ref": "inline",
                "parameter_hash": "sha256:fake",
                "alpha": config.alpha,
            },
            notes=["fake adapter verifier"],
        )


def test_importing_core_package_does_not_import_optional_backends():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, css_probes; print('torch' in sys.modules, 'transformers' in sys.modules, 'transformer_lens' in sys.modules)",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False False False"


def test_real_list_adapters_reports_backends_without_loading_models():
    result = subprocess.run(
        [sys.executable, "-m", "css_probes.cli", "real", "list-adapters"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert {item["name"] for item in payload} == {"huggingface", "transformer-lens"}
    assert all("install_hint" in item for item in payload)


def test_missing_transformer_lens_backend_has_actionable_cli_error(tmp_path):
    if importlib.util.find_spec("transformer_lens") is not None:
        return
    prompt_suite = tmp_path / "suite.json"
    prompt_suite.write_text(
        json.dumps(
            {
                "target": [{"prompt": "Alpha", "target_token": " beta"}],
                "off_target": [{"prompt": "One", "target_token": " two"}],
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "css_probes.cli",
            "real",
            "activation-surgery",
            "--backend",
            "transformer-lens",
            "--model",
            "local-only-model",
            "--prompt-suite",
            str(prompt_suite),
            "--layer",
            "0",
            "--stream",
            "residual",
            "--out",
            str(tmp_path / "real.json"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "backend unavailable" in result.stderr or "install with:" in result.stderr


def test_fake_real_adapter_emits_valid_packet_and_certificate():
    suite = PromptSuite(
        target=[PromptCase(prompt="The capital of France is", target_token=" Paris")],
        off_target=[PromptCase(prompt="2 + 2 =", target_token=" 4")],
    )
    config = ActivationSurgeryConfig(
        backend="fake",
        model_name_or_path="fake-local-model",
        prompt_suite=suite,
        layer=0,
        stream="residual",
        alpha=0.1,
        vector=[0.1, 0.0, 0.0],
    )

    result = run_real_activation_surgery(config, adapter=FakeAdapter())
    packet = packet_from_result(result)
    ok, warnings = verify_packet_shape(packet)

    assert result.accepted is True
    assert ok, warnings
    assert packet.target.model_family == "FakeCausalLM"
    assert packet.persistence == "ephemeral"
    assert packet.preconditions["local_files_only"] is True
    assert packet.postconditions["weight_fingerprint_changed"] is False
    assert "real_model_hook_cleanup" in packet.verifier.unit_tests


def test_fake_real_adapter_failure_returns_rejected_report():
    class FailingAdapter:
        def run_activation_surgery(self, config):
            raise ValueError("shape mismatch")

    suite = PromptSuite(
        target=[PromptCase(prompt="A", target_token=" B")],
        off_target=[PromptCase(prompt="C", target_token=" D")],
    )
    config = ActivationSurgeryConfig(
        backend="fake",
        model_name_or_path="fake-local-model",
        prompt_suite=suite,
        layer=0,
        stream="residual",
        vector=[0.1],
    )

    result = run_real_activation_surgery(config, adapter=FailingAdapter())

    assert result.accepted is False
    assert result.metrics["hook_cleanup_ok"] is False
    assert any("real_adapter_failure:ValueError" in warning for warning in result.warnings)


def test_real_adapter_rejects_disabled_local_only_mode_without_running_adapter():
    class ShouldNotRunAdapter:
        def run_activation_surgery(self, config):
            raise AssertionError("adapter should not run when local_files_only is false")

    suite = PromptSuite(
        target=[PromptCase(prompt="A", target_token=" B")],
        off_target=[PromptCase(prompt="C", target_token=" D")],
    )
    config = ActivationSurgeryConfig(
        backend="fake",
        model_name_or_path="fake-local-model",
        prompt_suite=suite,
        layer=0,
        stream="residual",
        vector=[0.1],
        local_files_only=False,
    )

    result = run_real_activation_surgery(config, adapter=ShouldNotRunAdapter())

    assert result.accepted is False
    assert result.metrics["local_files_only"] is False
    assert any("local_files_only must remain true" in warning for warning in result.warnings)


def test_real_adapter_rejects_persistence_warning_from_adapter():
    class PersistentAdapter(FakeAdapter):
        def run_activation_surgery(self, config):
            result = super().run_activation_surgery(config)
            result.operator["persistence"] = "persistent"
            return result

    suite = PromptSuite(
        target=[PromptCase(prompt="The capital of France is", target_token=" Paris")],
        off_target=[PromptCase(prompt="2 + 2 =", target_token=" 4")],
    )
    config = ActivationSurgeryConfig(
        backend="fake",
        model_name_or_path="fake-local-model",
        prompt_suite=suite,
        layer=0,
        stream="residual",
        alpha=0.1,
        vector=[0.1, 0.0, 0.0],
    )

    result = run_real_activation_surgery(config, adapter=PersistentAdapter())

    assert result.accepted is False
    assert "persistence_warning:persistent" in result.warnings


def test_persistent_real_model_packet_is_rejected_by_existing_gate():
    result = ProbeResult(
        name="real_activation_surgery_probe",
        status="fail",
        seed=0,
        metrics={
            "target_token_logprob_delta": 0.0,
            "off_target_degradation_max": 0.0,
            "norm_delta_max": 0.0,
            "cosine_drift_min": 1.0,
            "rollback_residue": 0.0,
            "weight_fingerprint_changed": False,
            "hook_cleanup_ok": True,
        },
        thresholds={},
        accepted=False,
        warnings=["persistence_warning:persistent"],
        notes=[],
        operator={
            "operator_type": "real_activation_additive",
            "persistence": "persistent",
            "backend": "fake",
            "model_family": "FakeCausalLM",
            "model_name_or_path": "fake-local-model",
            "declared_layer": 0,
            "stream": "residual",
            "target_shape": [3],
            "state_type": "activation_stream",
            "form": "h_prime = h + alpha * v",
            "rank": 1,
            "parameters_ref": "inline",
            "parameter_hash": "sha256:fake",
            "local_files_only": True,
            "allowed_tasks": ["controlled_real_activation_surgery"],
        },
    )

    packet = packet_from_result(result)
    ok, warnings = verify_packet_shape(packet)

    assert ok is False
    assert "phase0_rejected_persistence:persistent" in warnings
