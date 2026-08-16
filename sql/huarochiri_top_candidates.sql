SELECT
    center_id,
    center_name,
    district,
    classification,
    priority_score,
    ROUND(max_4g_cg * 100, 2) AS guaranteed_4g_pct,
    ROUND(max_4g_total * 100, 2) AS total_4g_pct,
    operator_count_4g_total,
    latitude,
    longitude
FROM huarochiri_priority
ORDER BY priority_score DESC
LIMIT 100;

