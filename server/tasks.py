"""
Task definitions for the SQL Query Craft environment.

Each task defines a natural-language question, expected SQL answer,
metadata for grading, and difficulty level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TaskDefinition:
    name: str
    difficulty: str
    question: str
    expected_query: str
    expected_columns: List[str]
    expected_tables: List[str]
    hints: str
    max_steps: int
    sql_features: List[str] = field(default_factory=list)


TASKS: Dict[str, TaskDefinition] = {}


def _register(task: TaskDefinition) -> None:
    TASKS[task.name] = task


# ── Task 1: Easy ────────────────────────────────────────────────────────────

_register(
    TaskDefinition(
        name="easy_employee_lookup",
        difficulty="easy",
        question=(
            "Find all active employees in the Engineering department who earn more "
            "than $75,000, sorted by salary in descending order. "
            "Return their first_name, last_name, and salary."
        ),
        expected_query="""
            SELECT e.first_name, e.last_name, e.salary
            FROM employees e
            JOIN departments d ON e.department_id = d.id
            WHERE d.name = 'Engineering'
              AND e.salary > 75000
              AND e.is_active = 1
            ORDER BY e.salary DESC
        """,
        expected_columns=["first_name", "last_name", "salary"],
        expected_tables=["employees", "departments"],
        hints=(
            "You need to JOIN employees with departments. "
            "Filter on department name, salary threshold, and active status. "
            "ORDER BY salary DESC."
        ),
        max_steps=5,
        sql_features=["JOIN", "WHERE", "ORDER BY"],
    )
)


# ── Task 2: Medium ──────────────────────────────────────────────────────────

_register(
    TaskDefinition(
        name="medium_sales_analysis",
        difficulty="medium",
        question=(
            "Calculate the total revenue and number of distinct orders for each "
            "product category, considering only orders with status 'completed'. "
            "Revenue for an item is quantity * unit_price. "
            "Only include categories with total revenue above $500. "
            "Sort by total revenue in descending order. "
            "Return columns: category, total_revenue, order_count."
        ),
        expected_query="""
            SELECT p.category,
                   SUM(oi.quantity * oi.unit_price) AS total_revenue,
                   COUNT(DISTINCT o.id) AS order_count
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status = 'completed'
            GROUP BY p.category
            HAVING total_revenue > 500
            ORDER BY total_revenue DESC
        """,
        expected_columns=["category", "total_revenue", "order_count"],
        expected_tables=["order_items", "products", "orders"],
        hints=(
            "Join order_items with products and orders. "
            "Filter for completed orders. "
            "GROUP BY category, use HAVING for the revenue threshold. "
            "Revenue per item = quantity * unit_price."
        ),
        max_steps=7,
        sql_features=["JOIN", "WHERE", "GROUP BY", "HAVING", "aggregate"],
    )
)


# ── Task 3: Hard ────────────────────────────────────────────────────────────

_register(
    TaskDefinition(
        name="hard_department_top_earner",
        difficulty="hard",
        question=(
            "For each department, find the employee with the highest salary "
            "(considering only active employees). Show: department_name, "
            "employee_name (as first_name || ' ' || last_name), their salary, "
            "the department's average salary (as avg_salary rounded to 2 decimals), "
            "and what percentage of the department's total salary this employee "
            "represents (as salary_pct rounded to 1 decimal). "
            "Sort by salary_pct descending."
        ),
        expected_query="""
            WITH dept_stats AS (
                SELECT department_id,
                       AVG(salary) AS avg_sal,
                       SUM(salary) AS total_sal
                FROM employees
                WHERE is_active = 1
                GROUP BY department_id
            ),
            ranked AS (
                SELECT e.first_name || ' ' || e.last_name AS employee_name,
                       d.name AS department_name,
                       e.salary,
                       ROUND(ds.avg_sal, 2) AS avg_salary,
                       ROUND(e.salary * 100.0 / ds.total_sal, 1) AS salary_pct,
                       ROW_NUMBER() OVER (PARTITION BY e.department_id ORDER BY e.salary DESC) AS rn
                FROM employees e
                JOIN departments d ON e.department_id = d.id
                JOIN dept_stats ds ON e.department_id = ds.department_id
                WHERE e.is_active = 1
            )
            SELECT department_name, employee_name, salary, avg_salary, salary_pct
            FROM ranked
            WHERE rn = 1
            ORDER BY salary_pct DESC
        """,
        expected_columns=["department_name", "employee_name", "salary", "avg_salary", "salary_pct"],
        expected_tables=["employees", "departments"],
        hints=(
            "Use CTEs or subqueries. Compute department-level aggregates "
            "(AVG and SUM salary) for active employees. Use ROW_NUMBER() "
            "window function to pick the top earner per department. "
            "Percentage = employee_salary * 100.0 / department_total_salary."
        ),
        max_steps=10,
        sql_features=["CTE", "window function", "JOIN", "subquery", "aggregate"],
    )
)


# ── Task 4: Hard ────────────────────────────────────────────────────────────

_register(
    TaskDefinition(
        name="hard_customer_spending",
        difficulty="hard",
        question=(
            "Find customers who have placed more than 2 completed orders. "
            "For these customers show: customer_name (first_name || ' ' || last_name), "
            "total_orders (count of completed orders), "
            "total_spent (sum of total_amount for completed orders, rounded to 2 decimals), "
            "avg_order_value (average total_amount for completed orders, rounded to 2 decimals), "
            "and spending_rank (RANK by total_spent descending). "
            "Sort by spending_rank ascending, then customer_name ascending."
        ),
        expected_query="""
            WITH customer_stats AS (
                SELECT c.first_name || ' ' || c.last_name AS customer_name,
                       COUNT(*) AS total_orders,
                       ROUND(SUM(o.total_amount), 2) AS total_spent,
                       ROUND(AVG(o.total_amount), 2) AS avg_order_value
                FROM customers c
                JOIN orders o ON c.id = o.customer_id
                WHERE o.status = 'completed'
                GROUP BY c.id, c.first_name, c.last_name
                HAVING COUNT(*) > 2
            )
            SELECT customer_name, total_orders, total_spent, avg_order_value,
                   RANK() OVER (ORDER BY total_spent DESC) AS spending_rank
            FROM customer_stats
            ORDER BY spending_rank ASC, customer_name ASC
        """,
        expected_columns=["customer_name", "total_orders", "total_spent", "avg_order_value", "spending_rank"],
        expected_tables=["customers", "orders"],
        hints=(
            "Join customers with orders, filter by status='completed'. "
            "GROUP BY customer and use HAVING COUNT(*) > 2. "
            "Compute SUM, AVG, COUNT aggregates. "
            "Use RANK() window function over total_spent descending."
        ),
        max_steps=10,
        sql_features=["CTE", "window function", "JOIN", "GROUP BY", "HAVING", "RANK"],
    )
)


def get_task(name: str) -> TaskDefinition:
    if name not in TASKS:
        available = ", ".join(sorted(TASKS.keys()))
        raise ValueError(f"Unknown task '{name}'. Available: {available}")
    return TASKS[name]


def list_tasks() -> List[str]:
    return sorted(TASKS.keys())
