"""Self-tests for the assertion oracle. Every primitive is itself tested, and the
finding-vs-authoring-error distinction is verified explicitly."""
import pytest

from src.testing.assertions import (
    MeasurementFinding,
    AuthoringError,
    assert_current,
    assert_in_range,
    assert_no_reply,
    assert_varies,
)


@pytest.mark.unit
def test_assert_current_accepts_valid_float():
    assert assert_current(1.5) == 1.5


@pytest.mark.unit
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.0])
def test_assert_current_rejects_bad_values(bad):
    with pytest.raises(MeasurementFinding):
        assert_current(bad)


@pytest.mark.unit
@pytest.mark.parametrize("bad", ["1.5", 2, True, None])
def test_assert_current_rejects_non_float(bad):
    with pytest.raises(MeasurementFinding):
        assert_current(bad)


@pytest.mark.unit
def test_assert_in_range_bad_bounds_is_authoring_error():
    with pytest.raises(AuthoringError):
        assert_in_range(1.0, 10.0, 0.0)


@pytest.mark.unit
def test_assert_in_range_out_of_band_is_finding():
    with pytest.raises(MeasurementFinding):
        assert_in_range(999.0, 0.0, 100.0)


@pytest.mark.unit
def test_assert_no_reply_ok_on_none():
    assert_no_reply(None)


@pytest.mark.unit
def test_assert_no_reply_finding_on_data():
    with pytest.raises(MeasurementFinding):
        assert_no_reply(b"1.23")


@pytest.mark.unit
def test_assert_varies_needs_two_samples():
    with pytest.raises(AuthoringError):
        assert_varies([1.0])


@pytest.mark.unit
def test_assert_varies_all_equal_is_finding():
    with pytest.raises(MeasurementFinding):
        assert_varies([2.0, 2.0, 2.0])


@pytest.mark.unit
def test_assert_varies_ok_when_spread():
    assert_varies([1.0, 2.0, 3.0])
