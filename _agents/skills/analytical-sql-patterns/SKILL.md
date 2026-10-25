---
skill_name: analytical-sql-patterns
description: Master analytical SQL with window functions, CTEs, ROLLUP, CUBE, GROUPING SETS, and lateral joins
category: Database & Data
version: 1.0.0
---

# Analytical SQL Patterns

Analytical SQL enables complex data analysis without requiring application code.

## Window Functions

```sql
-- Basic window function
SELECT
  order_id,
  customer_id,
  amount,
  SUM(amount) OVER (PARTITION BY customer_id) as customer_total,
  SUM(amount) OVER () as grand_total
FROM orders;

-- Window with ORDER BY (running totals)
SELECT
  order_id,
  customer_id,
  amount,
  SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date
  ) as running_total
FROM orders;

-- ROW_NUMBER, RANK, DENSE_RANK
SELECT
  product_id,
  sales,
  ROW_NUMBER() OVER (ORDER BY sales DESC) as rn,
  RANK() OVER (ORDER BY sales DESC) as rank,
  DENSE_RANK() OVER (ORDER BY sales DESC) as dense_rank
FROM products;

-- LAG and LEAD (previous/next values)
SELECT
  order_date,
  amount,
  LAG(amount) OVER (ORDER BY order_date) as previous_amount,
  LEAD(amount) OVER (ORDER BY order_date) as next_amount,
  amount - LAG(amount) OVER (ORDER BY order_date) as change
FROM orders;

-- FIRST_VALUE and LAST_VALUE
SELECT
  customer_id,
  order_date,
  amount,
  FIRST_VALUE(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date
  ) as first_order_amount,
  LAST_VALUE(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) as last_order_amount
FROM orders;

-- NTILE (percentile bucketing)
SELECT
  product_id,
  sales,
  NTILE(4) OVER (ORDER BY sales DESC) as quartile
FROM products;
```

## Common Table Expressions (CTEs)

```sql
-- Simple CTE
WITH customer_totals AS (
  SELECT
    customer_id,
    COUNT(*) as order_count,
    SUM(amount) as total_spent
  FROM orders
  GROUP BY customer_id
)
SELECT
  customer_id,
  order_count,
  total_spent
FROM customer_totals
WHERE total_spent > 1000;

-- Recursive CTE (hierarchies)
WITH RECURSIVE category_hierarchy AS (
  -- Base case: top-level categories
  SELECT
    id,
    parent_id,
    name,
    1 as level
  FROM categories
  WHERE parent_id IS NULL

  UNION ALL

  -- Recursive case: subcategories
  SELECT
    c.id,
    c.parent_id,
    c.name,
    ch.level + 1
  FROM categories c
  JOIN category_hierarchy ch ON c.parent_id = ch.id
)
SELECT * FROM category_hierarchy;

-- Multiple CTEs
WITH monthly_sales AS (
  SELECT
    DATE_TRUNC('month', order_date)::DATE as month,
    SUM(amount) as sales
  FROM orders
  GROUP BY DATE_TRUNC('month', order_date)
),
sales_growth AS (
  SELECT
    month,
    sales,
    LAG(sales) OVER (ORDER BY month) as previous_month_sales,
    ROUND((sales - LAG(sales) OVER (ORDER BY month)) /
          LAG(sales) OVER (ORDER BY month) * 100, 2) as growth_percent
  FROM monthly_sales
)
SELECT * FROM sales_growth;
```

## ROLLUP and CUBE

```sql
-- ROLLUP: Hierarchical aggregates
SELECT
  year,
  quarter,
  region,
  SUM(sales) as total_sales
FROM sales
GROUP BY ROLLUP (year, quarter, region);

-- Result includes:
-- (year, quarter, region, sales)
-- (year, quarter, NULL, sales)
-- (year, NULL, NULL, sales)
-- (NULL, NULL, NULL, sales)

-- CUBE: All combinations of aggregates
SELECT
  year,
  quarter,
  region,
  SUM(sales) as total_sales
FROM sales
GROUP BY CUBE (year, quarter, region);

-- Result includes all 2^3 = 8 combinations

-- GROUPING SETS: Explicit aggregation combinations
SELECT
  year,
  quarter,
  region,
  SUM(sales) as total_sales
FROM sales
GROUP BY GROUPING SETS (
  (year, quarter, region),
  (year, quarter),
  (year, region),
  (year),
  ()
);

-- Distinguish NULL from aggregated
SELECT
  year,
  quarter,
  region,
  SUM(sales) as total_sales,
  GROUPING(year) as year_is_aggregated,
  GROUPING(quarter) as quarter_is_aggregated,
  GROUPING(region) as region_is_aggregated
FROM sales
GROUP BY ROLLUP (year, quarter, region);
```

## LATERAL Joins

```sql
-- LATERAL: Allows reference to left-side table in subquery
SELECT
  customer_id,
  (latest_order).order_date,
  (latest_order).amount
FROM customers,
LATERAL (
  SELECT id, order_date, amount
  FROM orders
  WHERE customer_id = customers.id
  ORDER BY order_date DESC
  LIMIT 1
) as latest_order;

-- Top N per group using LATERAL
SELECT
  customer_id,
  order_ids
FROM (
  SELECT
    customer_id,
    ARRAY_AGG(id) as order_ids
  FROM (
    SELECT
      customer_id,
      id,
      ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC) as rn
    FROM orders
  ) t
  WHERE rn <= 5
  GROUP BY customer_id
) sub;

-- Alternative with LATERAL
SELECT
  c.customer_id,
  t.top_orders
FROM customers c,
LATERAL (
  SELECT
    ARRAY_AGG(id ORDER BY amount DESC) as top_orders
  FROM orders
  WHERE customer_id = c.customer_id
  LIMIT 5
) t;
```

## Complex Analytical Queries

```sql
-- Customer lifetime value with cohort analysis
WITH customer_cohorts AS (
  SELECT
    customer_id,
    DATE_TRUNC('month', MIN(order_date))::DATE as cohort_month,
    SUM(amount) as lifetime_value,
    COUNT(*) as total_orders,
    MAX(order_date) as last_order_date
  FROM orders
  GROUP BY customer_id
),
cohort_metrics AS (
  SELECT
    cohort_month,
    COUNT(DISTINCT customer_id) as customers,
    SUM(lifetime_value) as total_value,
    AVG(lifetime_value) as avg_ltv,
    AVG(total_orders) as avg_orders,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lifetime_value) as median_ltv
  FROM customer_cohorts
  GROUP BY cohort_month
)
SELECT * FROM cohort_metrics;

-- Moving averages
SELECT
  order_date,
  amount,
  AVG(amount) OVER (
    ORDER BY order_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as moving_avg_7days,
  AVG(amount) OVER (
    ORDER BY order_date
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as moving_avg_30days
FROM daily_orders;

-- Cumulative percentages
SELECT
  product_id,
  sales,
  SUM(sales) OVER (ORDER BY sales DESC) as cumulative_sales,
  ROUND(SUM(sales) OVER (ORDER BY sales DESC) * 100.0 /
        SUM(sales) OVER (), 2) as cumulative_percent
FROM product_sales;
```

## Set Operations

```sql
-- UNION: Combine results (removes duplicates)
SELECT customer_id FROM orders
UNION
SELECT customer_id FROM subscriptions;

-- UNION ALL: Combine results (keeps duplicates)
SELECT customer_id FROM orders
UNION ALL
SELECT customer_id FROM subscriptions;

-- INTERSECT: Common rows
SELECT customer_id FROM orders
INTERSECT
SELECT customer_id FROM subscriptions;

-- EXCEPT: Rows in first but not second
SELECT customer_id FROM orders
EXCEPT
SELECT customer_id FROM subscriptions;
```

## String Aggregation

```sql
-- GROUP_CONCAT equivalent (PostgreSQL)
SELECT
  category,
  STRING_AGG(product_name, ', ' ORDER BY product_name) as products,
  ARRAY_AGG(product_id ORDER BY product_name) as product_ids,
  JSON_AGG(jsonb_build_object('id', id, 'name', name)) as product_json
FROM products
GROUP BY category;

-- With WITHIN GROUP clause
SELECT
  category,
  STRING_AGG(DISTINCT product_name, ', ') WITHIN GROUP (ORDER BY product_name),
  COUNT(*) as product_count
FROM products
GROUP BY category;
```

## Performance Considerations

```sql
-- Window functions can be expensive on large datasets
-- Use WHERE clause before window functions
SELECT *
FROM (
  SELECT
    order_id,
    customer_id,
    amount,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC) as rn
  FROM orders
  WHERE order_date > NOW() - INTERVAL '1 year'
) t
WHERE rn <= 10;

-- Materialize CTEs if referenced multiple times
CREATE MATERIALIZED VIEW customer_totals AS
WITH ct AS (
  SELECT
    customer_id,
    COUNT(*) as order_count,
    SUM(amount) as total_spent
  FROM orders
  GROUP BY customer_id
)
SELECT * FROM ct;

-- Index on window partition columns
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);
```

Analytical SQL patterns unlock powerful insights without leaving the database.
