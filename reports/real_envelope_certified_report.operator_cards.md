# CSS Operator Cards

## real_activation_surgery_probe

Operator name: real_activation_additive
Target state: synthetic probe state
Operator form: real_activation_additive
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["controlled_real_activation_surgery"], "backend": "huggingface", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": "C:\\Users\\jamie\\AppData\\Local\\Temp\\css_hf_pythia70m_local", "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "accepted"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: {"cosine_drift_min": 0.98, "norm_delta_max": 1.0}
Spectral bounds: not declared
Behavioral result: {"off_target_degradation_max": 0.0, "off_target_delta": 0.10807291666666696, "target_success_delta": 0.291015625, "target_token_logprob_delta": 0.291015625}
Rollback result: {"rollback_residue": 0.0}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Controlled local real-model semantic surgery packet for real_activation_surgery_probe.
