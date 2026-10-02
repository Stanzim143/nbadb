from __future__ import annotations

import polars as pl
import pytest
from nba_api.stats.endpoints import BoxScoreMatchupsV3

from nbadb.core.errors import ResponseContractError
from nbadb.core.nba_api_runtime_contract import pinned_runtime_contracts
from nbadb.extract.base import _normalize_box_score_matchups
from nbadb.extract.nba_api_adapter import _expected_result_sets, _strict_stats_packets
from nbadb.schemas.raw.matchup import RawBoxScoreMatchupsSchema
from nbadb.schemas.staging.misc import StagingBoxScoreMatchupsSchema


def test_matchups_accepts_only_the_current_offensive_player_header_labels() -> None:
    contract = pinned_runtime_contracts()[BoxScoreMatchupsV3.__name__]
    name, headers = _expected_result_sets(contract, "boxscorematchupsv3")[0]

    assert name == "PlayerStats"
    assert headers[headers.index("playerSlugOff") + 1 :][:2] == (
        "positionOff",
        "commentOff",
    )
    assert "positionDef" not in headers
    assert "commentDef" not in headers

    packets, receipts = _strict_stats_packets(
        [(name, headers, [[None] * len(headers)])],
        [(name, headers)],
    )
    assert len(packets) == len(receipts) == 1

    with pytest.raises(ResponseContractError, match="provider columns differ"):
        _strict_stats_packets(
            [(name, (*headers, "UNAPPROVED_FIELD"), [[None] * (len(headers) + 1)])],
            [(name, headers)],
        )


def test_matchups_normalizer_rejects_more_than_two_game_teams() -> None:
    source = pl.DataFrame(
        {
            "game_id": ["0022400001"] * 3,
            "team_id": [1610612738, 1610612737, 1610612739],
            "team_tricode": ["BOS", "ATL", "CHI"],
            "person_id_off": [1001, 2001, 3001],
            "first_name_off": ["A", "B", "C"],
            "family_name_off": ["One", "Two", "Three"],
            "person_id_def": [2001, 1001, 1001],
            "first_name_def": ["B", "A", "A"],
            "family_name_def": ["Two", "One", "One"],
            "matchup_minutes": ["0:30"] * 3,
        }
    )

    with pytest.raises(ResponseContractError, match="exactly two"):
        _normalize_box_score_matchups(source)


def test_matchups_normalizer_derives_opponent_identity_and_validates_staging() -> None:
    metric_values = {
        "matchup_minutes": "1:30",
        "matchup_minutes_sort": 90.0,
        "partial_possessions": 2.5,
        "percentage_defender_total_time": 0.1,
        "percentage_offensive_total_time": 0.1,
        "percentage_total_time_both_on": 0.2,
        "switches_on": 0,
        "player_points": 2,
        "team_points": 4,
        "matchup_assists": 0,
        "matchup_potential_assists": 1,
        "matchup_turnovers": 0,
        "matchup_blocks": 0,
        "matchup_field_goals_made": 1,
        "matchup_field_goals_attempted": 2,
        "matchup_field_goals_percentage": 0.5,
        "matchup_three_pointers_made": 0,
        "matchup_three_pointers_attempted": 1,
        "matchup_three_pointers_percentage": 0.0,
        "help_blocks": 0,
        "help_field_goals_made": 0,
        "help_field_goals_attempted": 0,
        "help_field_goals_percentage": 0.0,
        "matchup_free_throws_made": 0,
        "matchup_free_throws_attempted": 0,
        "shooting_fouls": 0,
    }
    rows = []
    for team_id, team_code, off_id, def_id, off_name, def_name in (
        (1610612738, "BOS", 1001, 2001, "Offense A", "Defense A"),
        (1610612737, "ATL", 2001, 1001, "Offense B", "Defense B"),
    ):
        rows.append(
            {
                "game_id": "0022400001",
                "team_id": team_id,
                "team_tricode": team_code,
                "person_id_off": off_id,
                "first_name_off": off_name.split()[0],
                "family_name_off": off_name.split()[1],
                "position_off": "G",
                "comment_off": "",
                "person_id_def": def_id,
                "first_name_def": def_name.split()[0],
                "family_name_def": def_name.split()[1],
                **metric_values,
            }
        )

    result = _normalize_box_score_matchups(pl.DataFrame(rows))
    result = RawBoxScoreMatchupsSchema.validate(result)
    result = StagingBoxScoreMatchupsSchema.validate(result)

    assert result.height == 2
    assert result.get_column("matchup_minutes").to_list() == [1.5, 1.5]
    assert result.get_column("off_team_id").to_list() == [1610612738, 1610612737]
    assert result.get_column("def_team_id").to_list() == [1610612737, 1610612738]
    assert result.get_column("off_team_abbreviation").to_list() == ["BOS", "ATL"]
    assert result.get_column("def_team_abbreviation").to_list() == ["ATL", "BOS"]
