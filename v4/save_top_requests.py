import time
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError

from db_setup import get_session
from models import SearchPhrase, TopRequest, TopRequestItem
from yandex_wordstat_connector_v4 import YandexWordstatConnector
from logger import get_logger

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("YANDEX_WORDSTAT_TOKEN")
if not TOKEN:
    raise RuntimeError("не найден токен YANDEX_WORDSTAT_TOKEN в .env")

logger = get_logger(__name__)


def _same_or_null_filter(column, value):
    return (column == value) if value is not None else column.is_(None)


def save_top_requests(
    phrases: List[str],
    regions: Optional[List[int]] = None,
    devices: Optional[List[str]] = None,
    pause_seconds: float = 1.0,
):

    connector = YandexWordstatConnector(TOKEN)
    results = connector.get_top_requests_batch(
        phrases, regions=regions, devices=devices, pause_seconds=pause_seconds
    )

    # поддерживает только один регион/девайс на запрос
    region_id = regions[0] if regions and len(regions) == 1 else None
    device = devices[0] if devices and len(devices) == 1 else None

    with get_session() as session:
        # границы текущего дня 
        now = datetime.utcnow()
        start_of_day = datetime.combine(now.date(), datetime.min.time())
        start_of_next_day = start_of_day + timedelta(days=1)

        for phrase in phrases:
            try:
                data = results.get(phrase)
                if not data or "ошибка" in data:
                    logger.error(
                        f"ошибка при получении данных по фразе '{phrase}': "
                        f"{data.get('ошибка') if isinstance(data, dict) else 'нет данных'}"
                    )
                    continue

                # search_phrases (upsert по тексту фразы)
                search_phrase = (
                    session.query(SearchPhrase).filter_by(phrase=phrase).first()
                )
                if not search_phrase:
                    search_phrase = SearchPhrase(phrase=phrase, created_at=now)
                    session.add(search_phrase)
                    session.flush()  # получаем id

                # проверяю, не сохраняли ли сегодня уже такую же выборку
                exists_today = (
                    session.query(TopRequest.id)
                    .filter(
                        TopRequest.search_phrase_id == search_phrase.id,
                        _same_or_null_filter(TopRequest.region_id, region_id),
                        _same_or_null_filter(TopRequest.device, device),
                        TopRequest.requested_at >= start_of_day,
                        TopRequest.requested_at < start_of_next_day,
                    )
                    .first()
                )

                if exists_today:
                    logger.info(
                        f"запрос по фразе '{phrase}' (region={region_id}, device={device}) "
                        f"уже сохранён за {now.date()} — пропускаю"
                    )
                    continue

                # top_requests (шапка)
                total_count = data.get("totalCount")
                top_request = TopRequest(
                    search_phrase_id=search_phrase.id,
                    requested_at=now,
                    region_id=region_id,
                    device=device,
                    total_count=total_count,
                )
                session.add(top_request)
                session.flush()  # нужен id для items

                # top_request_items (детализация)
                for item in data.get("topRequests", []):
                    tr_item = TopRequestItem(
                        top_request_id=top_request.id,
                        phrase=item.get("phrase"),
                        count=item.get("count"),
                    )
                    session.add(tr_item)

                logger.info(
                    f"сохранены topRequests для '{phrase}' "
                    f"(region={region_id}, device={device}), total_count={total_count}"
                )

                # пауза между фразами (чтобы не перегружать сервер)
                time.sleep(pause_seconds)

            except SQLAlchemyError as db_err:
                session.rollback()
                logger.error(f"DB error for phrase '{phrase}': {db_err}")
            except Exception as e:
                session.rollback()
                logger.error(f"unexpected error for phrase '{phrase}': {e}")

        session.commit()

    logger.info(f"обработка завершена: фраз — {len(phrases)}")


if __name__ == "__main__":
    # пример запуска
    raw_input = "купить телефон, пицца москва\nманикюр на дому"
    client = YandexWordstatConnector(TOKEN)
    phrases = client.phrases_to_list(raw_input)
    logger.info(f"введенные фразы: {phrases}")

    save_top_requests(phrases=phrases, regions=[213], devices=["phone"])
