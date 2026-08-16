-- Resumen territorial reproducible sobre la tabla coverage_centers.
SELECT
    department,
    province,
    COUNT(*) AS centers,
    SUM(classification = 'RURAL') AS rural_centers,
    ROUND(AVG(max_4g_cg) * 100, 2) AS avg_guaranteed_4g_pct,
    ROUND(AVG(max_4g_total) * 100, 2) AS avg_total_4g_pct,
    ROUND(AVG(priority_score), 2) AS avg_priority,
    SUM(coverage_category = 'BRECHA CRITICA') AS critical_gap_centers
FROM coverage_centers
GROUP BY department, province
ORDER BY avg_priority DESC;

