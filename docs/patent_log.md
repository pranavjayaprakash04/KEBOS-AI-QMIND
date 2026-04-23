# Patent Log - Novel Contributions

## Patent Claim 3: Server-side behavioural biometrics via API request graph

### 2026-04-22
**File(s):** kebos-backend/app/ueba/baseline_engine.py
**Claim:** Patent Claim 3 - Server-side behavioural biometrics via API request graph (UEBA engine)
**Description:** 
Implemented UEBA Baseline Engine that builds behavioural profiles for users based on API request patterns. The system tracks features including hour_of_day, day_of_week, source_ip, endpoint, request_size_bytes, and user_agent. Uses Welford online algorithm to compute mean and variance incrementally without storing all historical data. Computes Mahalanobis distance to detect anomalies. When anomaly score > 0.8, automatically injects insider threat signals to QMind for analysis. This enables detection of compromised accounts and insider threats based on behavioral deviations from established baselines.

**Key Novel Mechanisms:**
1. Welford online algorithm for efficient baseline computation (O(1) memory per feature)
2. Mahalanobis distance for multi-dimensional anomaly detection
3. Automatic signal injection to QMind for UEBA-detected anomalies
4. Minimum sample threshold (50 samples) to prevent false positives during ramp-up

**Implementation Status:** Fully implemented, not stubbed.
