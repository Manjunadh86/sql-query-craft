"""
SQLite database setup with realistic e-commerce seed data.

Creates an in-memory database with departments, employees, products,
customers, orders, and order_items tables. All data is deterministic
for reproducible grading.
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional, Tuple

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    budget REAL NOT NULL,
    location TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id),
    salary REAL NOT NULL,
    hire_date TEXT NOT NULL,
    manager_id INTEGER REFERENCES employees(id),
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock_quantity INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    registration_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_date TEXT NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('completed','pending','shipped','cancelled'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL
);
"""

SCHEMA_DESCRIPTION = """DATABASE SCHEMA
===============

Table: departments
  - id          INTEGER PRIMARY KEY
  - name        TEXT NOT NULL
  - budget      REAL NOT NULL
  - location    TEXT NOT NULL

Table: employees
  - id              INTEGER PRIMARY KEY
  - first_name      TEXT NOT NULL
  - last_name       TEXT NOT NULL
  - email           TEXT UNIQUE NOT NULL
  - department_id   INTEGER NOT NULL (FK -> departments.id)
  - salary          REAL NOT NULL
  - hire_date       TEXT NOT NULL (format: YYYY-MM-DD)
  - manager_id      INTEGER (FK -> employees.id, NULL if top-level)
  - is_active       INTEGER NOT NULL (1=active, 0=inactive)

Table: products
  - id              INTEGER PRIMARY KEY
  - name            TEXT NOT NULL
  - category        TEXT NOT NULL (values: Electronics, Books, Clothing, Home, Sports)
  - price           REAL NOT NULL
  - stock_quantity  INTEGER NOT NULL
  - created_at      TEXT NOT NULL (format: YYYY-MM-DD)

Table: customers
  - id                  INTEGER PRIMARY KEY
  - first_name          TEXT NOT NULL
  - last_name           TEXT NOT NULL
  - email               TEXT UNIQUE NOT NULL
  - city                TEXT NOT NULL
  - country             TEXT NOT NULL
  - registration_date   TEXT NOT NULL (format: YYYY-MM-DD)

Table: orders
  - id              INTEGER PRIMARY KEY
  - customer_id     INTEGER NOT NULL (FK -> customers.id)
  - order_date      TEXT NOT NULL (format: YYYY-MM-DD)
  - total_amount    REAL NOT NULL
  - status          TEXT NOT NULL (values: completed, pending, shipped, cancelled)

Table: order_items
  - id          INTEGER PRIMARY KEY
  - order_id    INTEGER NOT NULL (FK -> orders.id)
  - product_id  INTEGER NOT NULL (FK -> products.id)
  - quantity    INTEGER NOT NULL
  - unit_price  REAL NOT NULL

RELATIONSHIPS
=============
- employees.department_id  -> departments.id
- employees.manager_id     -> employees.id (self-referencing)
- orders.customer_id       -> customers.id
- order_items.order_id     -> orders.id
- order_items.product_id   -> products.id
"""


def _seed_departments(cur: sqlite3.Cursor) -> None:
    cur.executemany(
        "INSERT INTO departments (id, name, budget, location) VALUES (?, ?, ?, ?)",
        [
            (1, "Engineering", 500000, "San Francisco"),
            (2, "Marketing", 300000, "New York"),
            (3, "Sales", 400000, "Chicago"),
            (4, "Human Resources", 200000, "San Francisco"),
            (5, "Finance", 350000, "New York"),
        ],
    )


def _seed_employees(cur: sqlite3.Cursor) -> None:
    cur.executemany(
        "INSERT INTO employees (id, first_name, last_name, email, department_id, salary, hire_date, manager_id, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "Alice", "Johnson", "alice.j@company.com", 1, 120000, "2020-03-15", None, 1),
            (2, "Bob", "Smith", "bob.s@company.com", 1, 95000, "2021-06-01", 1, 1),
            (3, "Charlie", "Brown", "charlie.b@company.com", 1, 85000, "2022-01-10", 1, 1),
            (4, "Diana", "Lee", "diana.l@company.com", 1, 70000, "2023-04-20", 2, 1),
            (5, "Eve", "Williams", "eve.w@company.com", 2, 90000, "2020-07-01", None, 1),
            (6, "Frank", "Davis", "frank.d@company.com", 2, 75000, "2021-09-15", 5, 1),
            (7, "Grace", "Wilson", "grace.w@company.com", 2, 65000, "2022-11-20", 5, 1),
            (8, "Henry", "Taylor", "henry.t@company.com", 2, 55000, "2023-08-01", 6, 0),
            (9, "Ivy", "Anderson", "ivy.a@company.com", 3, 88000, "2019-12-01", None, 1),
            (10, "Jack", "Thomas", "jack.t@company.com", 3, 82000, "2020-05-15", 9, 1),
            (11, "Karen", "Martinez", "karen.m@company.com", 3, 78000, "2021-03-01", 9, 1),
            (12, "Leo", "Garcia", "leo.g@company.com", 3, 60000, "2023-01-15", 10, 1),
            (13, "Mia", "Robinson", "mia.r@company.com", 4, 85000, "2020-02-01", None, 1),
            (14, "Noah", "Clark", "noah.c@company.com", 4, 62000, "2022-06-15", 13, 1),
            (15, "Olivia", "Lewis", "olivia.l@company.com", 4, 55000, "2023-09-01", 13, 1),
            (16, "Peter", "Walker", "peter.w@company.com", 5, 105000, "2019-08-01", None, 1),
            (17, "Quinn", "Hall", "quinn.h@company.com", 5, 92000, "2020-11-15", 16, 1),
            (18, "Rachel", "Allen", "rachel.a@company.com", 5, 78000, "2021-07-01", 16, 1),
            (19, "Sam", "Young", "sam.y@company.com", 5, 68000, "2022-12-01", 17, 1),
            (20, "Tina", "King", "tina.k@company.com", 5, 58000, "2023-11-01", 17, 0),
        ],
    )


def _seed_products(cur: sqlite3.Cursor) -> None:
    cur.executemany(
        "INSERT INTO products (id, name, category, price, stock_quantity, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "Laptop Pro", "Electronics", 999.99, 50, "2023-01-15"),
            (2, "Wireless Mouse", "Electronics", 29.99, 200, "2023-02-20"),
            (3, "USB-C Hub", "Electronics", 49.99, 150, "2023-03-10"),
            (4, "Python Mastery", "Books", 39.99, 100, "2023-04-05"),
            (5, "Data Science Handbook", "Books", 45.99, 80, "2023-05-15"),
            (6, "SQL Deep Dive", "Books", 34.99, 120, "2023-06-20"),
            (7, "Tech T-Shirt", "Clothing", 24.99, 300, "2023-07-01"),
            (8, "Hoodie Premium", "Clothing", 59.99, 100, "2023-08-15"),
            (9, "Cap Classic", "Clothing", 14.99, 500, "2023-09-01"),
            (10, "Desk Lamp LED", "Home", 34.99, 80, "2023-10-10"),
            (11, "Ergonomic Chair", "Home", 299.99, 30, "2023-11-05"),
            (12, "Standing Desk Mat", "Home", 49.99, 60, "2023-12-01"),
            (13, "Yoga Mat", "Sports", 29.99, 200, "2024-01-15"),
            (14, "Resistance Bands", "Sports", 19.99, 300, "2024-02-20"),
            (15, "Water Bottle", "Sports", 12.99, 500, "2024-03-10"),
        ],
    )


def _seed_customers(cur: sqlite3.Cursor) -> None:
    cur.executemany(
        "INSERT INTO customers (id, first_name, last_name, email, city, country, registration_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "John", "Doe", "john.d@email.com", "San Francisco", "USA", "2023-01-01"),
            (2, "Jane", "Smith", "jane.s@email.com", "New York", "USA", "2023-02-15"),
            (3, "Mike", "Johnson", "mike.j@email.com", "London", "UK", "2023-03-20"),
            (4, "Sarah", "Williams", "sarah.w@email.com", "Toronto", "Canada", "2023-04-10"),
            (5, "David", "Brown", "david.b@email.com", "Sydney", "Australia", "2023-05-25"),
            (6, "Emily", "Davis", "emily.d@email.com", "Berlin", "Germany", "2023-06-30"),
            (7, "Chris", "Wilson", "chris.w@email.com", "Tokyo", "Japan", "2023-07-15"),
            (8, "Lisa", "Taylor", "lisa.t@email.com", "Paris", "France", "2023-08-20"),
            (9, "Mark", "Anderson", "mark.a@email.com", "San Francisco", "USA", "2023-09-01"),
            (10, "Anna", "Thomas", "anna.t@email.com", "New York", "USA", "2023-10-15"),
            (11, "James", "Martinez", "james.m@email.com", "Chicago", "USA", "2023-11-20"),
            (12, "Kate", "Garcia", "kate.g@email.com", "Los Angeles", "USA", "2023-12-01"),
        ],
    )


def _seed_orders(cur: sqlite3.Cursor) -> None:
    cur.executemany(
        "INSERT INTO orders (id, customer_id, order_date, total_amount, status) VALUES (?, ?, ?, ?, ?)",
        [
            (1, 1, "2024-01-15", 1029.98, "completed"),
            (2, 2, "2024-01-20", 79.98, "completed"),
            (3, 3, "2024-02-05", 139.97, "completed"),
            (4, 1, "2024-02-15", 329.98, "completed"),
            (5, 4, "2024-02-28", 80.98, "completed"),
            (6, 5, "2024-03-10", 59.98, "shipped"),
            (7, 2, "2024-03-20", 1049.98, "completed"),
            (8, 6, "2024-04-01", 44.98, "completed"),
            (9, 1, "2024-04-15", 149.97, "completed"),
            (10, 7, "2024-04-25", 34.99, "cancelled"),
            (11, 3, "2024-05-05", 69.98, "completed"),
            (12, 8, "2024-05-15", 359.98, "completed"),
            (13, 2, "2024-05-25", 94.97, "completed"),
            (14, 9, "2024-06-05", 79.98, "completed"),
            (15, 4, "2024-06-15", 1049.98, "completed"),
            (16, 10, "2024-06-25", 49.98, "pending"),
            (17, 1, "2024-07-05", 59.97, "completed"),
            (18, 11, "2024-07-15", 299.99, "completed"),
            (19, 5, "2024-07-25", 24.99, "completed"),
            (20, 3, "2024-08-05", 999.99, "completed"),
            (21, 12, "2024-08-15", 74.97, "completed"),
            (22, 2, "2024-08-25", 49.99, "completed"),
            (23, 6, "2024-09-05", 29.99, "shipped"),
            (24, 9, "2024-09-15", 139.98, "completed"),
            (25, 4, "2024-09-25", 64.98, "completed"),
        ],
    )


def _seed_order_items(cur: sqlite3.Cursor) -> None:
    cur.executemany(
        "INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
        [
            # Order 1 (John): Laptop Pro + Wireless Mouse
            (1, 1, 1, 1, 999.99),
            (2, 1, 2, 1, 29.99),
            # Order 2 (Jane): 2x Python Mastery
            (3, 2, 4, 2, 39.99),
            # Order 3 (Mike): USB-C Hub + Hoodie + Yoga Mat
            (4, 3, 3, 1, 49.99),
            (5, 3, 8, 1, 59.99),
            (6, 3, 13, 1, 29.99),
            # Order 4 (John): Ergonomic Chair + Wireless Mouse
            (7, 4, 11, 1, 299.99),
            (8, 4, 2, 1, 29.99),
            # Order 5 (Sarah): Data Science Handbook + SQL Deep Dive
            (9, 5, 5, 1, 45.99),
            (10, 5, 6, 1, 34.99),
            # Order 6 (David): Hoodie + Water Bottle (shipped)
            (11, 6, 8, 1, 59.99),
            # Order 7 (Jane): Laptop Pro + USB-C Hub
            (12, 7, 1, 1, 999.99),
            (13, 7, 3, 1, 49.99),
            # Order 8 (Emily): SQL Deep Dive + Water Bottle
            (14, 8, 6, 1, 34.99),
            (15, 8, 15, 1, 9.99),
            # Order 9 (John): 3x USB-C Hub
            (16, 9, 3, 3, 49.99),
            # Order 10 (Chris): SQL Deep Dive (cancelled)
            (17, 10, 6, 1, 34.99),
            # Order 11 (Mike): 2x SQL Deep Dive
            (18, 11, 6, 2, 34.99),
            # Order 12 (Lisa): Ergonomic Chair + Hoodie
            (19, 12, 11, 1, 299.99),
            (20, 12, 8, 1, 59.99),
            # Order 13 (Jane): Tech T-Shirt + Yoga Mat + Resistance Bands
            (21, 13, 7, 1, 24.99),
            (22, 13, 13, 1, 29.99),
            (23, 13, 14, 2, 19.99),
            # Order 14 (Mark): 2x Python Mastery
            (24, 14, 4, 2, 39.99),
            # Order 15 (Sarah): Laptop Pro + USB-C Hub
            (25, 15, 1, 1, 999.99),
            (26, 15, 3, 1, 49.99),
            # Order 16 (Anna): Wireless Mouse + Resistance Bands (pending)
            (27, 16, 2, 1, 29.99),
            (28, 16, 14, 1, 19.99),
            # Order 17 (John): 3x Resistance Bands
            (29, 17, 14, 3, 19.99),
            # Order 18 (James): Ergonomic Chair
            (30, 18, 11, 1, 299.99),
            # Order 19 (David): Tech T-Shirt
            (31, 19, 7, 1, 24.99),
            # Order 20 (Mike): Laptop Pro
            (32, 20, 1, 1, 999.99),
            # Order 21 (Kate): Yoga Mat + Data Science Handbook
            (33, 21, 13, 1, 29.99),
            (34, 21, 5, 1, 44.98),
            # Order 22 (Jane): Standing Desk Mat
            (35, 22, 12, 1, 49.99),
            # Order 23 (Emily): Yoga Mat (shipped)
            (36, 23, 13, 1, 29.99),
            # Order 24 (Mark): USB-C Hub + Hoodie + Desk Lamp
            (37, 24, 3, 1, 49.99),
            (38, 24, 8, 1, 59.99),
            (39, 24, 10, 1, 29.99),
            # Order 25 (Sarah): Tech T-Shirt + Python Mastery
            (40, 25, 7, 1, 24.99),
            (41, 25, 4, 1, 39.99),
        ],
    )


def create_database() -> sqlite3.Connection:
    """Create a fresh in-memory SQLite database with all seed data."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    cur.executescript(SCHEMA_SQL)
    _seed_departments(cur)
    _seed_employees(cur)
    _seed_products(cur)
    _seed_customers(cur)
    _seed_orders(cur)
    _seed_order_items(cur)
    conn.commit()
    return conn


def execute_query(
    conn: sqlite3.Connection,
    query: str,
    max_rows: int = 100,
) -> Tuple[Optional[List[str]], Optional[List[Tuple]], Optional[str]]:
    """
    Execute a SQL query and return (columns, rows, error).

    Returns:
        (column_names, rows, None) on success
        (None, None, error_message) on failure
    """
    query = query.strip().rstrip(";")
    if not query:
        return None, None, "Empty query"

    upper = query.upper().strip()
    forbidden = ["DROP ", "TRUNCATE ", "ALTER ", "CREATE ", "INSERT ", "UPDATE ", "DELETE "]
    for kw in forbidden:
        if kw in upper and not upper.startswith("SELECT"):
            return None, None, f"Destructive or mutation query detected ({kw.strip()}). Only SELECT queries are allowed."

    try:
        cur = conn.cursor()
        cur.execute(query)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchmany(max_rows)
        return columns, rows, None
    except Exception as e:
        return None, None, str(e)


def format_query_result(
    columns: Optional[List[str]],
    rows: Optional[List[Tuple]],
    error: Optional[str],
    max_display: int = 20,
) -> str:
    """Format query result as a readable table string."""
    if error:
        return f"ERROR: {error}"
    if columns is None or rows is None:
        return "No results."

    if not rows:
        header = " | ".join(columns)
        return f"Columns: {header}\n(0 rows returned)"

    col_widths = [len(c) for c in columns]
    for row in rows[:max_display]:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))

    header = " | ".join(c.ljust(w) for c, w in zip(columns, col_widths))
    sep = "-+-".join("-" * w for w in col_widths)

    lines = [header, sep]
    for row in rows[:max_display]:
        line = " | ".join(str(v).ljust(w) for v, w in zip(row, col_widths))
        lines.append(line)

    if len(rows) > max_display:
        lines.append(f"... ({len(rows)} total rows, showing first {max_display})")

    lines.append(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")
    return "\n".join(lines)
