import snowflake.connector
from rest_framework import serializers
from django.conf import settings


def fetch_snowflake_data(customer: str, site_name: str, plant: str):
    """
    To fetched data from snowflake
    """

    # Establish Connection
    conn = snowflake.connector.connect(
        user=settings.SNOWFLAKE_USER,
        password=settings.SNOWFLAKE_PASSWORD,
        account=settings.SNOWFLAKE_ACCOUNT,
        database=settings.SNOWFLAKE_DATABASE,
        warehouse=settings.SNOWFLAKE_WAREHOUSE,
        role=settings.SNOWFLAKE_ROLE,
        schema=settings.SNOWFLAKE_SCHEMA,
    )

    # Create a cursor to execute queries
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT
            DATEADD(min, FLOOR(DATE_PART(minute, systemwritetime_tz)/5)*5, DATE_TRUNC(hr, systemwritetime_tz)) AS time,
            ROUND(AVG(h.value),2) AS value,
            CONCAT('rack-', h.rack,'  item-', h.item,' type-', h.type) AS series
        FROM HCSDEVICE h
        WHERE CONCAT(Customer,'-', Sitename,'-', plant) = %(CompanySitePlant)s
              AND category = 'phm'
              AND item = 'level'
              AND h.value != 0
              and systemwritetime_tz between dateAdd(hr,-24,current_timestamp) and (current_timestamp)
        GROUP BY series, time
        ORDER BY time DESC
        LIMIT 1000;
        """,
            {
                'CompanySitePlant': f'{customer}-{site_name}-{plant}',
            }
        )

        # Fetch all rows of data from the query results
        results = cursor.fetchall()
    except Exception:
        raise serializers.ValidationError(
            {
                'error': 'some unexpected error occurred'
            }
        )

    # Close cursor and connection
    cursor.close()
    conn.close()

    return results
