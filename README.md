<div align="center">
  <h1>🔍 Spectrum</h1>
  <h3>High-Performance Quantitative Trading Infrastructure</h3>
  
  [![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![TimescaleDB](https://img.shields.io/badge/TimescaleDB-PostgreSQL_17-black?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.timescale.com/)
  [![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
  [![Grafana](https://img.shields.io/badge/Grafana-Monitoring-F46800?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com)
  [![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

  <p>
    <b>Spectrum</b> is a modular, event-driven trading stack built for rigorous quantitative analysis and algorithmic execution.
    <br />
    Designed on clean architecture principles, it decouples the <b>Data/Infrastructure Layer</b> from the <b>Business Logic Layer</b>, ensuring scalability, maintainability, and high-throughput data processing.
  </p>
</div>

---

## 🏗️ Architecture

Spectrum leverages a containerized microservices architecture where **TimescaleDB** serves as the unified source of truth for both high-frequency time-series market data and transactional relational data (orders, portfolio state).

```mermaid
graph TD
    classDef infra fill:#f9f,stroke:#333,stroke-width:2px;
    classDef app fill:#bbf,stroke:#333,stroke-width:2px;

    subgraph Infrastructure
        TimescaleDB[("TimescaleDB (PostgreSQL 17)")]:::infra
        Grafana["Grafana Dashboards"]:::infra
    end

    subgraph Application "Prism"
        Ingester["Ingestion Service (Async)"]:::app
        Engine["Strategy Engine"]:::app
    end

    API["External APIs (Binance/Tiingo)"] -->|Raw Data Streams| Ingester
    Ingester -->|Batch Insert (Upsert)| TimescaleDB
    
    TimescaleDB -->|Historical Data| Engine
    TimescaleDB -->|System Metrics| Grafana
    
    Engine -->|Signals & Orders| TimescaleDB
    Engine -->|Execution| Broker["Broker API"]
```

## 🚀 Key Engineering Features

*   **Hybrid Storage Engine**: Exploits **TimescaleDB Hypertables** to achieve O(1) insert performance for massive time-series datasets while maintaining full SQL compliance for complex analytical queries.
*   **Resilient Ingestion Pipeline**: The `Prism` service implements intelligent backfilling mechanisms that automatically detect data gaps and resume ingestion, ensuring data continuity without manual intervention.
*   **Optimized Database Schema**: A meticulously designed schema with 7 core tables (`assets`, `market`, `models`, `signals`, `risk`, `orders`, `fills`), fully indexed and partitioned by time intervals.
*   **Clean Code & Modularity**: Application logic (Prism) is strictly separated from infrastructure orchestration. Dependencies are managed via **Conda** to ensure reproducible research environments.
*   **Observability First**: Native integration with **Grafana** provides real-time visualization of market data lag, system health, and trading performance.

## 🛠️ Technology Stack

| Domain | Tech Stack | Evaluation |
| :--- | :--- | :--- |
| **Business Logic** | **Python 3.11+** | Selected for its rich ecosystem in Data Science (Pandas, NumPy) and modern AsyncIO capabilities. |
| **Database** | **TimescaleDB** | Chosen over QuestDB/InfluxDB for its ability to handle relational data (users, portfolios) alongside metric data in a single ACID-compliant system. |
| **Interface** | **Psycopg2** | Industry-standard PostgreSQL adapter optimized for high-throughput batch insertions. |
| **Orchestration** | **Docker Compose** | Simplifies deployment into isolated, reproducible environments (Infrastructure vs Application). |
| **Visualization** | **Grafana** | Provides zero-code, highly customizable dashboards connected directly to the DB. |

## 📂 Project Structure

```bash
spectrum/
├── platform/           # Infrastructure Layer
│   ├── docker-compose.yml
│   ├── timescaledb/    # DB Initialization & Schema Definition
│   │   └── init/schema.sql  # Hypertable Definitions
│   └── grafana/        # Dashboard Provisioning
├── prism/              # Application Layer (Business Logic)
│   ├── docker-compose.yml
│   ├── environment.yml # Conda Environment Lockfile
│   ├── engine/         # Quantitative Strategy Runner
│   ├── ingestion/      # Multi-source Data Ingestors
│   ├── storage/        # Database Abstraction Layer
│   └── utils/          # Configuration & Logging
└── notebooks/          # Research & Backtesting Sandboxes
```

## ⚡ Quick Start

### Prerequisites
*   Docker Desktop & Docker Compose
*   Git

### Deployment

**1. Infrastructure Layer** (Database & Monitoring)
```bash
cd platform
docker-compose up -d
# Services: TimescaleDB (5432), Grafana (3000)
```

**2. Application Layer** (Prism Service)
```bash
cd ../prism
docker-compose build
docker-compose up -d
```

### Verification
Access the running database container to verify data ingestion:
```bash
docker exec -it spectrum-timescaledb psql -U postgres -d spectrum -c "SELECT ticker, count(*) FROM market GROUP BY ticker;"
```

## � Contact
**Ivan Galindo Angulo**  
[GitHub Profile](https://github.com/ivangalindoangulo)  

---
*Open Source project released under the [MIT License](LICENSE).*
