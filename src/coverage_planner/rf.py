"""Modelos de propagación interpretables y presupuesto de enlace."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LinkBudget:
    """Parámetros simplificados de un enlace descendente."""

    tx_power_dbm: float = 43.0
    tx_gain_dbi: float = 15.0
    tx_losses_db: float = 3.0
    rx_gain_dbi: float = 0.0
    receiver_sensitivity_dbm: float = -100.0
    fade_margin_db: float = 10.0

    @property
    def max_path_loss_db(self) -> float:
        return (
            self.tx_power_dbm
            + self.tx_gain_dbi
            - self.tx_losses_db
            + self.rx_gain_dbi
            - self.receiver_sensitivity_dbm
            - self.fade_margin_db
        )


def _positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} debe ser mayor que cero.")


def free_space_path_loss(frequency_mhz: float, distance_km: float | np.ndarray) -> np.ndarray:
    """Pérdida de espacio libre en dB; frecuencia en MHz y distancia en km."""
    _positive(frequency_mhz, "frequency_mhz")
    distances = np.asarray(distance_km, dtype=float)
    if np.any(distances <= 0):
        raise ValueError("distance_km debe ser mayor que cero.")
    return 32.44 + 20 * np.log10(frequency_mhz) + 20 * np.log10(distances)


def mobile_antenna_correction(frequency_mhz: float, mobile_height_m: float) -> float:
    """Corrección de antena móvil para ciudad pequeña/mediana."""
    _positive(frequency_mhz, "frequency_mhz")
    _positive(mobile_height_m, "mobile_height_m")
    log_frequency = np.log10(frequency_mhz)
    return (1.1 * log_frequency - 0.7) * mobile_height_m - (1.56 * log_frequency - 0.8)


def hata_path_loss(
    frequency_mhz: float,
    distance_km: float | np.ndarray,
    base_height_m: float = 40.0,
    mobile_height_m: float = 1.5,
    environment: str = "rural",
) -> np.ndarray:
    """Modelo Okumura-Hata urbano, suburbano o rural."""
    if not 150 <= frequency_mhz <= 1500:
        raise ValueError("Okumura-Hata es válido entre 150 y 1500 MHz.")
    if not 30 <= base_height_m <= 200:
        raise ValueError("base_height_m debe estar entre 30 y 200 m para Hata.")
    if not 1 <= mobile_height_m <= 10:
        raise ValueError("mobile_height_m debe estar entre 1 y 10 m para Hata.")

    distances = np.asarray(distance_km, dtype=float)
    if np.any((distances < 1) | (distances > 20)):
        raise ValueError("Okumura-Hata es válido entre 1 y 20 km.")

    correction = mobile_antenna_correction(frequency_mhz, mobile_height_m)
    log_frequency = np.log10(frequency_mhz)
    urban = (
        69.55
        + 26.16 * log_frequency
        - 13.82 * np.log10(base_height_m)
        - correction
        + (44.9 - 6.55 * np.log10(base_height_m)) * np.log10(distances)
    )
    environment = environment.lower()
    if environment == "urban":
        return urban
    if environment == "suburban":
        return urban - 2 * np.log10(frequency_mhz / 28) ** 2 - 5.4
    if environment == "rural":
        return urban - 4.78 * log_frequency**2 + 18.33 * log_frequency - 40.94
    raise ValueError("environment debe ser urban, suburban o rural.")


def cost231_path_loss(
    frequency_mhz: float,
    distance_km: float | np.ndarray,
    base_height_m: float = 40.0,
    mobile_height_m: float = 1.5,
    metropolitan: bool = False,
) -> np.ndarray:
    """Modelo COST-231 Hata para 1500-2000 MHz."""
    if not 1500 <= frequency_mhz <= 2000:
        raise ValueError("COST-231 Hata es válido entre 1500 y 2000 MHz.")
    if not 30 <= base_height_m <= 200:
        raise ValueError("base_height_m debe estar entre 30 y 200 m para COST-231.")
    if not 1 <= mobile_height_m <= 10:
        raise ValueError("mobile_height_m debe estar entre 1 y 10 m para COST-231.")

    distances = np.asarray(distance_km, dtype=float)
    if np.any((distances < 1) | (distances > 20)):
        raise ValueError("COST-231 Hata es válido entre 1 y 20 km.")
    correction = mobile_antenna_correction(frequency_mhz, mobile_height_m)
    city_correction = 3.0 if metropolitan else 0.0
    return (
        46.3
        + 33.9 * np.log10(frequency_mhz)
        - 13.82 * np.log10(base_height_m)
        - correction
        + (44.9 - 6.55 * np.log10(base_height_m)) * np.log10(distances)
        + city_correction
    )


def path_loss(
    model: str,
    frequency_mhz: float,
    distance_km: float | np.ndarray,
    base_height_m: float = 40.0,
    mobile_height_m: float = 1.5,
    environment: str = "rural",
) -> np.ndarray:
    """Despachador uniforme para los tres modelos disponibles."""
    normalized_model = model.lower().replace("-", "").replace(" ", "")
    if normalized_model in {"fspl", "freespace"}:
        return free_space_path_loss(frequency_mhz, distance_km)
    if normalized_model in {"hata", "okumurahata"}:
        return hata_path_loss(
            frequency_mhz,
            distance_km,
            base_height_m,
            mobile_height_m,
            environment,
        )
    if normalized_model in {"cost231", "cost231hata"}:
        return cost231_path_loss(
            frequency_mhz,
            distance_km,
            base_height_m,
            mobile_height_m,
            metropolitan=environment.lower() == "urban",
        )
    raise ValueError(f"Modelo no soportado: {model}")


def estimate_radius_km(
    model: str,
    frequency_mhz: float,
    budget: LinkBudget,
    base_height_m: float = 40.0,
    mobile_height_m: float = 1.5,
    environment: str = "rural",
) -> float:
    """Calcula el radio máximo dentro del dominio válido del modelo."""
    normalized_model = model.lower().replace("-", "").replace(" ", "")
    lower, upper = (0.01, 100.0) if normalized_model in {"fspl", "freespace"} else (1.0, 20.0)

    lower_loss = float(
        path_loss(model, frequency_mhz, lower, base_height_m, mobile_height_m, environment)
    )
    upper_loss = float(
        path_loss(model, frequency_mhz, upper, base_height_m, mobile_height_m, environment)
    )
    if budget.max_path_loss_db <= lower_loss:
        return round(lower, 3)
    if budget.max_path_loss_db >= upper_loss:
        return round(upper, 3)

    for _ in range(80):
        midpoint = (lower + upper) / 2
        loss = float(
            path_loss(
                model,
                frequency_mhz,
                midpoint,
                base_height_m,
                mobile_height_m,
                environment,
            )
        )
        if loss <= budget.max_path_loss_db:
            lower = midpoint
        else:
            upper = midpoint
    return round(lower, 3)

