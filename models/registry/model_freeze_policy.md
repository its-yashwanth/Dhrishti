# Drishti Model Freeze, Preservation, and Governance Policy

**Document ID:** `POL-MODEL-FREEZE-001`  
**Effective Date:** 2026-10-16  
**Governing Phase:** Phase 6.7 — Best-Model Selection, Preservation, and Legacy Model Cleanup  
**Authority:** Drishti Model Architecture & Governance Board  

---

## 1. Purpose and Scope

This policy establishes immutable operational rules governing the preservation, protection, modification, and retirement of machine learning models in the Drishti project.

Its scope covers:
1. The five strictly frozen model tracks.
2. The active production baseline models in `models/`.
3. Upstream and downstream adapters, preprocessors, and agent inference pipelines.
4. Legacy model retirement, backup, and cleanup procedures.

---

## 2. Policy Section I: Strictly Frozen Model Tracks

The following five models represent finalized best-in-class performance benchmarks in the Drishti project and are **PERMANENTLY FROZEN**:

1. **Model A (1M Trade Impact):** `experiments/mandatory_ml_performance_optimization/models/model_a_log_value_1m_lgb.joblib`
2. **Model A (3M Trade Impact):** `experiments/mandatory_ml_performance_optimization/models/model_a_log_value_3m_lgb.joblib`
3. **Model C (1M Price Impact):** `experiments/mandatory_ml_performance_optimization/models/model_c_log_price_1m_lgb.joblib`
4. **Model C (3M Price Impact):** `experiments/mandatory_ml_performance_optimization/models/model_c_log_price_3m_lgb.joblib`
5. **Model B-1 (National Yield):** `experiments/mandatory_ml_performance_optimization/models/model_b1_national_yield_lgb.joblib`

### Mandatory Freeze Rules:
- **Rule 1 (Zero Retraining):** No script, automated pipeline, or agent shall execute training, fine-tuning, or parameter updates on these artifacts.
- **Rule 2 (Zero Weight Overwrite):** The serialized binary weights (`.joblib`) shall not be overwritten, re-saved, compressed, or modified in any way.
- **Rule 3 (Immutable Preprocessing):** Feature sets, encoders, target transformations ($\ln(1+y)$, $\ln(y)$), and preprocessing logic must remain bit-identical.
- **Rule 4 (Cryptographic Parity):** Every CI/CD run, test suite, and audit must verify that SHA-256 checksums match the baseline registered in `models/registry/preservation_manifest.json`.

---

## 3. Policy Section II: Production Promotion & Active Model Directory

The active model directory (`models/`) is strictly reserved for models actively used in live inference or production agent cascades:

1. **Clean Directory Invariant:** `models/` shall contain only the selected primary models and required baselines. Temporary training artifacts, out-of-fold predictions, and experimental checkpoints must reside in isolated experiment directories.
2. **Promotion Criteria:**
   - Must beat the persistence baseline on out-of-sample MAE on a statistically valid test set ($N \ge 50$ for time series).
   - Must achieve non-negative out-of-sample $R^2$ ($R^2 > 0.0$).
   - Must provide an automated interface adapter for backward compatibility.
3. **Rejection & Baseline Retention:**
   - Any candidate model that underperforms the persistence baseline (e.g., 1-month food inflation ML candidate deteriorating by $27.20\%$) must be rejected.
   - The persistence baseline must remain the active production forecasting method for that task.

---

## 4. Policy Section III: Legacy Model Retirement and Cleanup

Before any model artifact is removed from the active directory:
1. **Mandatory Backup:** A complete copy must be created in `archive/legacy_models_backup_phase_6_7/models_pre_cleanup/` and verified with byte size and SHA-256 hash match.
2. **Dependency Audit:** Downstream code (`drishti_mcp/tools/ml_cascade_tool.py`, `scripts/cascade_orchestrator.py`, `scripts/event_store.py`) must be audited to ensure zero broken dependencies.
3. **Deletion Manifest:** Every deletion must be cataloged in `experiments/phase_6_7_model_preservation/deletion_manifest.csv` with reason, backup path, and replacement path.
4. **Zero Metric Deletion:** Deleting model weights does NOT delete historical records. All metrics must be preserved in `models/registry/complete_model_metric_history.csv`.

---

## 5. Policy Section IV: Missing Metric Handling

- Under no circumstances shall missing metrics be filled with `0`, `0.0`, or fabricated numbers.
- If an evaluation metric (such as RMSE, Deficit F1, or baseline MAE) was not reported in the original verified experiment log, it must be explicitly recorded as `NOT_AVAILABLE`.
- Any historical metric whose underlying artifact or split boundaries cannot be independently confirmed must be flagged as `REPORTED_UNVERIFIED`.
