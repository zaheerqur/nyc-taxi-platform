-- Fails if any negative or zero fares survive the staging filter
SELECT *
FROM {{ ref('stg_trips') }}
WHERE fare_amount <= 0
