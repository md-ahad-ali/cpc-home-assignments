"""
Subsystem 3: Energy Analytics & Sustainability
Owner: Md. Ahad Ali
"""

from collections import defaultdict
from datetime import datetime
from statistics import mean, pstdev


class AnalyticsEngine:
    VALID_PERIODS = ("hour", "day", "month")

    def __init__(self, tariff_rate=0.30, emission_factor=0.40, logs=None):
        self._tariff_rate = 0.0
        self._emission_factor = 0.0
        self._logs = []
        self.set_tariff_rate(tariff_rate)
        self.set_emission_factor(emission_factor)
        self.initialize(logs or [])

    def initialize(self, logs):
        for row in logs:
            if row["energy_consumed_kwh"] < 0:
                raise ValueError("energy_consumed_kwh must not be negative")
        self._logs = list(logs)

    def get_tariff_rate(self):
        return self._tariff_rate

    def get_emission_factor(self):
        return self._emission_factor

    def get_logs(self):
        return list(self._logs)

    def set_tariff_rate(self, value):
        if value < 0:
            raise ValueError("tariff_rate must not be negative")
        self._tariff_rate = float(value)

    def set_emission_factor(self, value):
        if value < 0:
            raise ValueError("emission_factor must not be negative")
        self._emission_factor = float(value)

    def calculate_costs(self, kwh):
        return round(kwh * self._tariff_rate, 2)

    def calculate_carbon(self, kwh):
        return round(kwh * self._emission_factor, 2)

    def total_kwh(self):
        return round(sum(r["energy_consumed_kwh"] for r in self._logs), 2)

    def _summarize(self, kwh):
        return {
            "total_kwh": round(kwh, 2),
            "cost_eur": self.calculate_costs(kwh),
            "carbon_kg_co2": self.calculate_carbon(kwh),
        }

    def _aggregate(self, key_func):
        groups = defaultdict(float)
        for row in self._logs:
            groups[key_func(row)] += row["energy_consumed_kwh"]
        return {key: self._summarize(kwh) for key, kwh in sorted(groups.items())}

    def aggregate_by_room(self):
        return self._aggregate(lambda r: r["room_id"])

    def aggregate_by_building(self):
        return self._aggregate(lambda r: r["building_id"])

    def aggregate_by_time(self, period="day"):
        if period not in AnalyticsEngine.VALID_PERIODS:
            raise ValueError("period must be one of " + str(AnalyticsEngine.VALID_PERIODS))
        formats = {
            "hour": "%Y-%m-%d %H:00",
            "day": "%Y-%m-%d",
            "month": "%Y-%m"
        }
        fmt = formats[period]
        return self._aggregate(lambda r: r["timestamp"].strftime(fmt))


class SustainabilityCalculator:
    def __init__(self, efficiency_benchmark=100.0, period_days=365):
        self._efficiency_benchmark = 0.0
        self._period_days = 365
        self._ready = False
        self.set_efficiency_benchmark(efficiency_benchmark)
        self.set_period_days(period_days)
        self.initialize()

    def initialize(self):
        self._ready = True

    def get_efficiency_benchmark(self):
        return self._efficiency_benchmark

    def get_period_days(self):
        return self._period_days

    def is_ready(self):
        return self._ready

    def set_efficiency_benchmark(self, value):
        if value <= 0:
            raise ValueError("efficiency_benchmark must be above zero")
        self._efficiency_benchmark = float(value)

    def set_period_days(self, value):
        if value <= 0:
            raise ValueError("period_days must be above zero")
        self._period_days = int(value)

    def energy_intensity(self, total_kwh, area_sqm):
        if area_sqm <= 0:
            raise ValueError("area_sqm must be above zero")
        return (total_kwh / area_sqm) * (365 / self._period_days)

    def compute_score(self, total_kwh, area_sqm):
        intensity = self.energy_intensity(total_kwh, area_sqm)
        if intensity == 0:
            return 100.0
        score = 100.0 * self._efficiency_benchmark / intensity
        return round(min(100.0, score), 2)

    def get_grade(self, score):
        for limit, letter in ((90, "A"), (75, "B"), (60, "C"), (40, "D")):
            if score >= limit:
                return letter
        return "E"


class AnomalyDetector:
    def __init__(self, threshold=3.0, min_samples=10):
        self._threshold = 3.0
        self._min_samples = 10
        self._mean = None
        self._std = None
        self.set_threshold(threshold)
        self.set_min_samples(min_samples)

    def fit(self, values):
        if len(values) < self._min_samples:
            raise ValueError("need at least " + str(self._min_samples) + " values")
        self._mean = mean(values)
        self._std = pstdev(values)

    def get_threshold(self):
        return self._threshold

    def get_min_samples(self):
        return self._min_samples

    def get_baseline(self):
        if self._mean is None:
            return None
        return round(self._mean, 2), round(self._std, 2)

    def set_threshold(self, value):
        if value <= 0:
            raise ValueError("threshold must be above zero")
        self._threshold = float(value)

    def set_min_samples(self, value):
        if value < 2:
            raise ValueError("min_samples must be at least 2")
        self._min_samples = int(value)

    def z_score(self, value):
        if self._mean is None:
            raise RuntimeError("call fit() first")
        if self._std == 0:
            return 0.0
        return (value - self._mean) / self._std

    def is_anomaly(self, value):
        return abs(self.z_score(value)) > self._threshold

    def detect(self, logs):
        found = []
        for row in logs:
            z = self.z_score(row["energy_consumed_kwh"])
            if abs(z) > self._threshold:
                found.append(dict(row, z_score=round(z, 2)))
        return found


class EnergyForecaster:

    def __init__(self, window=24, horizon=1):
        self._window = 24
        self._horizon = 1
        self._history = []
        self.set_window(window)
        self.set_horizon(horizon)

    def fit(self, history):
        if len(history) < self._window:
            raise ValueError("need at least " + str(self._window) + " values")
        self._history = [float(v) for v in history]

    def get_window(self):
        return self._window

    def get_horizon(self):
        return self._horizon

    def get_history(self):
        return list(self._history)

    def set_window(self, value):
        if value < 1:
            raise ValueError("window must be at least 1")
        self._window = int(value)

    def set_horizon(self, value):
        if value < 1:
            raise ValueError("horizon must be at least 1")
        self._horizon = int(value)

    def predict(self):
        if not self._history:
            raise RuntimeError("call fit() first")
        series = list(self._history)
        predictions = []
        for _ in range(self._horizon):
            nxt = mean(series[-self._window:])
            predictions.append(round(nxt, 2))
            series.append(nxt)
        return predictions


if __name__ == "__main__":
    base = datetime(2026, 10, 1)
    logs = [
        {
            "room_id": 1 + i % 2,
            "building_id": 1,
            "timestamp": base.replace(hour=i % 24, day=1 + i // 24),
            "energy_consumed_kwh": 5.0 + (i % 5) * 0.4,
            "indoor_temp": 21.0
        }
        for i in range(48)
    ]

    logs.append({
        "room_id": 1,
        "building_id": 1,
        "timestamp": base.replace(day=5),
        "energy_consumed_kwh": 40.0,
        "indoor_temp": 22.0
    })

    engine = AnalyticsEngine(0.30, 0.40, logs)
    print("Building:", engine.aggregate_by_building())

    calc = SustainabilityCalculator(efficiency_benchmark=100, period_days=30)
    score = calc.compute_score(engine.total_kwh(), area_sqm=50)
    print("Score:", score, calc.get_grade(score))

    detector = AnomalyDetector(threshold=3, min_samples=10)
    detector.fit([r["energy_consumed_kwh"] for r in logs[:-1]])
    print("Anomalies:", detector.detect(logs))

    forecaster = EnergyForecaster(window=24, horizon=3)
    forecaster.fit([r["energy_consumed_kwh"] for r in logs[:-1]])
    print("Forecast:", forecaster.predict())