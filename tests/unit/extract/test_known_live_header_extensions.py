from __future__ import annotations

import pytest
from nba_api.stats.endpoints import (
    DraftHistory,
    LeagueDashTeamShotLocations,
    PlayerDashboardByClutch,
)

from nbadb.core.errors import ResponseContractError
from nbadb.core.nba_api_runtime_contract import pinned_runtime_contracts
from nbadb.extract.nba_api_adapter import _expected_result_sets, _strict_stats_packets


def _assert_known_extension(
    endpoint_cls: type,
    slug: str,
    name: str,
    additions: tuple[str, ...],
) -> None:
    contract = pinned_runtime_contracts()[endpoint_cls.__name__]
    expected = _expected_result_sets(contract, slug)
    result_set_name, headers = expected[0]
    assert result_set_name == name
    assert headers[-len(additions) :] == additions

    packets, receipts = _strict_stats_packets(
        [(name, list(headers), [[0] * len(headers)])],
        expected,
    )
    assert packets[0].headers == headers
    assert len(receipts) == 1


def test_draft_history_retains_the_known_player_profile_flag() -> None:
    _assert_known_extension(
        DraftHistory,
        "drafthistory",
        "DraftHistory",
        ("PLAYER_PROFILE_FLAG",),
    )


def test_team_shot_locations_retains_known_corner_zone_totals() -> None:
    _assert_known_extension(
        LeagueDashTeamShotLocations,
        "leaguedashteamshotlocations",
        "ShotLocations",
        ("corner_3_fgm", "corner_3_fga", "corner_3_fg_pct"),
    )


_CLUTCH_LIVE_HEADERS = (
    "GROUP_SET",
    "GROUP_VALUE",
    "GP",
    "W",
    "L",
    "W_PCT",
    "MIN",
    "FGM",
    "FGA",
    "FG_PCT",
    "FG3M",
    "FG3A",
    "FG3_PCT",
    "FTM",
    "FTA",
    "FT_PCT",
    "OREB",
    "DREB",
    "REB",
    "AST",
    "TOV",
    "STL",
    "BLK",
    "BLKA",
    "PF",
    "PFD",
    "PTS",
    "PLUS_MINUS",
    "NBA_FANTASY_PTS",
    "DD2",
    "TD3",
    "WNBA_FANTASY_PTS",
    "FP_HIGH_SCORE",
    "GP_RANK",
    "W_RANK",
    "L_RANK",
    "W_PCT_RANK",
    "MIN_RANK",
    "FGM_RANK",
    "FGA_RANK",
    "FG_PCT_RANK",
    "FG3M_RANK",
    "FG3A_RANK",
    "FG3_PCT_RANK",
    "FTM_RANK",
    "FTA_RANK",
    "FT_PCT_RANK",
    "OREB_RANK",
    "DREB_RANK",
    "REB_RANK",
    "AST_RANK",
    "TOV_RANK",
    "STL_RANK",
    "BLK_RANK",
    "BLKA_RANK",
    "PF_RANK",
    "PFD_RANK",
    "PTS_RANK",
    "PLUS_MINUS_RANK",
    "NBA_FANTASY_PTS_RANK",
    "DD2_RANK",
    "TD3_RANK",
    "WNBA_FANTASY_PTS_RANK",
    "FP_HIGH_SCORE_RANK",
    "TEAM_COUNT",
)


def test_player_dashboard_clutch_retains_exact_live_header_extension() -> None:
    contract = pinned_runtime_contracts()[PlayerDashboardByClutch.__name__]
    expected = _expected_result_sets(contract, contract.endpoint_slug)

    assert len(expected) == 11
    assert {headers for _name, headers in expected} == {_CLUTCH_LIVE_HEADERS}

    packets, receipts = _strict_stats_packets(
        [
            (name, _CLUTCH_LIVE_HEADERS, [[0] * len(_CLUTCH_LIVE_HEADERS)])
            for name, _headers in expected
        ],
        expected,
    )

    assert tuple(packet.headers for packet in packets) == (_CLUTCH_LIVE_HEADERS,) * 11
    assert len(receipts) == 11


def test_player_dashboard_clutch_rejects_unapproved_header_extension() -> None:
    contract = pinned_runtime_contracts()[PlayerDashboardByClutch.__name__]
    expected = _expected_result_sets(contract, contract.endpoint_slug)
    result_set_name, _headers = expected[0]

    with pytest.raises(ResponseContractError, match="provider columns differ"):
        _strict_stats_packets(
            [
                (
                    result_set_name,
                    (*_CLUTCH_LIVE_HEADERS, "UNAPPROVED_FIELD"),
                    [[0] * (len(_CLUTCH_LIVE_HEADERS) + 1)],
                )
            ],
            [expected[0]],
        )
