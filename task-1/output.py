import sqlite3
import pandas as pd

conn = sqlite3.connect('ecomm_data.db')

query = """
SELECT 
    p.name AS Product, 
    CAST(REPLACE(p1.price_next_day, '£', '') AS REAL) AS New_Price, 
    CAST(REPLACE(p.price, '£', '') AS REAL) AS Old_Price,
    ROUND(
        (
            (CAST(REPLACE(p1.price_next_day, '£', '') AS REAL) - 
             CAST(REPLACE(p.price, '£', '') AS REAL)) 
            * 100.0 
            / CAST(REPLACE(p.price, '£', '') AS REAL)
        ), 1
    ) AS Change
FROM products p 
JOIN products_next_day p1 
  ON p.sku = p1.sku 
WHERE p.price != p1.price_next_day;
"""
cursor = conn.execute(query)
df = pd.read_sql_query(query,conn)
df.to_csv('result.csv',index=False)

print(cursor.fetchall())

conn.close()