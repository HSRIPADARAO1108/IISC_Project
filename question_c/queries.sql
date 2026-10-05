-- Question C, Level 2: three queries written by hand. :now is bound to the reference time.

-- Q1. Alerts per user in the last 24 hours (users with none still show 0)
SELECT u.user_id, u.name, COUNT(a.alert_id) AS alerts_24h
FROM users u
LEFT JOIN alerts a ON a.user_id = u.user_id AND a.ts >= :now - 86400 AND a.ts <= :now
GROUP BY u.user_id, u.name
ORDER BY u.user_id;

-- Q2. Users with more than five alerts in any one clock hour (and the hour it happened)
SELECT user_id,
       strftime('%Y-%m-%d %H:00', ts, 'unixepoch') AS hour_utc,
       COUNT(*) AS alerts_in_hour
FROM alerts
GROUP BY user_id, hour_utc
HAVING COUNT(*) > 5
ORDER BY user_id, hour_utc;

-- Q3. Average heart rate per user per hour (sensor-lost zeros are not heart rates, so they are excluded)
SELECT user_id,
       strftime('%Y-%m-%d %H:00', ts, 'unixepoch') AS hour_utc,
       ROUND(AVG(hr), 2) AS avg_hr,
       COUNT(*)          AS samples
FROM readings
WHERE hr > 0
GROUP BY user_id, hour_utc
ORDER BY user_id, hour_utc;
