import time
from datetime import datetime, date, UTC
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError

from db_setup import get_session
from models import SearchPhrase, Dynamics, DynamicsPoint
from yandex_wordstat_connector_v4 import YandexWordstatConnector
from logger import get_logger

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("YANDEX_WORDSTAT_TOKEN")
if not TOKEN:
    raise RuntimeError("не найден токен YANDEX_WORDSTAT_TOKEN в .env")

logger = get_logger(__name__)


def _to_date(d: object) -> date:
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return date.fromisoformat(d)
    raise ValueError(f"ожидалась дата в формате YYYY-MM-DD, получено: {d!r}")


def save_dynamics(
    phrases: List[str],
    period: str,
    from_date: str,
    to_date: Optional[str] = None,
    regions: Optional[List[int]] = None,
    devices: Optional[List[str]] = None,
    pause_seconds: float = 1.0,
):


    connector = YandexWordstatConnector(TOKEN)
    results = connector.get_dynamics_batch(
        phrases=phrases,
        period=period,
        from_date=from_date,
        to_date=to_date,
        regions=regions,
        devices=devices,
    )

    region_id = regions[0] if regions and len(regions) == 1 else None
    device = devices[0] if devices and len(devices) == 1 else None

    now = datetime.now(UTC).replace(tzinfo=None)

    base_from = _to_date(from_date)
    base_to = _to_date(to_date) if to_date else None

    with get_session() as session:
        for phrase in phrases:
            try:
                data = results.get(phrase)
                if not data or "ошибка" in data:
                    logger.error(
                        f"ошибка при получении динамики по фразе '{phrase}': "
                        f"{data.get('ошибка') if isinstance(data, dict) else 'нет данных'}"
                    )
                    continue

                series = data.get("dynamics", [])

                # вычисляю to_date, если не передали явно
                if base_to is None:
                    if series:
                        last_date = max(_to_date(p.get("date")) for p in series if p.get("date"))
                        computed_to = last_date
                    else:
                        computed_to = base_from
                else:
                    computed_to = base_to

                # создаю SearchPhrase
                search_phrase = session.query(SearchPhrase).filter_by(phrase=phrase).first()
                if not search_phrase:
                    search_phrase = SearchPhrase(phrase=phrase, created_at=now)
                    session.add(search_phrase)
                    session.flush()

                # создание Dynamics
                dynamics = Dynamics(
                    search_phrase_id=search_phrase.id,
                    requested_at=now,
                    from_date=base_from,
                    to_date=computed_to,
                    period=period,
                    region_id=region_id,
                    device=device,
                )
                session.add(dynamics)
                session.flush()

                # создание точки DynamicsPoint
                for pt in series:
                    pt_date = _to_date(pt.get("date"))
                    pt_count = int(pt.get("count", 0))
                    pt_share = float(pt.get("share", 0.0))

                    dp = DynamicsPoint(
                        dynamics_id=dynamics.id,
                        date=pt_date,
                        count=pt_count,
                        share=pt_share,
                    )
                    session.add(dp)

                logger.info(
                    f"сохранена динамика для '{phrase}' "
                    f"(period={period}, {base_from}–{computed_to}, region={region_id}, device={device}), "
                    f"точек={len(series)}"
                )

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
    logger.info(f"Введенные фразы: {phrases}")

    save_dynamics(
        phrases=phrases,
        period="weekly",
        from_date="2025-05-05",
        regions=[213],
        devices=["desktop"],
    )
