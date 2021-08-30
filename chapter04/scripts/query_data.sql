SELECT p.pagename, p.hr AS "hour", p.average AS "average pageviews"
FROM (
     SELECT
        pagename,
        date_part('hour', datetime) as hr,
        AVG(pageviewcount) AS average,
        row_number() over (PARTITION BY pagename ORDER BY AVG(pageviewcount) DESC) as row_number
    FROM pageview_counts
    GROUP BY pagename, hr
) AS p
WHERE row_number=1;
