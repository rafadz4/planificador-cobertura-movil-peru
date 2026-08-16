import numpy as np
import pytest

from coverage_planner.rf import (
    LinkBudget,
    estimate_radius_km,
    free_space_path_loss,
    hata_path_loss,
)


def test_fspl_reference_value() -> None:
    assert float(free_space_path_loss(900, 1)) == pytest.approx(91.52, abs=0.02)


def test_hata_loss_increases_with_distance() -> None:
    losses = hata_path_loss(850, np.array([1.0, 5.0, 10.0]), environment="rural")
    assert np.all(np.diff(losses) > 0)


def test_radius_stays_inside_model_domain() -> None:
    radius = estimate_radius_km("hata", 850, LinkBudget(), environment="rural")
    assert 1.0 <= radius <= 20.0


def test_hata_rejects_frequency_outside_validity() -> None:
    with pytest.raises(ValueError, match="150 y 1500"):
        hata_path_loss(1800, 5)

