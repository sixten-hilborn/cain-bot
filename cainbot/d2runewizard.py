import requests
from .types import TerrorZone


class D2RunewizardClient:
    def __init__(self, contact_email: str):
        self.headers = {
            "D2R-Contact": contact_email,
            "D2R-Platform": "Discord",
            "D2R-Repo": "https://github.com/sixten-hilborn/cain-bot",
        }

    def get_terror_zone(self) -> TerrorZone:
        response = requests.get(
            "https://d2runewizard.com/api/trackers/terror-zone",
            headers=self.headers,
            timeout=10,
        )
        response.raise_for_status()

        json_data = response.json()
        return TerrorZone(name=json_data["currentTerrorZone"]["zone"])
