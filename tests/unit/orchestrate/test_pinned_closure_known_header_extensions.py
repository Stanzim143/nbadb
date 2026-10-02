from __future__ import annotations

import hashlib
import json

import pytest

from nbadb.core.errors import ParserInputCaptureIntegrityError
from nbadb.core.nba_api_runtime_contract import pinned_runtime_contracts
from nbadb.extract.bronze import ResultSetReceipt, parent_occurrence_states_digest
from nbadb.extract.nba_api_adapter import _expected_result_sets
from nbadb.orchestrate.extractor_runner import _pinned_closure_result_sets


def _headers_sha256(headers: tuple[str, ...]) -> str:
    encoded = json.dumps(list(headers), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _receipt(
    headers: tuple[str, ...],
    *,
    name: str = "ShotLocations",
    ordinal: int = 0,
) -> ResultSetReceipt:
    return ResultSetReceipt(
        name=name,
        provider_index=ordinal,
        canonical_index=ordinal,
        headers_sha256=_headers_sha256(headers),
        row_count=30,
        json_path=None,
        container_kind="nba_api_result_set",
        container_count=1,
        missing_count=0,
        null_count=0,
        parent_observation_count=1,
        parent_occurrence_states_sha256=parent_occurrence_states_digest(("present",)),
        observed_field_orders_sha256=_headers_sha256(headers),
        normalized_output_sha256="a" * 64,
    )


def _known_team_shot_headers() -> tuple[str, ...]:
    contract = pinned_runtime_contracts()["LeagueDashTeamShotLocations"]
    return _expected_result_sets(contract, contract.endpoint_slug)[0][1]


def test_closure_accepts_exact_known_team_shot_header_extension() -> None:
    headers = _known_team_shot_headers()

    projected = _pinned_closure_result_sets(
        "LeagueDashTeamShotLocations",
        (_receipt(headers),),
    )

    assert len(projected) == 1
    assert projected[0].ordered_columns_sha256 == _headers_sha256(headers)


def test_closure_rejects_unapproved_team_shot_header_extension() -> None:
    headers = (*_known_team_shot_headers(), "unapproved_field")

    with pytest.raises(ParserInputCaptureIntegrityError, match="lossless drift"):
        _pinned_closure_result_sets(
            "LeagueDashTeamShotLocations",
            (_receipt(headers),),
        )


def test_closure_accepts_all_known_player_clutch_header_extensions() -> None:
    contract = pinned_runtime_contracts()["PlayerDashboardByClutch"]
    expected = _expected_result_sets(contract, contract.endpoint_slug)
    receipts = tuple(
        _receipt(headers, name=name, ordinal=index)
        for index, (name, headers) in enumerate(expected)
    )

    projected = _pinned_closure_result_sets("PlayerDashboardByClutch", receipts)

    assert len(projected) == 11
    assert tuple(item.ordered_columns_sha256 for item in projected) == tuple(
        _headers_sha256(headers) for _name, headers in expected
    )


def test_closure_rejects_unapproved_player_clutch_header_extension() -> None:
    contract = pinned_runtime_contracts()["PlayerDashboardByClutch"]
    expected = _expected_result_sets(contract, contract.endpoint_slug)
    receipts = [
        _receipt(
            (*headers, "UNAPPROVED_FIELD") if index == 0 else headers,
            name=name,
            ordinal=index,
        )
        for index, (name, headers) in enumerate(expected)
    ]

    with pytest.raises(ParserInputCaptureIntegrityError, match="lossless drift"):
        _pinned_closure_result_sets("PlayerDashboardByClutch", tuple(receipts))
