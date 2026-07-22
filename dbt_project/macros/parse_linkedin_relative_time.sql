{% macro parse_linkedin_relative_time(time_posted_column, reference_column) %}
    {#-
        Converts LinkedIn's relative "time ago" text (e.g., "3 days ago", "2 weeks ago")
        into an absolute timestamp, anchored on reference_column (load timestamp).
        Unmatched or null input yields null.
    -#}
    case
        when {{ time_posted_column }} is null then null
        {% for unit in ["minute", "hour", "day", "week", "month", "year"] %}
        when lower({{ time_posted_column }}) like '%{{ unit }}%'
            then dateadd(
                {{ unit }},
                - nullif(regexp_substr({{ time_posted_column }}, '[0-9]+'), '')::int,
                {{ reference_column }}
            )
        {% endfor %}
        else null
    end
{% endmacro %}
