SELECT 
    p.id,
    p.name AS product_name,
    c.name AS category_name,
    SUM(oi.quantity) AS total_sold,
    SUM(oi.subtotal) AS total_revenue,
    RANK() OVER (
        PARTITION BY p.category_id 
        ORDER BY SUM(oi.quantity) DESC
    ) AS rank_in_category
FROM products p
INNER JOIN categories c ON p.category_id = c.id
INNER JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name, c.name, p.category_id
ORDER BY c.name, rank_in_category;

WITH customer_revenue AS (
    SELECT 
        c.id AS customer_id,
        c.name AS customer_name,
        c.email,
        COUNT(o.id) AS total_orders,
        SUM(o.total_amount) AS total_revenue,
        AVG(o.total_amount) AS avg_order_value,
        MIN(o.created_at) AS first_order_date,
        MAX(o.created_at) AS last_order_date
    FROM customers c
    LEFT JOIN orders o ON c.id = o.customer_id
    GROUP BY c.id, c.name, c.email
)
SELECT 
    customer_id,
    customer_name,
    email,
    total_orders,
    ROUND(total_revenue::numeric, 2) AS total_revenue,
    ROUND(avg_order_value::numeric, 2) AS avg_order_value,
    first_order_date,
    last_order_date,
    CASE 
        WHEN total_revenue > 1000 THEN 'VIP'
        WHEN total_revenue > 500 THEN 'Gold'
        WHEN total_revenue > 100 THEN 'Silver'
        ELSE 'Bronze'
    END AS customer_tier
FROM customer_revenue
ORDER BY total_revenue DESC NULLS LAST;

SELECT 
    id,
    name,
    price,
    metadata->>'brand' AS brand,
    metadata->>'color' AS color
FROM products
WHERE metadata @> '{"brand": "TechCorp"}';

-- Find products by color (using JSON text extraction ->>)
SELECT 
    id,
    name,
    price,
    metadata->>'color' AS color
FROM products
WHERE metadata->>'color' = 'Black';

-- Find products that have a specific key (using existence operator ?)
SELECT 
    id,
    name,
    metadata->>'brand' AS brand
FROM products
WHERE metadata ? 'brand';

-- Find products matching multiple criteria
SELECT 
    id,
    name,
    price,
    metadata
FROM products
WHERE metadata @> '{"brand": "TechCorp", "color": "Silver"}';

