from __future__ import annotations

import pytest
from nba_api.stats.endpoints import PlayerVsPlayer

from nbadb.core.errors import ResponseContractError
from nbadb.core.nba_api_runtime_contract import pinned_runtime_contracts
from nbadb.extract.nba_api_adapter import _expected_result_sets, _strict_stats_packets


def test_player_vs_player_accepts_only_the_known_reference_column_omission() -> None:
    contract = pinned_runtime_contracts()[PlayerVsPlayer.__name__]
    expected = _expected_result_sets(contract, "playervsplayer")

    expected_by_name = {
        result_set.result_set_name: result_set.expected_columns
        for result_set in contract.result_sets
    }
    assert len(expected) == 10
    for name, headers in expected:
        pinned_headers = expected_by_name[name]
        if name in {
            "Overall",
            "OnOffCourt",
            "ShotDistanceOverall",
            "ShotDistanceOnCourt",
            "ShotDistanceOffCourt",
            "ShotAreaOverall",
            "ShotAreaOnCourt",
            "ShotAreaOffCourt",
        }:
            assert pinned_headers[-2:] == ("CFID", "CFPARAMS")
            assert headers == pinned_headers[:-2]
        else:
            assert headers == pinned_headers

    packets, receipts = _strict_stats_packets(
        [(name, headers, [[None] * len(headers)]) for name, headers in expected],
        expected,
    )
    assert len(packets) == 10
    assert len(receipts) == 10


def test_player_vs_player_rejects_any_other_header_drift() -> None:
    contract = pinned_runtime_contracts()[PlayerVsPlayer.__name__]
    expected = _expected_result_sets(contract, "playervsplayer")
    name, headers = expected[0]

    with pytest.raises(ResponseContractError, match="provider columns differ"):
        _strict_stats_packets(
            [(name, (*headers, "UNAPPROVED_FIELD"), [[None] * (len(headers) + 1)])],
            [expected[0]],
        )
