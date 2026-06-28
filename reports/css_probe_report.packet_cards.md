# CSS Packet Cards

## ssp_activation_patch_probe

Operator name: activation_additive
Target state: activation_stream / residual
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": 0.05, "target_metric": "target_success_delta"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": ["off_target_regression_probe", "activation_patch_probe"], "causal_tests": [], "spectral_tests": [], "unit_tests": ["norm_drift_probe", "rollback_probe"]}
Evidence: {"per_case": {}, "verifier_metrics": {"cosine_drift_min": 0.9886860023785768, "norm_delta_max": 0.14999999999993371, "off_target_degradation_max": 0.0, "rollback_residue": 5.551115123125783e-17, "target_success_delta": 0.3203125}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for activation_patch_probe.

## ssp_low_rank_operator_probe

Operator name: activation_low_rank
Target state: activation_stream / residual
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "accepted"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": ["activation_patch_probe"], "causal_tests": [], "spectral_tests": ["spectral_radius_probe"], "unit_tests": ["norm_drift_probe", "rollback_probe"]}
Evidence: {"per_case": {}, "verifier_metrics": {"cosine_drift_min": 0.9998638825927529, "norm_delta_max": 0.01871778163047479, "rollback_residue": 6.106226635438361e-16}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for low_rank_operator_probe.

## ssp_norm_drift_probe

Operator name: activation_additive
Target state: activation_stream / residual
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "accepted"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": [], "causal_tests": [], "spectral_tests": [], "unit_tests": ["norm_drift_probe"]}
Evidence: {"per_case": {}, "verifier_metrics": {"cosine_drift_min": 0.9949874393852146, "norm_delta_max": 0.09999999999998635}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for norm_drift_probe.

## ssp_spectral_radius_probe

Operator name: activation_low_rank
Target state: activation_stream / residual
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "accepted"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": [], "causal_tests": [], "spectral_tests": ["spectral_radius_probe"], "unit_tests": []}
Evidence: {"per_case": {}, "verifier_metrics": {}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for spectral_radius_probe.

## ssp_pseudospectrum_probe

Operator name: synthetic_linear_dynamics
Target state: linear_state / state
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "accepted"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": [], "causal_tests": [], "spectral_tests": ["spectral_radius_probe", "pseudospectrum_probe"], "unit_tests": []}
Evidence: {"per_case": {}, "verifier_metrics": {}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for pseudospectrum_probe.

## ssp_causal_locality_probe

Operator name: activation_additive
Target state: activation_stream / residual
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": 0.25, "target_metric": "target_margin_delta"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": ["activation_patch_probe"], "causal_tests": ["causal_locality_probe"], "spectral_tests": [], "unit_tests": []}
Evidence: {"per_case": {}, "verifier_metrics": {}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for causal_locality_probe.

## ssp_off_target_regression_probe

Operator name: activation_additive
Target state: activation_stream / residual
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": 0.2, "target_metric": "target_margin_delta"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": ["off_target_regression_probe", "activation_patch_probe"], "causal_tests": ["causal_locality_probe"], "spectral_tests": [], "unit_tests": []}
Evidence: {"per_case": {}, "verifier_metrics": {"off_target_degradation_max": 0.0}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for off_target_regression_probe.

## ssp_rollback_probe

Operator name: activation_additive
Target state: activation_stream / residual
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "accepted"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": [], "causal_tests": [], "spectral_tests": [], "unit_tests": ["rollback_probe"]}
Evidence: {"per_case": {}, "verifier_metrics": {"rollback_residue": 0.0}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for rollback_probe.

## ssp_operator_vs_text_benchmark

Operator name: activation_additive
Target state: activation_stream / residual
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "operator_absolute_advantage"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": ["off_target_regression_probe", "activation_patch_probe"], "causal_tests": [], "spectral_tests": [], "unit_tests": []}
Evidence: {"per_case": {}, "verifier_metrics": {"off_target_degradation_max": 0.0}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for operator_vs_text_benchmark.

## ssp_koopman_dynamics_message_probe

Operator name: local_dynamics
Target state: dynamics_state / trajectory
Persistence: removable
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "one_step_mse_improvement"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": [], "causal_tests": [], "spectral_tests": ["spectral_radius_probe", "pseudospectrum_probe"], "unit_tests": []}
Evidence: {"per_case": {}, "verifier_metrics": {}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for koopman_dynamics_message_probe.

## ssp_proof_state_surgery_probe

Operator name: proof_state_transition
Target state: proof_state / proof_stack
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["synthetic_probe_suite"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": null, "target_metric": "proof_closed"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": [], "causal_tests": [], "spectral_tests": [], "unit_tests": ["proof_state_surgery_probe"]}
Evidence: {"per_case": {}, "verifier_metrics": {}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for proof_state_surgery_probe.

## ssp_kv_cache_surgery_probe

Operator name: kv_cache_additive
Target state: kv_cache / key
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["toy_kv_cache_surgery"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": 0.05, "target_metric": "target_success_delta"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": ["off_target_regression_probe", "activation_patch_probe"], "causal_tests": ["causal_locality_probe"], "spectral_tests": [], "unit_tests": ["norm_drift_probe", "rollback_probe"]}
Evidence: {"per_case": {}, "verifier_metrics": {"cosine_drift_min": 0.9888102735743266, "norm_delta_max": 0.07999999999992001, "off_target_degradation_max": 0.0, "rollback_residue": 0.0, "target_success_delta": 0.07999999999989812}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for kv_cache_surgery_probe.

## ssp_lora_adapter_dry_run_probe

Operator name: lora_adapter_dry_run
Target state: adapter_delta / linear_weight
Persistence: removable
Preconditions: {"allowed_tasks": ["removable_lora_adapter_dry_run"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": 0.05, "target_metric": "target_success_delta"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": ["off_target_regression_probe", "activation_patch_probe"], "causal_tests": [], "spectral_tests": ["spectral_radius_probe"], "unit_tests": ["norm_drift_probe", "rollback_probe", "real_model_no_weight_mutation"]}
Evidence: {"per_case": {}, "verifier_metrics": {"cosine_drift_min": 0.9997639353655692, "norm_delta_max": 0.07772968007691004, "off_target_degradation_max": 0.0, "rollback_residue": 0.0, "target_success_delta": 0.0617394716432802, "weight_fingerprint_changed": false}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for lora_adapter_dry_run_probe.

## ssp_cross_checkpoint_transfer_probe

Operator name: cross_checkpoint_activation_additive
Target state: activation_stream / residual
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["cross_checkpoint_transfer_validation"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": 0.05, "target_metric": "target_success_delta"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": ["off_target_regression_probe", "activation_patch_probe"], "causal_tests": [], "spectral_tests": [], "unit_tests": ["norm_drift_probe", "rollback_probe"]}
Evidence: {"per_case": {}, "verifier_metrics": {"cosine_drift_min": 0.9871170230062709, "cross_model_transfer_passed": true, "norm_delta_max": 0.15999999999997816, "off_target_degradation_max": 0.0, "rollback_residue": 5.551115123125783e-17, "target_success_delta": 0.14692325090331795}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for cross_checkpoint_transfer_probe.

## ssp_adversarial_packet_fuzz_probe

Operator name: adversarial_packet_fuzzing
Target state: packet_policy / validator
Persistence: ephemeral
Preconditions: {"allowed_tasks": ["packet_policy_fuzzing"], "backend": "synthetic", "deterministic_seed": 0, "local_files_only": true, "model_name_or_path": null, "requires_sandbox": true}
Intended effect: {"description": "Satisfy the synthetic probe acceptance contract without violating Phase 0 bounds.", "minimum_delta": 0.05, "target_metric": "target_success_delta"}
Forbidden effects: off_target_degradation_gt_0.02, cosine_drift_below_0.98, rollback_residue_gt_1e-9, unstable_spectral_or_pseudospectral_growth
Verifier: {"behavioral_tests": ["off_target_regression_probe", "activation_patch_probe"], "causal_tests": [], "spectral_tests": [], "unit_tests": ["norm_drift_probe", "rollback_probe"]}
Evidence: {"per_case": {}, "verifier_metrics": {"cosine_drift_min": 1.0, "norm_delta_max": 0.0, "off_target_degradation_max": 0.0, "rollback_residue": 0.0, "target_success_delta": 1.0}}
Accepted / rejected: accepted
Rejection reasons: none
Human rendering: Synthetic certified semantic surgery packet for adversarial_packet_fuzz_probe.
