# eBeam Operational Analytics

### Operational Performance Analytics & Business Intelligence Dashboard

An end-to-end analytics project focused on transforming industrial operational data into actionable performance insights using Python and Power BI.

---

## Project Overview

This project transforms operational records from an industrial irradiation process into a structured analytics workflow.

The solution combines Python-based data processing, KPI calculation, data-quality auditing, historical data preparation, and an interactive Power BI dashboard.

The project was developed to support operational performance monitoring, downtime analysis, production analysis, and data-quality assessment.

---

## Business Problem

Industrial operations generate large amounts of information through different operational records.

However, raw operational data is not immediately suitable for analysis. Data must be cleaned, transformed, validated, and structured before meaningful performance indicators can be calculated.

The main challenges addressed by this project were:

- Processing operational records from multiple sources.
- Standardizing data for analysis.
- Calculating operational performance indicators consistently.
- Identifying missing or incomplete operational records.
- Analyzing downtime and process interruptions.
- Preparing historical datasets for Business Intelligence.
- Providing an interactive view of operational performance.

---

## Solution

An end-to-end analytics workflow was developed using Python and Power BI.

The solution separates data preparation and analytical processing from visualization:

**Raw Operational Data → Python → Prepared Analytical Data → Power BI → Operational Insights**

Python is used for data cleaning, transformation, KPI calculations, validation, auditing, and preparation of historical datasets.

Power BI is used for data modeling, interactive analysis, visualization, and operational dashboards.

---

## Data Pipeline

The project follows a structured data pipeline that separates data processing from visualization.

```text
┌─────────────────────────┐
│   Raw Operational Data  │
│                         │
│ • Process records       │
│ • Downtime records      │
│ • Beam ON records       │
│ • Master log            │
│ • Time records          │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│         Python          │
│                         │
│ • Data cleaning         │
│ • Transformation        │
│ • KPI calculations      │
│ • Data validation       │
│ • Operational audits    │
│ • Historical processing │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Prepared Analytical     │
│ Data                    │
│                         │
│ • Historical datasets   │
│ • Monthly KPIs          │
│ • Service times         │
│ • Downtime data         │
│ • Audit results         │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│       Power BI          │
│                         │
│ • Data modeling         │
│ • DAX measures          │
│ • Interactive filters   │
│ • KPI visualization     │
│ • Pareto analysis       │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Operational Insights  │
│                         │
│ • Performance           │
│ • Downtime              │
│ • Production            │
│ • Data quality          │
└─────────────────────────┘
```

---

## Analytical Focus

The solution focuses on five main analytical areas:

- **Operational Performance** — Monitoring process efficiency and performance indicators.
- **Downtime Analysis** — Identifying and analyzing process interruptions and their impact.
- **Production Analysis** — Monitoring treated loads and operational activity.
- **Data Quality** — Detecting incomplete or missing operational records.
- **Historical Analysis** — Preparing structured datasets for monthly and historical comparison.
