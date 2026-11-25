# MTA Daily Ridership Analysis & Forecasting

**An End-to-End Data Analytics and Time Series Forecasting Project**

A comprehensive data project built around the MTA Daily Ridership dataset, progressing from data processing and relational database design to exploratory data analysis, business insights, and time series forecasting.

The project is structured into three stages, each building on the previous one to create a reproducible analytical workflow.

---

## Project Overview

The project analyzes daily activity across seven MTA transportation systems from March 2020 to October 2024.

It focuses on:
- Building a validated and structured data pipeline.
- Designing a relational database using a Star Schema.
- Exploring transportation performance and operational patterns.
- Investigating COVID-19 impact and recovery trends.
- Developing and evaluating time series forecasting models.
- Generating reproducible analytical reports and visualizations.

## Project Roadmap

| Stage | Focus | Key Deliverables |
|---|---|---|
| [Week One](./WEEK%20ONE/README.md) | Data Processing & Database Design | Cleaned dataset, dimensional tables, PostgreSQL database |
| [Week Two](./WEEK%20TWO/README.md) | Exploratory Data Analysis | 12 analytical questions, SQL analysis, KPIs, 12 visualizations |
| [Week Three](./WEEK%20THREE/README.md) | Time Series Forecasting | Forecasting models, backtesting, evaluation, forecasts, prediction intervals |

## Project Workflow

<pre>
Raw MTA Dataset
      |
      v
WEEK ONE
Data Processing & Validation
Star Schema & PostgreSQL
      |
      v
WEEK TWO
Exploratory Data Analysis
SQL Analytics & Visualizations
12 Analytical Questions
      |
      v
WEEK THREE
Time Series Forecasting
Model Evaluation & Backtesting
7-Day and 30-Day Horizons
      |
      v
Reports, Insights & Forecast Outputs
</pre>

## Transportation Systems

The project covers seven MTA transportation systems:

1. Subways
2. Buses
3. Long Island Rail Road (LIRR)
4. Metro-North Railroad
5. Access-A-Ride
6. Bridges and Tunnels
7. Staten Island Railway (SIR)

**Important:** These systems do not share a common measurement unit. Ridership, scheduled trips, and vehicle traffic must not be combined into a single raw activity total.

## Dataset Information

| Attribute | Description |
|---|---|
| Dataset | MTA Daily Ridership |
| Coverage | 2020-03-01 to 2024-10-31 |
| Daily observations | 1,706 |
| Transportation systems | 7 |
| Original dataset columns | 15 |
| Fact table records | 11,942 |

The original source values are preserved. The data pipeline focuses on validation, reshaping, and structuring rather than unnecessary value modification.

## Technologies & Tools

**Programming & Data Analysis**
- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn

**Database & SQL**
- PostgreSQL
- SQL
- Relational Database Design
- Star Schema

**Forecasting & Machine Learning**
- Scikit-learn
- Statsmodels
- SciPy
- Time Series Analysis
- Rolling-Origin Backtesting

**Development & Reporting**
- Jupyter Notebook
- Jupyter nbconvert
- Git & GitHub
- Markdown
- Pytest

## Repository Structure

```text
MTA_Daily_Ridership/
│
├── README.md
│
├── WEEK ONE/
│   ├── README.md
│   ├── data/
│   │   └── raw/
│   ├── database/
│   ├── python/
│   └── sql/
│
├── WEEK TWO/
│   ├── README.md
│   ├── python/
│   ├── sql/
│   ├── visualizations/
│   └── reports/
│
└── WEEK THREE/
    ├── README.md
    ├── python/
    ├── reports/
    ├── models/
    ├── forecasts/
    └── visualizations/
```

## Getting Started

### Prerequisites

- Python 3.13.5
- PostgreSQL 18
- Jupyter Notebook / JupyterLab
- Git

### Setup

Clone the repository:

```bash
git clone https://github.com/anasabouelazm/MTA_Daily_Ridership.git
cd MTA_Daily_Ridership
```

Install the required dependencies using the relevant requirements file, if provided.

Follow the individual README files for installation, execution, and validation instructions for each stage.

## Project Documentation

Each stage has its own documentation covering its objectives, methodology, implementation, execution instructions, and deliverables.

- [WEEK ONE — Data Processing & Database Design](./WEEK%20ONE/README.md)
- [WEEK TWO — Exploratory Data Analysis](./WEEK%20TWO/README.md)
- [WEEK THREE — Time Series Forecasting](./WEEK%20THREE/README.md)

---

**Project Domain:** Data Engineering | Data Analytics | SQL | Time Series Forecasting | Machine Learning

**Repository:** [MTA Daily Ridership](https://github.com/anasabouelazm/MTA_Daily_Ridership)