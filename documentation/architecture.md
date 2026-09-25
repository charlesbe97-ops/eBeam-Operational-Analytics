# System Architecture

## Overview

The project follows an end-to-end operational analytics architecture designed to separate data processing, analytical preparation, and Business Intelligence.

```text
Raw Operational Records
          │
          ▼
┌──────────────────────────┐
│          Python          │
│                          │
│ • Data cleaning          │
│ • Transformation         │
│ • KPI calculations       │
│ • Data validation        │
│ • Operational audits     │
│ • Historical processing  │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│   Prepared Data Tables   │
│                          │
│ • Historical Process     │
│ • Historical Downtime    │
│ • Historical Beam ON     │
│ • Historical Master      │
│ • Historical Audits      │
│ • Monthly KPIs           │
│ • Service Times          │
│ • Pallets by Service     │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│         Power BI         │
│                          │
│ • Data model             │
│ • Relationships          │
│ • DAX measures           │
│ • Interactive filters    │
│ • KPI cards              │
│ • Trend analysis         │
│ • Pareto analysis        │
└────────────┬─────────────┘
             │
             ▼
      Operational Insights
