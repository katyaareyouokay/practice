from yandex_wordstat_connector_v2 import YandexWordstatConnector

TOKEN = "y0__xChkf2jCBjN7RAgvfHo4xMASAdtzxQZ7n2PNhhK0qGEcQoMbg"

client = YandexWordstatConnector(TOKEN)


phrases = ["купить телефон", "пицца москва", "маникюр на дому"]
batch_data = client.get_dynamics_batch(
    phrases=phrases,
    period="monthly",
    from_date="2025-05-01",
    to_date="2025-06-30",
    regions=[213],
    devices=["all"]
)

for phrase, result in batch_data.items():
    print(f"{phrase}: {result}")
