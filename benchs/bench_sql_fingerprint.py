from pytest_sqlguard.sql import sql_fingerprint as sql_fingperprint_py

QUERY = """
-- CTE to find customers with minimum number of purchases
WITH FrequentCustomers AS (
    SELECT
        customer_id,
        COUNT(order_id) AS total_orders
    FROM
        Orders
    GROUP BY
        customer_id
    HAVING
        COUNT(order_id) >= 5
),

-- CTE to calculate the average order value per product category
CategoryAverage AS (
    SELECT
        pc.category_id,
        pc.category_name,
        AVG(oi.price * oi.quantity) AS avg_category_value
    FROM
        OrderItems oi
    JOIN
        Products p ON oi.product_id = p.product_id
    JOIN
        ProductCategories pc ON p.category_id = pc.category_id
    GROUP BY
        pc.category_id, pc.category_name
)

-- Main query joining the CTEs with other tables
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    fc.total_orders,
    o.order_id,
    o.order_date,
    p.product_name,
    oi.quantity,
    oi.price,
    ca.category_name,
    ca.avg_category_value,
    (oi.price * oi.quantity) AS order_item_total,
    CASE
        WHEN (oi.price * oi.quantity) > ca.avg_category_value THEN 'Above Average'
        WHEN (oi.price * oi.quantity) = ca.avg_category_value THEN 'Average'
        ELSE 'Below Average'
    END AS price_comparison
FROM
    Customers c
JOIN
    FrequentCustomers fc ON c.customer_id = fc.customer_id
JOIN
    Orders o ON c.customer_id = o.customer_id
JOIN
    OrderItems oi ON o.order_id = oi.order_id
JOIN
    Products p ON oi.product_id = p.product_id
JOIN
    CategoryAverage ca ON p.category_id = ca.category_id
WHERE
    o.order_date >= DATEADD(MONTH, -6, GETDATE())
    AND oi.price > 10.00
    AND p.category_id IN (1, 3, 5)
ORDER BY
    c.customer_id, o.order_date DESC;
"""


def print_sql_fingerprint_py():
    print(sql_fingperprint_py(query=QUERY))


def test_normalize_python(benchmark):
    """
    Benchmark our sql_fingerprint python version
    It disables the lru_cache surrounding that function.
    """

    benchmark(
        sql_fingperprint_py.__wrapped__,
        query=QUERY,
    )


def test_normalize_rust(benchmark):
    from pytest_sqlguard.sqlrs import normalize_sql

    benchmark(normalize_sql, QUERY)


if __name__ == "__main__":
    print_sql_fingerprint_py()
