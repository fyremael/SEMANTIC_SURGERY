# CSS Operator Cards

## activation_patch_probe

Operator name: activation_additive
Target state: synthetic probe state
Operator form: activation_additive
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": 0.05, "target_metric": "target_success_delta"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: {"cosine_drift_min": 0.98, "norm_delta_max": 1.0}
Spectral bounds: not declared
Behavioral result: {"off_target_degradation_max": 0.0, "off_target_delta": 0.018653450143599294, "target_margin_delta": 0.14225706563550805, "target_success_delta": 0.3203125}
Rollback result: {"rollback_residue": 5.551115123125783e-17}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for activation_patch_probe.

## low_rank_operator_probe

Operator name: activation_low_rank
Target state: synthetic probe state
Operator form: activation_low_rank
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "accepted"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: {"cosine_drift_min": 0.98}
Spectral bounds: {"sigma_max": 1.1, "spectral_radius_max": 1.05}
Behavioral result: {"off_target_delta": 4.460877918988342e-06, "target_margin_delta": -0.00018863841924529265}
Rollback result: {"rollback_residue": 6.106226635438361e-16}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for low_rank_operator_probe.

## norm_drift_probe

Operator name: activation_additive
Target state: synthetic probe state
Operator form: activation_additive
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "accepted"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: {"cosine_drift_min": 0.98, "norm_delta_max": 1.0}
Spectral bounds: not declared
Behavioral result: not declared
Rollback result: not declared
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for norm_drift_probe.

## spectral_radius_probe

Operator name: activation_low_rank
Target state: synthetic probe state
Operator form: activation_low_rank
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "accepted"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: not declared
Spectral bounds: {"sigma_max": 1.1, "spectral_radius_max": 1.05, "transient_growth_max": 1.7}
Behavioral result: not declared
Rollback result: not declared
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for spectral_radius_probe.

## pseudospectrum_probe

Operator name: synthetic_linear_dynamics
Target state: synthetic probe state
Operator form: synthetic_linear_dynamics
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "accepted"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: not declared
Spectral bounds: {"pseudospectral_proxy_max": 5.0, "sigma_max": 1.1, "spectral_radius_max": 1.05, "transient_growth_proxy_max": 12.0}
Behavioral result: not declared
Rollback result: not declared
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for pseudospectrum_probe.

## causal_locality_probe

Operator name: activation_additive
Target state: synthetic probe state
Operator form: activation_additive
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": 0.25, "target_metric": "target_margin_delta"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: not declared
Spectral bounds: not declared
Behavioral result: {"causal_locality_score": 5.801916439120177, "locality_ratio": 5.801916439120177, "target_delta": 0.3999999999998692, "target_margin_delta": 0.3999999999998692}
Rollback result: not declared
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for causal_locality_probe.

## off_target_regression_probe

Operator name: activation_additive
Target state: synthetic probe state
Operator form: activation_additive
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": 0.2, "target_metric": "target_margin_delta"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: not declared
Spectral bounds: not declared
Behavioral result: {"causal_locality_score": 299516272965.56256, "off_target_degradation_max": 0.0, "off_target_delta": 1.6150275561344074e-15, "target_margin_delta": 0.2999999999999126}
Rollback result: not declared
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for off_target_regression_probe.

## rollback_probe

Operator name: activation_additive
Target state: synthetic probe state
Operator form: activation_additive
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "accepted"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: not declared
Spectral bounds: not declared
Behavioral result: not declared
Rollback result: {"rollback_residue": 0.0}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for rollback_probe.

## operator_vs_text_benchmark

Operator name: activation_additive
Target state: synthetic probe state
Operator form: activation_additive
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "operator_absolute_advantage"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: not declared
Spectral bounds: not declared
Behavioral result: {"additive_operator_off_target_delta": 1.8856444183867893e-15, "additive_operator_target_margin_delta": 0.34999999999989806, "latent_vector_off_target_delta": 0.0015428105550000185, "latent_vector_target_margin_delta": 0.34462173694752035, "low_rank_operator_off_target_delta": -2.388411646652485e-05, "low_rank_operator_target_margin_delta": -0.0005283344063082372, "no_message_target_margin_delta": 0.0, "off_target_degradation_max": 0.0, "operator_off_target_degradation_max": 0.0, "operator_plus_certificate_target_margin_delta": 0.34999999999989806, "target_margin_delta": 0.34999999999989806, "text_off_target_delta": -0.021983000375058855, "text_target_margin_delta": 0.041888705939917885}
Rollback result: not declared
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for operator_vs_text_benchmark.

## koopman_dynamics_message_probe

Operator name: local_dynamics
Target state: synthetic probe state
Operator form: local_dynamics
Persistence: removable
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "one_step_mse_improvement"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: {"rollout_max_norm_max": 5.0}
Spectral bounds: {"pseudospectral_proxy_max": 5.0, "sigma_max": 1.1, "spectral_radius_max": 1.05}
Behavioral result: not declared
Rollback result: not declared
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for koopman_dynamics_message_probe.

## proof_state_surgery_probe

Operator name: proof_state_transition
Target state: synthetic probe state
Operator form: proof_state_transition
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "proof_closed"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Norm bounds: not declared
Spectral bounds: not declared
Behavioral result: {"checker_accepted": true}
Rollback result: not declared
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for proof_state_surgery_probe.
