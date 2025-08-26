from yandex_wordstat_connector_v3 import YandexWordstatConnector

def test_batch_run():
    token = "y0__xChkf2jCBjN7RAgvfHo4xMASAdtzxQZ7n2PNhhK0qGEcQoMbg"

    client = YandexWordstatConnector(token=token)

    batch = [
        {
            "method": "dynamics",
            "payload": {
                "phrase": "купить ноутбук",
                "period": "weekly",
                "from_date": "2024-02-05",
                "to_date": "2024-04-07",
                "regions": [213],
                "devices": ["all"]
            }
        },
        {
            "method": "topRequests",
            "payload": {
                "phrase": "котики",
                "regions": [2],
                "devices": ["desktop"]
            }
        },
        {
            "method": "topRequests",
            "payload": {
                "phrase": "!приют для (собак|кошек)",
                "regions": [213],
                "devices": ["phone"]
            }
        },
        {
            "method": "dynamics",
            "payload": {
                "phrase": "заказать пиццу",
                "period": "monthly",
                "from_date": "2024-05-01",
                "to_date": "2024-12-31",
                "regions": [213],
                "devices": ["all"]
            }
        },
        {
            "method": "dynamics",
            "payload": {
                "phrase": "заказать пиццу",
                "period": "daily",
                "from_date": "2025-05-30",
                "regions": [4],
                "devices": ["all"]
            }
        }
    ]

    results = client.run_batch_requests(batch)

    for i, result in enumerate(results):
        print(f"\nРезультат запроса #{i+1}:\n", result)

# обязательный вызов при запуске скрипта
if __name__ == "__main__":
    test_batch_run()
