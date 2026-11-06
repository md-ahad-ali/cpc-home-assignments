"""
Subsystem 4: Recommendations & Reporting (FR4.1 - FR4.10)
Owner: MD Sakib Khan

Classes: AIRecommendation, AIService, Report, ReportManager
Each class has __init__, an initialize() method, and get/set methods.

AIService works with any client that has the OpenAI shape:
    client.chat.completions.create(model=..., messages=[...])
Without a client, it returns a fallback message (NFR4.8).
"""

import csv
import os
import re
import time
from datetime import datetime


class AIRecommendation:
    def __init__(self, rec_id, building_id, recommendation_text, estimated_savings_pct=0.0):
        self._id = rec_id
        self._building_id = building_id
        self._created_at = None
        self._recommendation_text = ""
        self._estimated_savings_pct = 0.0
        self.initialize()
        self.set_recommendation_text(recommendation_text)
        self.set_estimated_savings_pct(estimated_savings_pct)

    def initialize(self):
        self._created_at = datetime.now()

    # ---- getters ----
    def get_id(self):
        return self._id

    def get_building_id(self):
        return self._building_id

    def get_created_at(self):
        return self._created_at

    def get_recommendation_text(self):
        return self._recommendation_text

    def get_estimated_savings_pct(self):
        return self._estimated_savings_pct

    # ---- setters ----
    def set_recommendation_text(self, text):
        if not text or not text.strip():
            raise ValueError("recommendation text must not be empty")
        self._recommendation_text = text.strip()

    def set_estimated_savings_pct(self, value):
        value = float(value)
        if value < 0 or value > 100:
            raise ValueError("savings must be between 0 and 100")
        self._estimated_savings_pct = value


class AIService:
    FALLBACK_TEXT = "Recommendations are not available now. Please try again later."

    def __init__(self, api_key=None, model="gpt-4o-mini", max_retries=3, client=None):
        self._api_key = None
        self._model = model
        self._max_retries = 3
        self._base_delay = 1.0
        self._client = client
        self._cache = {}
        self.initialize(api_key)
        self.set_max_retries(max_retries)

    def initialize(self, api_key=None):
        """NFR4.2: read the key from the environment (.env) if none is given."""
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._cache = {}

    # ---- getters ----
    def get_model(self):
        return self._model

    def get_max_retries(self):
        return self._max_retries

    def get_base_delay(self):
        return self._base_delay

    def has_api_key(self):
        return bool(self._api_key)

    # ---- setters ----
    def set_model(self, model):
        if not model:
            raise ValueError("model must not be empty")
        self._model = model

    def set_max_retries(self, value):
        if value < 1:
            raise ValueError("max_retries must be at least 1")
        self._max_retries = int(value)

    def set_base_delay(self, seconds):
        if seconds < 0:
            raise ValueError("delay must not be negative")
        self._base_delay = float(seconds)

    def set_client(self, client):
        self._client = client

    # ---- behavior ----
    def format_prompt(self, building_name, area_sqm, total_kwh, cost_eur, carbon_kg):
        """FR4.2 and NFR4.6: use building data only, no personal data."""
        return (
            "Building: " + building_name + ", area " + str(area_sqm) + " sqm. "
            "Energy use: " + str(total_kwh) + " kWh, cost " + str(cost_eur)
            + " EUR, carbon " + str(carbon_kg) + " kg CO2. "
            "Give 3 short energy-saving tips. "
            "End with one line: SAVINGS: <number>%"
        )

    def call_openai_api(self, prompt):
        """Retry with backoff (NFR4.5). Return the fallback text if all tries fail."""
        if prompt in self._cache:  # NFR4.7
            return self._cache[prompt]
        if self._client is None:
            return AIService.FALLBACK_TEXT
        for attempt in range(self._max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = response.choices[0].message.content
                self._cache[prompt] = text
                return text
            except Exception:
                time.sleep(self._base_delay * (2 ** attempt))
        return AIService.FALLBACK_TEXT

    def parse_savings(self, text):
        """FR4.3: read the savings percent from the last line."""
        match = re.search(r"SAVINGS:\s*(\d+(?:\.\d+)?)\s*%", text)
        return float(match.group(1)) if match else 0.0

    def generate_recommendation(self, rec_id, building_id, prompt):
        """FR4.1: return an AIRecommendation object."""
        text = self.call_openai_api(prompt)
        return AIRecommendation(rec_id, building_id, text, self.parse_savings(text))


class Report:
    def __init__(self, report_id, building_id, title):
        self._id = report_id
        self._building_id = building_id
        self._title = ""
        self._created_at = None
        self._recommendations = []
        self.initialize()
        self.set_title(title)

    def initialize(self):
        self._created_at = datetime.now()
        self._recommendations = []

    # ---- getters ----
    def get_id(self):
        return self._id

    def get_building_id(self):
        return self._building_id

    def get_title(self):
        return self._title

    def get_created_at(self):
        return self._created_at

    def get_recommendations(self):
        return list(self._recommendations)

    # ---- setters ----
    def set_title(self, title):
        if not title or not title.strip():
            raise ValueError("title must not be empty")
        self._title = title.strip()

    def set_created_at(self, value):
        self._created_at = value

    def add_recommendation(self, recommendation):
        self._recommendations.append(recommendation)

    # ---- behavior ----
    def preview(self):
        """FR4.6: return the report as plain text."""
        lines = [self._title, "Created: " + self._created_at.strftime("%Y-%m-%d %H:%M"), ""]
        for rec in self._recommendations:
            lines.append("- " + rec.get_recommendation_text()
                         + " (savings " + str(rec.get_estimated_savings_pct()) + "%)")
        return "\n".join(lines)

    def export_csv(self, path):
        """FR4.8: write one row per recommendation."""
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["building_id", "created_at", "recommendation", "savings_pct"])
            for rec in self._recommendations:
                writer.writerow([
                    rec.get_building_id(),
                    rec.get_created_at().isoformat(),
                    rec.get_recommendation_text(),
                    rec.get_estimated_savings_pct(),
                ])
        return path

    def export_pdf(self, path):
        """FR4.7: needs a PDF library such as reportlab. Add it in the next step."""
        raise NotImplementedError("PDF export needs the reportlab package")


class ReportManager:
    def __init__(self):
        self._reports = []
        self._next_id = 1
        self.initialize()

    def initialize(self):
        self._reports = []
        self._next_id = 1

    # ---- getters ----
    def get_reports(self):
        return list(self._reports)

    def get_next_id(self):
        return self._next_id

    # ---- setters ----
    def set_next_id(self, value):
        if value < 1:
            raise ValueError("next id must be at least 1")
        self._next_id = int(value)

    # ---- behavior ----
    def create_report(self, building_id, title):
        """FR4.9: keep every report in the history."""
        report = Report(self._next_id, building_id, title)
        self._next_id += 1
        self._reports.append(report)
        return report

    def filter_reports(self, building_id=None, start=None, end=None):
        """FR4.10: filter by building and date range."""
        result = []
        for report in self._reports:
            if building_id is not None and report.get_building_id() != building_id:
                continue
            if start is not None and report.get_created_at() < start:
                continue
            if end is not None and report.get_created_at() > end:
                continue
            result.append(report)
        return result


if __name__ == "__main__":
    service = AIService()  # no client, so it returns the fallback text
    prompt = service.format_prompt("Main Hall", 1200, 317.2, 95.16, 126.88)
    rec = service.generate_recommendation(1, 1, prompt)

    manager = ReportManager()
    report = manager.create_report(1, "October Report")
    report.add_recommendation(rec)
    print(report.preview())
    print("Reports for building 1:", len(manager.filter_reports(building_id=1)))
