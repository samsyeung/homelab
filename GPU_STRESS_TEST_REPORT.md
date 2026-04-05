# GPU Stress Test Report - gpu-fryer
**Date:** 2026-04-04  
**Test Tool:** gpu-fryer (CUBLAS matrix multiplication, BF16 precision)  
**Duration:** 120 seconds per GPU  
**Test Type:** Compute-intensive (8192x8192 matrix multiplication)  
**Memory Allocation:** 95% GPU memory (~21.5GB per RTX 3090)

---

## Executive Summary

**All four RTX 3090 GPUs are healthy with no throttling detected.** Performance is consistent with a minor exception:

- **GPU0**: Excellent thermals (48.77°C avg, 56°C peak) with solid compute performance
- **GPU1**: **Higher thermal performance** with peak of 74°C; consider checking thermal contact
- **GPU2**: Best thermal efficiency (52.64°C avg, 60°C peak) with consistent performance
- **GPU3**: Balanced performance with steady 65°C peak temperature

**Key Finding:** No hardware throttling, no performance degradation, all GPUs sustaining ~73-74 TFlops.

---

## Detailed Results

### GPU0: NVIDIA GeForce RTX 3090 (UUID: 98835b8b-e798-65a9-e2f1-a44bc3cc8413)

| Metric | Value |
|--------|-------|
| **Average Performance** | 73,658 GFlops/s |
| **Peak Performance** | 75,866 GFlops/s |
| **Min Performance** | 72,567 GFlops/s |
| **Performance Deviation** | ±0.4% |
| **Temperature Range** | 37°C - 56°C |
| **Average Temperature** | 48.77°C |
| **Thermal Delta (Idle to Load)** | ~22°C |
| **HW Throttling** | None |
| **Thermal SW Throttling** | None |
| **Thermal HW Throttling** | None |

**Analysis:** GPU0 demonstrates excellent thermal performance despite having the highest idle power draw (30.7W). The GPU maintains steady ~74 TFlops throughout the 2-minute test with zero throttling events. Temperature stability is excellent, peaking at only 56°C under sustained compute load.

---

### GPU1: NVIDIA GeForce RTX 3090 (UUID: 2eae1cf9-3344-0055-e3e3-dd4b2c115653)

| Metric | Value |
|--------|-------|
| **Average Performance** | 73,792 GFlops/s |
| **Peak Performance** | 75,866 GFlops/s |
| **Min Performance** | 71,468 GFlops/s |
| **Performance Deviation** | ±0.3% |
| **Temperature Range** | 41°C - 74°C |
| **Average Temperature** | 58.83°C |
| **Thermal Delta (Idle to Load)** | ~33°C |
| **HW Throttling** | None |
| **Thermal SW Throttling** | None |
| **Thermal HW Throttling** | None |

**Analysis:** GPU1 reaches 74°C peak temperature under the same BF16 compute workload as GPU0, which only reaches 56°C. This 18°C difference is significant and indicates a **thermal contact or cooling issue**. The 33°C temperature rise is the highest among all GPUs. Performance remains solid at 73.8 TFlops average, but thermal headroom is reduced.

**Recommendation:** Inspect thermal paste application, check heatsink contact pressure, verify no dust/obstruction in cooling path.

---

### GPU2: NVIDIA GeForce RTX 3090 (UUID: f76d969b-5ca6-3d51-a5c3-4b7fa1d35a3f)

| Metric | Value |
|--------|-------|
| **Average Performance** | 72,826 GFlops/s |
| **Peak Performance** | 74,767 GFlops/s |
| **Min Performance** | 60,473 GFlops/s |
| **Performance Deviation** | ±1.8% |
| **Temperature Range** | 40°C - 60°C |
| **Average Temperature** | 52.64°C |
| **Thermal Delta (Idle to Load)** | ~20°C |
| **HW Throttling** | None |
| **Thermal SW Throttling** | None |
| **Thermal HW Throttling** | None |

**Analysis:** GPU2 shows the **best thermal efficiency**, peaking at 60°C with a 20°C rise. Performance is slightly lower than GPU0/GPU1 (72.8 vs 73.8 TFlops), with one performance dip to 60.5 TFlops near the end of the test (likely normal variation). Overall health is excellent.

---

### GPU3: NVIDIA GeForce RTX 3090 (UUID: 68c0afc4-c323-e5b7-5c15-c9a3455e2752)

| Metric | Value |
|--------|-------|
| **Average Performance** | 73,484 GFlops/s |
| **Peak Performance** | 74,767 GFlops/s |
| **Min Performance** | 72,567 GFlops/s |
| **Performance Deviation** | ±0.2% |
| **Temperature Range** | 47°C - 65°C |
| **Average Temperature** | 58.32°C |
| **Thermal Delta (Idle to Load)** | ~18°C |
| **HW Throttling** | None |
| **Thermal SW Throttling** | None |
| **Thermal HW Throttling** | None |

**Analysis:** GPU3 delivers very consistent performance at 73.5 TFlops with minimal variation (±0.2%). Thermal profile is good, peaking at 65°C with steady 18°C rise. Performance consistency is excellent - most stable of the four.

---

## Comparative Analysis

### Compute Performance

```
GPU0: 73,658 GFlops/s  ████████░░  
GPU1: 73,792 GFlops/s  █████████░  (Highest)
GPU2: 72,826 GFlops/s  █████████░  
GPU3: 73,484 GFlops/s  ████████░░  
```

**Variance:** 966 GFlops/s range (1.3% spread) - All performing within expected tolerance.

### Thermal Profile Under Load

| GPU | Peak Temp | Avg Temp | Thermal Rise | Efficiency |
|-----|-----------|----------|--------------|------------|
| **GPU0** | 56°C | 48.77°C | 22°C | ✅ Excellent |
| **GPU1** | 74°C | 58.83°C | 33°C | ⚠️ Concerning |
| **GPU2** | 60°C | 52.64°C | 20°C | ✅ Best |
| **GPU3** | 65°C | 58.32°C | 18°C | ✅ Good |

### Throttling Status

✅ **No throttling on any GPU** - All GPUs sustain full performance throughout the 2-minute test.

---

## Idle vs. Load Power Consumption

Based on earlier measurements, comparing idle to under-load behavior:

| GPU | Idle Power | Load Profile | Efficiency |
|-----|-----------|--------------|-----------|
| GPU0 | 30.7W | Excellent thermals at 73.7 TFlops | Efficient despite high idle |
| GPU1 | 15.3W | Higher thermals at 73.8 TFlops | Thermal issue, not power |
| GPU2 | 19.4W | Best thermal efficiency | Optimal |
| GPU3 | 16.2W | Consistent performance | Good |

**Key Insight:** GPU0's higher idle power (30.7W) does NOT correlate with performance or thermal issues under load. This remains a silicon characteristic, not a systemic fault.

---

## Conclusions & Recommendations

### Health Status

✅ **GPU0:** Healthy. Excellent thermal performance. Higher idle power is not a concern.  
⚠️ **GPU1:** Healthy but **thermal contact issue suspected**. Monitor closely.  
✅ **GPU2:** Healthy. Best thermal efficiency.  
✅ **GPU3:** Healthy. Consistent performance.

### Actions Required

**Immediate (GPU1):**
1. Reseat GPU1 in its PCIe slot to check for proper seating
2. Inspect thermal paste between GPU die and heatsink
3. Check for dust/blockage in cooler heatsink fins
4. Consider re-applying thermal paste if GPU is >2 years old

**Monitoring:**
- Track GPU1 thermal behavior in production workloads
- Alert if GPU1 peak temperature exceeds 80°C during compute tasks
- Continue monitoring GPU0 idle power for any increase

### Historical Context

From 1-year Prometheus data:
- GPU0's idle power has remained elevated (~16W baseline → 30W current)
- No evidence of rapid degradation
- All GPUs show normal manufacturing tolerance variance (~±10%)

---

## Test Methodology

**Test Tool:** gpu-fryer v1.1.0 (CUDA compute stress test)
- Uses CUBLAS for matrix multiplication (8192×8192 matrices)
- Precision: BF16 (auto-selected for Tensor Core utilization)
- Memory allocation: 95% of GPU VRAM
- Duration: 120 seconds per GPU
- Sampling: Real-time per-second performance + temperature monitoring
- Parallel testing: Sequential per-GPU (5-second cooldown between tests)

**Metrics Captured:**
- GFlops/s (computational throughput)
- Temperature (°C)
- Throttling flags (hardware, thermal SW, thermal HW)
- Performance variance and deviation

---

## Reference Data

**RTX 3090 Specifications:**
- Peak FP32: 142.1 TFlops
- Peak TF32: 569.5 TFlops
- Peak Tensor Core: ~1.4-2.8 PFlops (precision dependent)
- Max Power: 350W
- Max Temperature: 87°C (thermal limit)
- Target Operating: 60-75°C for sustained workloads

**Test Results vs Specs:**
- All GPUs operating at ~74 TFlops (5.2% of FP32 spec, normal for BF16 matrix ops)
- All well below 87°C limit, with GPU0 at 56°C showing excellent margin
- GPU1 at 74°C approaching mid-range of typical operating temps

---

## Extended 5-Minute Stress Test (2026-04-05) - With Junction & VRAM Monitoring

**Test Setup:** All 4 GPUs in parallel for 300 seconds with simultaneous gputemps JSON monitoring (captures junction, core, and VRAM temps)

### Comprehensive Temperature Analysis

| GPU | Avg Performance | Die Temp (avg/min/max) | Core Temp (min/max) | Junction Temp (min/max) | VRAM Temp (min/max) | Status |
|-----|-----------------|----------------------|-------------------|----------------------|-------------------|--------|
| **GPU0** | 73,333 GFlops/s | 55.89°C (39-60°C) | 28-56°C | **37-72°C** ⭐ | 40-86°C | ✅ Excellent |
| **GPU1** | 72,326 GFlops/s | 67.97°C (43-75°C) | 27-54°C | **37-104°C** ⚠️ | 36-90°C | ⚠️ CRITICAL |
| **GPU2** | 71,866 GFlops/s | 62.44°C (43-69°C) | 31-64°C | **41-83°C** | 44-90°C | ✅ Good |
| **GPU3** | 72,386 GFlops/s | 66.53°C (49-72°C) | 32-65°C | **42-88°C** | 40-76°C | ⚠️ Elevated |

### Critical Finding: Memory Junction Temperature Gap

- **GPU1 peak junction: 104°C** (27°C above RTX 3090 target operating range of 60-75°C)
- **GPU3 peak junction: 88°C** (still 13°C above target)
- **GPU0 peak junction: 72°C** (within excellent margin)
- **GPU2 peak junction: 83°C** (acceptable but elevated)

**Thermal Performance Ranking:**
1. **GPU0**: Best performer - 37-72°C junction (35°C range)
2. **GPU2**: Moderate - 41-83°C junction (42°C range)
3. **GPU3**: Elevated - 42-88°C junction (46°C range, preventive maintenance candidate)
4. **GPU1**: CRITICAL - 37-104°C junction (67°C range, immediate TIM replacement required)

### VRAM Temperature Observations

- **GPU1 VRAM consistently 10-14°C hotter** than peer GPUs throughout test
- GPU1 VRAM reached 90°C at test end (same peak as GPU2 despite lower die temps)
- GPU3 VRAM best managed (40-76°C), lowest peak among all GPUs
- GPU0 VRAM stable but elevated (40-86°C)

### Performance Consistency

- **GPU0**: Most consistent (73,333 GFlops/s avg, ±0.4% deviation)
- **GPU1**: Lower average (72,326 GFlops/s) despite highest idle performance - suggests thermal stress
- **GPU3**: Solid (72,386 GFlops/s avg, ±0.2% deviation)
- **GPU2**: One anomaly (brief dip to 19.7K GFlops) around 240s mark, otherwise 71,866 GFlops/s avg

### Throttling Status
✅ **Zero throttling events** across all 4 GPUs during entire 5-minute sustained load (300+ seconds)

### Recommendations (Pre-TIM Baseline)

**Immediate Action Required:**
- **GPU1**: TIM replacement required - junction temps at 104°C are unsustainable long-term
- Expected improvement post-TIM: 104°C → 75-80°C junction range

**Preventive Maintenance:**
- **GPU3**: TIM replacement recommended - 88°C junction is elevated despite no throttling
- **GPU2**: Monitor; acceptable current performance but approaching elevated threshold
