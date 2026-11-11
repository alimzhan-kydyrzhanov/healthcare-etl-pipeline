-- name: monthly_revenue_by_category
-- Выручка и число процедур по месяцам и категориям
SELECT d.year, d.month, p.category,
       COUNT(*)        AS procedures,
       SUM(f.cost_kzt) AS revenue_kzt
FROM fact_procedure f
JOIN dim_date d      ON d.date_key = f.date_key
JOIN dim_procedure p ON p.procedure_code = f.procedure_code
GROUP BY d.year, d.month, p.category
ORDER BY d.year, d.month, revenue_kzt DESC;

-- name: top_procedures_by_age_group
-- Самая частая процедура в каждой возрастной группе (оконная функция)
WITH counts AS (
    SELECT pt.age_group, pr.name, COUNT(*) AS n,
           RANK() OVER (PARTITION BY pt.age_group ORDER BY COUNT(*) DESC) AS rnk
    FROM fact_procedure f
    JOIN dim_patient pt  ON pt.patient_key = f.patient_key
    JOIN dim_procedure pr ON pr.procedure_code = f.procedure_code
    GROUP BY pt.age_group, pr.name
)
SELECT age_group, name, n FROM counts WHERE rnk = 1 ORDER BY age_group;

-- name: data_quality_summary
-- Сколько строк отклонено и почему
SELECT source_table, reason, COUNT(*) AS rows_rejected
FROM dq_rejected
WHERE run_id = (SELECT run_id FROM etl_runs ORDER BY started_at DESC LIMIT 1)
GROUP BY source_table, reason
ORDER BY rows_rejected DESC;
