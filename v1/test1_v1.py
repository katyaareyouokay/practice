from yandex_wordstat_connector_v1 import YandexWordstatConnector

TOKEN = "y0__xChkf2jCBjN7RAgvfHo4xMASAdtzxQZ7n2PNhhK0qGEcQoMbg"

client = YandexWordstatConnector(TOKEN)

# тест запроса топа
top_data = client.get_top_requests(
    phrase="купить телефон",
    regions=[213],  # Москва
    devices=["desktop"]
)
print("Топы:", top_data)

# тест запроса динамики
dyn_data = client.get_dynamics(
    phrase="купить телефон",
    period="monthly",
    from_date="2025-05-01",
    to_date="2025-06-30",
    regions=[213],
    devices=["all"]
)
print("Динамика:", dyn_data)
