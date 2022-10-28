import requests
import re


class D2RunewizardClient():
    @staticmethod
    def get_terror_zone():
        try:
            response = requests.get(
                'https://d2runewizard.com/api/terror-zone',
                params=D2RunewizardClient.get_api_token_params(),
                timeout=10)
            response.raise_for_status()

            return response.json()
        except Exception as err:
            print(f'[TerrorZone] D2Runewizard API Error: {err}')
            return D2RunewizardClient.get_terror_zone_from_html()

    @staticmethod
    def get_terror_zone_from_html():
        try:
            response = requests.get('https://d2runewizard.com/terror-zone-tracker', timeout=10)
            response.raise_for_status()

            pattern = '''<h2 class=\\"terror-zone-tracker_currentZone[A-Za-z_\\- ]+\\">([A-Za-z' ]+)<\\/h2>'''
            match = re.search(pattern, response.text)
            if match is None:
                return None

            return {"terrorZone": {"zone": match.group(1)}}
        except Exception as err:
            print(f'[TerrorZone] D2Runewizard API Error: {err}')
            return None

    @staticmethod
    def get_api_token_params():
        payload = {}
        return payload
