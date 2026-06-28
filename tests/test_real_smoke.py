import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROMPT_SUITE = ROOT / "examples" / "prompt_suite_harmless.json"


@pytest.mark.skipif(not os.environ.get("CSS_HF_MODEL_PATH"), reason="CSS_HF_MODEL_PATH not configured")
def test_optional_huggingface_local_smoke(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "css_probes.cli",
            "real",
            "activation-surgery",
            "--backend",
            "huggingface",
            "--model",
            os.environ["CSS_HF_MODEL_PATH"],
            "--prompt-suite",
            str(PROMPT_SUITE),
            "--layer",
            "0",
            "--stream",
            "residual",
            "--out",
            str(tmp_path / "hf_real.json"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode in {0, 1}, result.stderr
    assert (tmp_path / "hf_real.json").exists()


@pytest.mark.skipif(not os.environ.get("CSS_TL_MODEL_PATH"), reason="CSS_TL_MODEL_PATH not configured")
def test_optional_transformer_lens_local_smoke(tmp_path):
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
            os.environ["CSS_TL_MODEL_PATH"],
            "--prompt-suite",
            str(PROMPT_SUITE),
            "--layer",
            "0",
            "--stream",
            "residual",
            "--out",
            str(tmp_path / "tl_real.json"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode in {0, 1}, result.stderr
    assert (tmp_path / "tl_real.json").exists()
