from __future__ import annotations

from typing import ClassVar

from nbadb.transform.base import SqlTransformer


class AnalyticsClutchPerformanceTransformer(SqlTransformer):
    output_table: ClassVar[str] = "analytics_clutch_performance"
    depends_on: ClassVar[list[str]] = [
        "fact_player_clutch_detail",
        "dim_all_players",
    ]

    _SQL: ClassVar[str] = """
        WITH clutch_enriched AS (
            SELECT
                c.*,
                p.display_first_last AS player_name,
                NULL::BIGINT AS team_id,
                NULL::VARCHAR AS team_abbreviation
            FROM fact_player_clutch_detail c
            LEFT JOIN (
                SELECT
                    person_id,
                    MIN(display_first_last) AS display_first_last,
                    MIN(TRY_CAST(from_year AS INTEGER)) AS from_year,
                    MAX(TRY_CAST(to_year AS INTEGER)) AS to_year
                FROM dim_all_players
                GROUP BY person_id
            ) p
              ON p.person_id = c.player_id
             AND (
                 p.from_year IS NULL
                 OR TRY_CAST(SUBSTR(c.season_year, 1, 4) AS INTEGER) >= p.from_year
             )
             AND (
                 p.to_year IS NULL
                 OR TRY_CAST(SUBSTR(c.season_year, 1, 4) AS INTEGER) <= p.to_year
             )
        )
        SELECT
            c.player_id,
            c.team_id,
            c.season_year,
            c.season_type,
            c.clutch_window,
            c.group_set,
            c.group_value,
            c.player_name,
            c.team_abbreviation,
            c.gp, c.w, c.l, c.min,
            c.fgm, c.fga, c.fg_pct,
            c.fg3m, c.fg3a, c.fg3_pct,
            c.ftm, c.fta, c.ft_pct,
            c.oreb, c.dreb, c.reb,
            c.ast, c.tov, c.stl, c.blk,
            c.pf, c.pts, c.plus_minus,
            NULL::DOUBLE AS net_rating,
            NULL::DOUBLE AS off_rating,
            NULL::DOUBLE AS def_rating
        FROM clutch_enriched c
    """
