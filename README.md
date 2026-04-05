---
title: SQL Query Craft
emoji: 🗃️
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7069
tags:
  - openenv
---

# SQL Query Craft — OpenEnv Environment

A real-world **text-to-SQL** OpenEnv environment where AI agents learn to write SQL queries to answer business analytics questions against a realistic e-commerce database.

## Motivation

Writing SQL queries from natural language is one of the most common tasks in data analytics, business intelligence, and software engineering. Despite being a daily activity for millions of professionals, it remains challenging for AI agents — requiring understanding of database schemas, query semantics, aggregation logic, and complex join patterns.

**SQL Query Craft** bridges this gap by providing a standardized RL environment where agents can practice and be evaluated on progressively harder SQL tasks, from simple lookups to complex analytics involving CTEs, window functions, and multi-table joins.

## Environment Description

The agent receives:
- A **natural language question** about business data
- The complete **database schema** (6 tables, realistic e-commerce data)
- **Expected column names** for the answer
- **Hints** (available in early steps)
- **Feedback** from previous query attempts (results, errors, reward breakdowns)

The agent must respond with a SQL `SELECT` query. The environment executes it against an in-memory SQLite database and returns a reward based on query correctness.

## Action Space

| Field   | Type   | Description                        |
|---------|--------|------------------------------------|
| `query` | `str`  | A SQL SELECT query to execute      |

```python
from models import SQLAction
action = SQLAction(query="SELECT first_name, salary FROM employees WHERE salary > 80000")
```

## Observation Space

| Field                | Type            | Description                                                |
|----------------------|-----------------|------------------------------------------------------------|
| `question`           | `str`           | Natural language question to answer                        |
| `schema_description` | `str`           | Full database schema in human-readable format              |
| `query_result`       | `str`           | Formatted table of results from the last query             |
| `query_error`        | `str`           | Error message if the last query failed                     |
| `expected_columns`   | `List[str]`     | Column names the answer should contain                     |
| `hints`              | `str`           | Hints for solving the task (available in early steps)      |
| `task_name`          | `str`           | Current task identifier                                    |
| `difficulty`         | `str`           | Task difficulty: easy, medium, or hard                     |
| `step_number`        | `int`           | Current step number                                        |
| `max_steps`          | `int`           | Maximum steps allowed                                      |
| `reward_breakdown`   | `Dict[str,float]`| Detailed breakdown of how reward was computed             |
| `done`               | `bool`          | Whether the episode has ended                              |
| `reward`             | `float`         | Reward for the current step (0.0 – 1.0)                   |

## Reward Function

Rewards provide **rich partial-credit signals** (not just binary success/failure):

| Component           | Weight | Description                                        |
|---------------------|--------|----------------------------------------------------|
| Valid SQL           | 0.10   | Query parses and executes without errors           |
| Correct Tables      | 0.10   | Query references the right tables                  |
| Column Count        | 0.10   | Result has the expected number of columns          |
| Column Names        | 0.15   | Column names match expected names                  |
| Row Count           | 0.10   | Result has the expected number of rows             |
| Data Match          | 0.45   | Result values match the expected output            |
| **Total**           | **1.00**|                                                    |

- **Destructive penalty**: Queries containing DROP, DELETE, INSERT, etc. receive a -0.20 penalty.
- **Episode ends** when reward >= 0.95 (success) or step count reaches max_steps.
- The reward signals enable learning even when the agent's query is partially correct.

## Database Schema

A realistic e-commerce database with 6 tables:

- **departments** (5 rows) — id, name, budget, location
- **employees** (20 rows) — id, first_name, last_name, email, department_id, salary, hire_date, manager_id, is_active
- **products** (15 rows) — id, name, category, price, stock_quantity, created_at
- **customers** (12 rows) — id, first_name, last_name, email, city, country, registration_date
- **orders** (25 rows) — id, customer_id, order_date, total_amount, status
- **order_items** (41 rows) — id, order_id, product_id, quantity, unit_price

## Tasks

### 1. `easy_employee_lookup` (Easy)
**Question**: Find active Engineering employees earning > $75K, sorted by salary descending.
- **SQL Features**: JOIN, WHERE, ORDER BY
- **Max Steps**: 5
- **Expected Difficulty**: Straightforward for any SQL-capable model

### 2. `medium_sales_analysis` (Medium)
**Question**: Calculate total revenue and order count per product category for completed orders, filtered by revenue > $500.
- **SQL Features**: Multiple JOINs, GROUP BY, HAVING, aggregates
- **Max Steps**: 7
- **Expected Difficulty**: Requires understanding of aggregation and multi-table joins

### 3. `hard_department_top_earner` (Hard)
**Question**: For each department, find the highest-paid active employee and show their percentage of the department's total salary.
- **SQL Features**: CTEs, window functions (ROW_NUMBER), subqueries, JOINs
- **Max Steps**: 10
- **Expected Difficulty**: Challenges frontier models with complex analytics patterns

### 4. `hard_customer_spending` (Hard)
**Question**: Find high-frequency customers (>2 completed orders) with spending rankings.
- **SQL Features**: CTEs, RANK() window function, GROUP BY, HAVING, aggregates
- **Max Steps**: 10
- **Expected Difficulty**: Requires combining multiple advanced SQL concepts

## Setup & Usage

### Prerequisites

- Python 3.10+
- Docker
- `pip install openenv-core[core]>=0.2.2`

### Local Development

```bash
# Install dependencies
pip install -e .

# Start the server
uvicorn server.app:app --host 0.0.0.0 --port 7069

# In another terminal, run inference
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your-token-here"
python inference.py
```

### Docker

```bash
# Build
docker build -t sql-query-craft:latest .

# Run
docker run -p 7069:7069 sql-query-craft:latest

# Run inference against local container
export LOCAL_IMAGE_NAME=sql-query-craft:latest
python inference.py
```

### Validate

```bash
openenv validate
```

## Baseline Scores

| Task                       | Difficulty | Qwen2.5-72B-Instruct |
|----------------------------|------------|-----------------------|
| `easy_employee_lookup`     | Easy       | ~0.95                 |
| `medium_sales_analysis`    | Medium     | ~0.75                 |
| `hard_department_top_earner`| Hard      | ~0.55                 |
| `hard_customer_spending`   | Hard       | ~0.50                 |

*Scores are approximate and depend on inference temperature and max steps.*

## Project Structure

```
├── openenv.yaml          # OpenEnv environment manifest
├── models.py             # SQLAction, SQLObservation, SQLState (Pydantic)
├── client.py             # EnvClient for WebSocket communication
├── __init__.py           # Package exports
├── pyproject.toml        # Python dependencies
├── inference.py          # Baseline inference script
├── Dockerfile            # Container definition
├── README.md             # This file
└── server/
    ├── __init__.py
    ├── app.py            # FastAPI server (create_app)
    ├── sql_environment.py # Core Environment implementation
    ├── database.py       # SQLite database with seed data
    ├── tasks.py          # Task definitions (4 tasks)
    └── graders.py        # Reward computation with partial credit
```

## License

MIT
