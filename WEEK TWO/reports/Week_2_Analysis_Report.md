# Week 2 Analysis Report — MTA Daily Ridership

## Executive Summary

The Week 2 analysis uses the validated Week 1 cleaned dataset: 1,706 consecutive days from 2020-03-01 to 2024-10-31, seven transportation systems, and 11,942 date x system observations. Data-quality checks found zero missing values, zero duplicate rows or dates, zero negative values, and no calendar gaps. The 32 Staten Island Railway (SIR) zero-activity days were retained, and recovery values above 100 were retained and investigated.

Because the seven systems use different units, cross-system comparisons use the published recovery percentage, within-system indices, ratios and correlations. Raw activity is never summed across systems.

Key findings:

- In the last 12 months (2023-11-01 to 2024-10-31), mean recovery was highest for Access-A-Ride (117.5%) and Bridges and Tunnels (101.1%), and lowest for SIR (50.9%) and Buses (59.9%).
- During March-April 2020, mean recovery ranged from 25.0% (LIRR) to 52.6% (Bridges and Tunnels); the lowest single-day recoveries were 1% for Buses and 2% for LIRR.
- Only Access-A-Ride (2023-05-07) and Bridges and Tunnels (2021-12-04) met the conservative sustained-recovery definition (7-day mean >= 100 for 14 consecutive days).
- Day-to-day activity volatility was highest for SIR (0.514 of its own mean) and lowest for Bridges and Tunnels (0.088).
- A one-day recovery jump on 2023-11-10 appears in all seven systems without a matching activity jump, pointing to a comparison-baseline issue rather than a demand surge.
- The February 2023 methodology update affected pre-pandemic comparison percentages, not activity estimates; recovery trends around that date require caution.

## Key KPIs

| System | Unit | Mean daily activity | Last-12m recovery | First-to-last 12m change | Daily-change volatility | Days >100 | Sustained >=100 |
|---|---|---:|---:|---:|---:|---:|---|
| Subways | estimated riders | 2,509,055 | 71.3% | +162.0% | 0.267 | 8 | Not reached |
| Buses | estimated riders | 1,006,868 | 59.9% | +106.0% | 0.301 | 4 | Not reached |
| LIRR | estimated riders | 135,960 | 87.5% | +249.6% | 0.348 | 142 | Not reached |
| Metro-North | estimated riders | 114,888 | 78.0% | +383.5% | 0.340 | 20 | Not reached |
| Access-A-Ride | scheduled trips | 21,942 | 117.5% | +101.2% | 0.260 | 496 | 2023-05-07 |
| Bridges and Tunnels | vehicles | 855,603 | 101.1% | +37.1% | 0.088 | 556 | 2021-12-04 |
| Staten Island Railway | estimated riders | 4,429 | 50.9% | +140.7% | 0.514 | 19 | Not reached |

Definitions:

- **Recovery** = the source `% of Comparable Pre-Pandemic Day`; 100 means the activity matched the comparable 2019 month/day-type day.
- **First-to-last 12m change** = last-12-month mean activity versus first-12-month mean activity (2020-03 to 2021-02). The first window is COVID-affected, so this is a recovery gap, not a normal growth rate.
- **Daily-change volatility** = standard deviation of daily activity changes divided by that system's own mean (unit-free).
- **Sustained >=100** = first date with a 7-day rolling mean recovery of at least 100 for 14 consecutive days.

## Answers to the 12 Analytical Questions

### A. Transportation System Performance

**Q1. How does ridership performance differ across systems?**  
Relevant columns: `recovery_percentage`; `activity_value` kept per system. Method: rank systems by last-12-month mean recovery. Last-12-month recovery was Access-A-Ride 117.5%, Bridges and Tunnels 101.1%, LIRR 87.5%, Metro-North 78.0%, Subways 71.3%, Buses 59.9%, and SIR 50.9%. Because this measure is relative to each system's own 2019 comparable day, it is comparable across systems even though activity units are not. Interpretation: two systems have closed or passed their comparison gap, while subway, bus and SIR activity remains materially below it.

**Q2. Which systems have the highest and lowest relative changes?**  
Relevant columns: `date_key`, `activity_value`. Method: percent change from the first 12 available months to the last 12 months, within each system. Highest: Metro-North +383.5% and LIRR +249.6%. Lowest: Bridges and Tunnels +37.1%, Access-A-Ride +101.2% and Buses +106.0%. Interpretation: the largest changes are in modes with the deepest early-pandemic depressions; the comparison is not a normal-year growth measure.

**Q3. Which systems show the greatest day-to-day volatility?**  
Relevant columns: `activity_value`. Method: standard deviation of daily changes divided by each system's mean, with coefficient of variation as a cross-check. Highest: SIR 0.514 (CV 0.61), LIRR 0.348 (CV 0.52), Metro-North 0.340 (CV 0.58). Lowest: Bridges and Tunnels 0.088 (CV 0.17). Interpretation: SIR and commuter rail show much larger day-to-day swings relative to their own scale; Bridges and Tunnels is the most stable series.

Charts: `02_system_performance.png`, `08_recovery_distribution.png`.

### B. Time-Based Analysis

**Q4. How does daily ridership change over time for each system?**  
Relevant columns: `date_key`, `activity_value`. Method: 7-day rolling mean per system. All systems show a very low 2020 trough and a much higher 2024 level. Monthly means illustrate the range: Subways 391,016 (2020-04) to 3,658,850 (2024-10); Buses 13,249 (2020-05) to 1,294,158 (2024-10); LIRR 7,244 (2020-04) to 229,105 (2024-10); Metro-North 8,145 (2020-04) to 204,956 (2024-10); Access-A-Ride 6,062 (2020-04) to 33,769 (2024-10); Bridges and Tunnels 330,540 (2020-04) to 982,010 (2024-06); SIR 656 (2020-04) to 6,715 (2024-10). Interpretation: the shape is a deep shock followed by a partial-to-full recovery, not a uniform linear trend.

**Q5. What are the monthly trends and which months are consistently higher or lower?**  
Relevant columns: `date_key`, `activity_value`. Method: monthly means plus an activity index within each year (100 = that year's mean). Highest indexed months: Metro-North March 134, SIR March 131, Buses October 129, Subways October 118, LIRR November 121, Bridges and Tunnels August 108. Lowest: Metro-North January 68, LIRR January 72, Buses July 78, Subways January 80, SIR April 80. Interpretation: autumn and March are generally strong for transit modes; Bridges and Tunnels has a weaker seasonal swing and peaks in summer.

**Q6. Are there weekday/weekend differences?**  
Relevant columns: `dim_date.day_name`, `activity_value`. Method: mean activity by day type and weekend/weekday ratio within each system. Ratios: Bridges and Tunnels 0.93; Subways and Access-A-Ride 0.59; Buses 0.56; Metro-North 0.53; LIRR 0.49; SIR 0.27. SIR's weekend mean is strongly depressed by its 32 zero-activity weekend days, which were retained. Interpretation: rail and subway systems have a pronounced weekday commuting pattern; vehicle traffic is much less day-type dependent.

**Q7. What seasonal patterns or unusual peaks and drops occur?**  
Relevant columns: `date_key`, `activity_value`, `recovery_pct`. Method: month-of-year index, ranked daily extremes and event-date review. The early March 2020 values were high before the shutdown, followed by extreme lows in April-May 2020: for example Buses 5,498 riders on 2020-04-26 (0.5% of its mean, 1% recovery) and Subways 198,399 on 2020-04-12 (7.9% of its mean, 8% recovery). Bridges and Tunnels had an unusual low of 156,759 vehicles on 2021-02-01 (18.3% of its mean, 18% recovery). On 2023-11-10 recovery jumped in every system without an activity jump. Interpretation: recurring seasonality is clear, but several extreme days require separate investigation.

Charts: `03_daily_activity_trends.png`, `04_monthly_recovery_trends.png`, `05_month_of_year_heatmap.png`, `06_weekday_weekend_ratio.png`.

### C. COVID-19 Impact and Recovery

**Q8. How significantly did COVID-19 affect ridership across systems?**  
Relevant columns: `recovery_percentage`, `activity_value`, `date_key`. Method: March-April 2020 mean and minimum recovery. Mean recovery was LIRR 25.0%, SIR 27.2%, Buses 27.6%, Metro-North 27.8%, Subways 29.7%, Access-A-Ride 46.2%, Bridges and Tunnels 52.6%. Minimum recovery in that window was 1% for Buses, 2% for LIRR, 3% for Metro-North, 7% for Subways, 13% for Access-A-Ride, 24% for Bridges and Tunnels and 4% for SIR. Interpretation: the shock was severe across all systems, deepest in bus and commuter-rail modes. Limitation: the dataset has no pre-2020 activity, so impact is measured through the published recovery percentage.

**Q9. How did each system recover relative to its baseline?**  
Relevant columns: `recovery_percentage`. Method: distribution, last-12-month mean, and counts of days above 100. Last-12-month means are shown in the KPI table. Days above 100: Bridges and Tunnels 556, Access-A-Ride 496, LIRR 142, Metro-North 20, SIR 19, Subways 8, Buses 4. Maximum recovery was LIRR 237%, Metro-North 193%, SIR 182%, Access-A-Ride 144%, Subways 143%, Buses 126% and Bridges and Tunnels 120%. Interpretation: Access-A-Ride and Bridges and Tunnels have spent substantial time above their comparison baseline; for LIRR/Metro-North the source notes that ridership is model-estimated, so high percentages should be treated as modelled estimates. The shared maximum date of 2023-11-10 for five systems is investigated in Q12.

**Q10. When did each system reach or exceed its baseline?**  
Relevant columns: `recovery_percentage`, `date_key`. Method: first date with a 7-day rolling mean >= 100 sustained for 14 consecutive days. Bridges and Tunnels reached this on 2021-12-04 (first 7-day crossing 2021-10-08); Access-A-Ride on 2023-05-07. LIRR first crossed on a 7-day basis on 2023-06-19 but did not sustain it for 14 days. No sustained crossing was observed for Subways, Buses, Metro-North or SIR; their longest daily streaks at or above 100 were 1, 1, 2 and 4 days respectively. Interpretation: baseline recovery was not uniform, and isolated high days should not be reported as full recovery.

Charts: `07_covid_impact.png`, `08_recovery_distribution.png`, `09_recovery_paths.png`.

### D. Relationships and Operational Insights

**Q11. Which systems show similar movement patterns?**  
Relevant columns: `activity_value` per system. Method: Pearson correlation of 7-day activity divided by each system's own mean. Strongest pairs: LIRR-Metro-North 0.98, Subways-LIRR 0.96, Subways-SIR 0.96, LIRR-Access-A-Ride 0.94. Bridges and Tunnels is the least correlated with other systems (0.73 with Metro-North, its lowest pair). Interpretation: commuter rail and subway/SIR series move closely together after smoothing; vehicle traffic follows a different pattern. Correlation is not causation.

**Q12. What unusual patterns or operational signals deserve follow-up?**  
Relevant columns: `activity_value`, `recovery_pct`, `date_key`. Signals: (1) 32 SIR zero-activity days, all weekends (3 in 2020, 29 in 2021), with recovery also 0; (2) 2023-11-10 recovery jumps in all seven systems (Subways 143%, Buses 126%, LIRR 237%, Metro-North 193%, Access-A-Ride 135%, Bridges and Tunnels 118%, SIR 182%) while activity stayed close to neighbouring days; (3) the February 2023 methodology update affects the comparison percentages; (4) extreme lows in April-May 2020 and the 2021-02-01 Bridges and Tunnels low. Interpretation: the 2023-11-10 pattern is more consistent with a baseline/denominator issue than a demand event, but the dataset cannot confirm the cause.

Charts: `10_correlation_heatmap.png`, `11_recovery_anomaly_2023_11_10.png`, `12_sir_zero_activity.png`.

## Important Visual Findings

- `01_activity_distributions.png` — each system's activity distribution has its own scale; no incompatible units are shared.
- `02_system_performance.png` — relative change and volatility rankings are unit-free and easy to compare.
- `03_daily_activity_trends.png` — all systems share the deep 2020 trough and uneven recovery.
- `04_monthly_recovery_trends.png` — the 100% baseline and February 2023 methodology marker make recovery gaps visible.
- `05_month_of_year_heatmap.png` — autumn/March strength and January/February weakness for most transit modes.
- `06_weekday_weekend_ratio.png` — vehicle traffic is least day-type dependent; SIR most.
- `07_covid_impact.png` — March-April 2020 recovery and minimum recovery by system.
- `08_recovery_distribution.png` — full recovery-percentage distributions, including values above 100.
- `09_recovery_paths.png` — sustained crossings are rare; only two systems meet the conservative rule.
- `10_correlation_heatmap.png` — commuter rail/subway/SIR co-movement versus Bridges and Tunnels.
- `11_recovery_anomaly_2023_11_10.png` — one-day recovery jump across all systems.
- `12_sir_zero_activity.png` — SIR zeros concentrated in 2021 weekends.

## Business Insights

### Observed facts

- Access-A-Ride (117.5%) and Bridges and Tunnels (101.1%) averaged at or above their 2019 comparison baseline in the last 12 months; SIR (50.9%) and Buses (59.9%) remained far below it.
- Metro-North (+383.5%) and LIRR (+249.6%) had the largest first-to-last 12-month activity changes; Bridges and Tunnels the smallest (+37.1%).
- SIR had the highest day-to-day volatility (0.514) and 32 zero-activity weekend days; Bridges and Tunnels the lowest volatility (0.088).
- Only Bridges and Tunnels and Access-A-Ride achieved sustained baseline recovery under the stated rule.
- On 2023-11-10 recovery jumped sharply in every system while activity did not.

### Analytical interpretations

- The largest activity changes coincide with the deepest early-pandemic lows; they reflect recovery from a depressed base, not ordinary growth.
- High recovery above 100 is plausible for Access-A-Ride scheduled trips and preliminary Bridges and Tunnels traffic, but the source does not provide a causal explanation and the 2023-11-10 spike suggests at least one baseline artefact.
- Strong correlations indicate shared weekly/seasonal structure across subway, commuter rail, Access-A-Ride and SIR; they do not prove one system causes another's changes.

### Recommendations

1. Validate the 2019 comparison denominator for 2023-11-10 before using that date in KPI reporting.
2. Work with the SIR operator to classify the 32 zero weekends as service outages or reporting gaps; keep the zeros in the dataset.
3. Label pre- and post-February-2023 recovery values as methodologically distinct in dashboards, and document that the comparison baseline was refreshed.
4. Report system KPIs by unit family; use recovery percentage or indices for cross-system comparisons.
5. Investigate the 2021-02-01 Bridges and Tunnels low and the April-May 2020 extremes against operational records before attributing causes.

### Limitations

- No direct pre-2020 activity values exist; COVID impact is inferred from the published recovery percentage.
- Activity measures are not uniform: Access-A-Ride counts scheduled trips, Bridges and Tunnels counts preliminary vehicles, and LIRR/Metro-North are model estimates.
- The February 2023 methodology update concerned pre-COVID comparison percentages; the dataset version history is not available to quantify its exact effect.
- Recent days may be revised by the source, and no service, fare, weather or event variables are available to support causal claims.
- Correlation is association only.

## Conclusions

Week 2 shows a common pandemic shock followed by clearly different recovery paths. Cross-system conclusions are valid only when expressed in unit-free terms. Access-A-Ride and Bridges and Tunnels have reached their comparison baseline, while subway, bus and SIR activity remains below it. SIR is both the most volatile and the only system with retained zero-activity days. Two data-quality follow-ups — the 2023-11-10 recovery spike and the SIR zero weekends — should precede any operational decisions. All figures in this report are reproducible from the Week 1 cleaned CSV via `WEEK TWO/python/MTA_Exploratory_Data_Analysis.ipynb` and the four SQL files in `WEEK TWO/sql/`.
