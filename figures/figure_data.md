# Figure data (table view)

Every plotted value, so nothing is available only as colour or position.
Source: `results/benchmark.json` · gain 43.91 · threshold 0.85

## Figure 1 — hard stratum (58 episodes, 16 compound pairs)

| policy | accuracy | pair-clustered 95% CI | nominations |
|---|---|---|---|
| No assays spent | 8.6% | 0.0–24.1% | 5 |
| Three extracts at random | 8.6% | 0.0–24.1% | 5 |
| Strongest-looking first (current practice) | 19.0% | 6.9–34.4% | 11 |
| Adaptive contrast (this work) | 19.0% | 6.9–34.4% | 11 |

## Figure 2 — nomination rule (952 episodes, 238 pairs, adaptive_contrast, developable scoring)

| rule | coverage | precision | leads worth isolating | wasted / 100 |
|---|---|---|---|---|
| potency-only | 65.0% | 50.2% | 32.7% | 32.35 |
| selectivity-aware | 32.9% | 99.4% | 32.7% | 0.21 |

## Figure 3 — organ series (measured data, no simulation)

| species | organ | rotenoid share (CANOPUS) | T. cruzi inhibition |
|---|---|---|---|
| *Pachyrhizus erosus* | leaves | 21.91% | 112.2% |
| *Pachyrhizus erosus* | woody stems | 4.96% | 53.7% |
| *Pachyrhizus erosus* | roots | 0.20% | 0.0% |
| *Cnestis palala* | woody stems | 51.80% | 112.0% |
| *Cnestis palala* | roots | 49.61% | 112.1% |
| *Cnestis palala* | leaves | 0.37% | 0.0% |
