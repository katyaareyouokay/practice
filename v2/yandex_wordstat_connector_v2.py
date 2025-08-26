import requests
from typing import Optional, List, Dict, Any
import time

# константы для проверки
VALID_PERIODS = {"monthly", "weekly", "daily"}
VALID_DEVICES = {"all", "desktop", "phone", "tablet"}
MAX_REQUESTS_PER_RUN = 100

# класс подключения к wordstat
class YandexWordstatConnector:
    BASE_URL = "https://api.wordstat.yandex.net"

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Content-Type": "application/json;charset=utf-8",
            "Authorization": f"Bearer {self.token}"
        }
        self.valid_regions = self.get_valid_regions()

    # получение всех регионов
    def get_valid_regions(self) -> List[int]:
        url = f"{self.BASE_URL}/v1/getRegionsTree"
        response = requests.post(url, headers=self.headers, json={})
        if response.status_code == 200:
            regions_data = response.json()
            print("getRegionsTree:", regions_data)  # отладочный вывод
            ids = []
            for root in regions_data:  # обработка всех корней дерева
                ids.extend(self.extract_region_ids(root))
            print("получены ID регионов:", ids[:20], "...")  # смотрю, что там лежит по первым 20ти
            return ids
        else:
            raise Exception(f"ошибка получения регионов: {response.status_code} {response.text}")

    # извлечение id всех доступных регионов
    def extract_region_ids(self, data: Dict[str, Any]) -> List[int]:
        ids = []
        if "value" in data: #достаю только нужное - доступные номера регионов
            ids.append(int(data["value"]))
        if "children" in data and data["children"]:
            for child in data["children"]:
                ids.extend(self.extract_region_ids(child))
        return ids

    # валидация устройств
    def validate_devices(self, devices: Optional[List[str]]) -> bool:
        if not devices:
            return True
        return all(device in VALID_DEVICES for device in devices)

    # валидация периода
    def validate_period(self, period: str) -> bool:
        return period in VALID_PERIODS

    # валидация регионов
    def validate_regions(self, regions: Optional[List[int]]) -> bool:
        if not regions:
            return True
        return all(region_id in self.valid_regions for region_id in regions)

    # получение запросов topRequests
    def get_top_requests(
        self,
        phrase: str,
        regions: Optional[List[int]] = None,
        devices: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/v1/topRequests"
        payload = {"phrase": phrase}
        if regions:
            if not self.validate_regions(regions):
                raise ValueError("неверные ID регионов")
            payload["regions"] = regions
        if devices:
            if not self.validate_devices(devices):
                raise ValueError("неверные значения устройств")
            payload["devices"] = devices

        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"ошибка при получении топов: {response.status_code} {response.text}")

    # получение запросов dynamics
    def get_dynamics(
        self,
        phrase: str,
        period: str,
        from_date: str,
        to_date: Optional[str] = None,
        regions: Optional[List[int]] = None,
        devices: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if not self.validate_period(period):
            raise ValueError(f"неверный период: {period}")
        if not self.validate_devices(devices):
            raise ValueError("неверные значения устройств")
        if not self.validate_regions(regions):
            raise ValueError("неверные ID регионов")

        url = f"{self.BASE_URL}/v1/dynamics"
        payload = {
            "phrase": phrase,
            "period": period,
            "fromDate": from_date
        }
        if to_date:
            payload["toDate"] = to_date
        if regions:
            payload["regions"] = regions
        if devices:
            payload["devices"] = devices

        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"ошибка при получении динамики: {response.status_code} {response.text}")

    # загрузка динамики по фразам
    def get_dynamics_batch(
        self,
        phrases: List[str],
        period: str,
        from_date: str,
        to_date: Optional[str] = None,
        regions: Optional[List[int]] = None,
        devices: Optional[List[str]] = None,
        pause_seconds: float = 1.0
    ) -> Dict[str, Dict[str, Any]]:
        if len(phrases) > MAX_REQUESTS_PER_RUN:
            raise ValueError(f"слишком много фраз — максимум {MAX_REQUESTS_PER_RUN}!")  # чтобы проходило по квоте

        results = {}
        success_count = 0
        error_count = 0

        for phrase in phrases:
            try:
                print(f"запрос данных по фразе: {phrase}")
                data = self.get_dynamics(
                    phrase=phrase,
                    period=period,
                    from_date=from_date,
                    to_date=to_date,
                    regions=regions,
                    devices=devices
                )
                results[phrase] = data
                success_count += 1
            except Exception as e:
                print(f"ошибка при фразе '{phrase}': {e}")
                results[phrase] = {"error": str(e)}
                error_count += 1
            time.sleep(pause_seconds)

        print(f"\n запросы завершены: успешно — {success_count}, с ошибками — {error_count}")
        return results

    # универсальная валидация параметров
    def validate_inputs(
        self,
        period: Optional[str] = None,
        regions: Optional[List[int]] = None,
        devices: Optional[List[str]] = None
    ) -> None:
        if period and not self.validate_period(period):
            raise ValueError(f"неверный период: {period}")
        if devices and not self.validate_devices(devices):
            raise ValueError("неверные значения устройств")
        if regions and not self.validate_regions(regions):
            raise ValueError("неверные ID регионов")

    # универсальный запуск batch-запросов
    def run_batch_requests(
        self,
        phrases: List[str],
        mode: str,
        *,
        period: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        regions: Optional[List[int]] = None,
        devices: Optional[List[str]] = None,
        pause_seconds: float = 1.0
    ) -> Dict[str, Any]:
        self.validate_inputs(period=period, regions=regions, devices=devices)

        if mode == "dynamics":
            if not all([period, from_date]):
                raise ValueError("для режима 'dynamics' нужны period и from_date")
            return self.get_dynamics_batch(
                phrases=phrases,
                period=period,
                from_date=from_date,
                to_date=to_date,
                regions=regions,
                devices=devices,
                pause_seconds=pause_seconds
            )
        elif mode == "top":
            results = {}
            for phrase in phrases:
                try:
                    print(f"запрос top по фразе: {phrase}")
                    result = self.get_top_requests(
                        phrase=phrase,
                        regions=regions,
                        devices=devices
                    )
                    results[phrase] = result
                except Exception as e:
                    print(f"ошибка при фразе '{phrase}': {e}")
                    results[phrase] = {"error": str(e)}
                time.sleep(pause_seconds)
            return results
        else:
            raise ValueError("неизвестный режим — только 'dynamics' или 'top'")
