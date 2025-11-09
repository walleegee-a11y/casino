# Job Aggregation Rules for apr_inn_all

When aggregating multiple APR tasks into `apr_inn_all`, different keywords use different aggregation strategies:

## Aggregation Strategies

### 1. **SUM** (Total across all tasks)
- **Counts/Violations**: `error`, `warning`, `_num`, `count`, `nov`
  - Example: `place_inn.error=2 + route_inn.error=5 = apr_inn_all.error=7`
- **TNS (Total Negative Slack)**: Sum all slack violations
  - Example: `place.s_tns=-100 + route.s_tns=-50 = apr_inn_all.s_tns=-150`
- **Runtime**: `cpu_time`, `real_time`, `runtime`
  - Example: `place.cpu_time=100 + route.cpu_time=200 = apr_inn_all.cpu_time=300`

### 2. **MIN** (Worst case for timing)
- **WNS (Worst Negative Slack)**: Most negative = worst
  - Example: `place.s_wns=-0.5 + route.s_wns=-0.1 = apr_inn_all.s_wns=-0.5` (worst)

### 3. **MAX** (Worst case for congestion)
- **Congestion**: `overflow`, `hotspot`
  - Example: `place.overflow=5% + route.overflow=10% = apr_inn_all.overflow=10%` (worst)

### 4. **LAST** (Final stage value)
- **Area/Utilization**: `area`, `utilization`, `density`
  - Example: Use `chipfinish_inn.area` as final value (not sum)
  - Rationale: Area doesn't accumulate; final stage has authoritative value

### 5. **AVERAGE** (Mean across tasks)
- **Other metrics**: Default for unclassified keywords
  - Example: Custom metrics average across stages

## Example: apr_inn Aggregation

### Input Tasks:
```
place_inn:
  s_wns: -0.5 ns
  s_tns: -100 ns
  s_nov: 50
  error: 2
  cpu_time: 100s
  area: 1000 um²

route_inn:
  s_wns: -0.1 ns
  s_tns: -50 ns
  s_nov: 30
  error: 5
  cpu_time: 200s
  area: 1020 um²

chipfinish_inn:
  s_wns: -0.2 ns
  s_tns: -30 ns
  s_nov: 20
  error: 1
  cpu_time: 50s
  area: 1015 um²
```

### Aggregated Output (apr_inn_all):
```
s_wns: -0.5 ns       (MIN: worst case)
s_tns: -180 ns       (SUM: total slack)
s_nov: 100           (SUM: total violations)
error: 8             (SUM: total errors)
cpu_time: 350s       (SUM: total runtime)
area: 1015 um²       (LAST: final value from chipfinish)
```

## Why These Rules?

| Metric | Strategy | Reasoning |
|--------|----------|-----------|
| WNS | MIN | One critical path determines overall timing |
| TNS | SUM | All negative slack accumulates |
| Errors | SUM | Total error count across stages |
| Area | LAST | Final stage has authoritative value |
| Runtime | SUM | Total time spent |

## Customization

To change aggregation rules, modify `aggregate_tasks_to_job()` in `hawkeye_casino/gui/dashboard.py` around line 3380.

## Archive Strategy

**Do NOT archive aggregates** (pv_all, apr_inn_all). Instead:
1. ✅ Archive raw task data only
2. ✅ Compute aggregates on-demand in GUI
3. ✅ Web server computes aggregates via API

This keeps archive pure and allows rule changes without re-archiving.
