import pyautogui
import requests


class HACommunicator:
    def __init__(self, url, token, entity_lst, button_status, lamp_status):
        self.URL = url
        self.HA_TOKEN = token

        self.ENTITY_LST = entity_lst

        self.BUTTON_STATUS = button_status
        self.LAMP_STATUS = lamp_status

        self.headers = {
            "Authorization": f"Bearer {self.HA_TOKEN}",
            "Content-Type": "application/json",
        }

        self.turn_on_url = f"{self.URL}/api/services/light/turn_on"
        self.turn_off_url = f"{self.URL}/api/services/light/turn_off"

    def turn_off(self):
        if self.URL and self.HA_TOKEN and self.ENTITY_LST:
            payload = {
                "entity_id": self.ENTITY_LST,
            }

            response = requests.post(self.turn_off_url, headers=self.headers, json=payload)

            # print("Statuscode:", response.status_code)
            # print("Response:", response.text)
            if response.text == "[]":
                self.LAMP_STATUS.lamp_status = False

    def screen_mode(self, position_lst):
        if self.BUTTON_STATUS:
            self.LAMP_STATUS.lamp_status = True

            for entity in self.ENTITY_LST:
                x, y = position_lst[self.ENTITY_LST.index(entity)].position
                r, g, b = pyautogui.pixel(x, y)

                payload = {
                    "entity_id": entity,
                    "rgb_color": [r, g, b],
                    "brightness": 255,
                    "transition": 0.5
                }

                response = requests.post(self.turn_on_url, headers=self.headers, json=payload)
                # print("Statuscode:", response.status_code)
                # print("Antwort:", response.text)

        else:
            if self.LAMP_STATUS.lamp_status:
                self.turn_off()

    def crazy_mode(self):
        if self.BUTTON_STATUS:
            self.LAMP_STATUS.lamp_status = True

            for entity in self.ENTITY_LST:
                x, y = pyautogui.position()
                r, g, b = pyautogui.pixel(x, y)

                payload = {
                    "entity_id": entity,
                    "rgb_color": [r, g, b],
                    "brightness": 255,
                    "transition": 0.2
                }

                response = requests.post(self.turn_on_url, headers=self.headers, json=payload)
                # print("Statuscode:", response.status_code)
                # print("Antwort:", response.text)
        else:
            if self.LAMP_STATUS.lamp_status:
                self.turn_off()

    def average_mode(self):
        if self.BUTTON_STATUS:
            self.LAMP_STATUS.lamp_status = True
            width, height = pyautogui.size()

            points = [
                (width // 4, height // 4),
                (3 * width // 4, height // 4),
                (width // 4, 3 * height // 4),
                (3 * width // 4, 3 * height // 4),
            ]

            colors = []
            for idx, (x, y) in enumerate(points, start=1):
                r, g, b = pyautogui.pixel(x, y)
                colors.append((r, g, b))

            n = len(colors)
            avg_r = sum(c[0] for c in colors) / n
            avg_g = sum(c[1] for c in colors) / n
            avg_b = sum(c[2] for c in colors) / n

            avg_color = (round(avg_r), round(avg_g), round(avg_b))
            for entity in self.ENTITY_LST:
                payload = {
                    "entity_id": entity,
                    "rgb_color": avg_color,
                    "brightness": 255,
                    "transition": 1
                }

                response = requests.post(self.turn_on_url, headers=self.headers, json=payload)
                # print("Statuscode:", response.status_code)
                # print("Antwort:", response.text)

        else:
            if self.LAMP_STATUS.lamp_status:
                self.turn_off()
