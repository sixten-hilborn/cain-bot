import requests
import logging
from .types import TerrorZone

logger = logging.getLogger(__name__)

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

        try:
            json_data = response.json()
        except ValueError:
            logger.error(
                f"Invalid JSON: status={response.status_code} content_type={response.headers.get('Content-Type')} body={response.text[:300]}",
            )
            raise
        return TerrorZone(name=json_data["currentTerrorZone"]["zone"])
