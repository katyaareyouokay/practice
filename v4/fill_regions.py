from db_setup import get_session
from models import Region
from yandex_wordstat_connector_v4 import YandexWordstatConnector
from logger import get_logger
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("YANDEX_WORDSTAT_TOKEN")

if not TOKEN:
    raise RuntimeError("не найден токен YANDEX_WORDSTAT_TOKEN в .env")


logger = get_logger(__name__)

def fill_regions():
    connector = YandexWordstatConnector(token=TOKEN)

    try:
        regions_data = connector.get_regions()
        logger.info(f"получено {len(regions_data)} регионов")

        with get_session() as session:
            added = 0
            for region in regions_data:
                region_id = int(region["value"])
                label = region["label"]

                # есть ли уже такой регион в БД
                exists = session.query(Region).filter_by(id=region_id).first()
                if not exists:
                    session.add(Region(id=region_id, label=label))
                    added += 1

            session.commit()
            logger.info(f"добавлено {added} новых регионов в базу данных")

    except IntegrityError as e:
        logger.error(f"ошибка целостности при добавлении регионов: {e}")
    except Exception as e:
        logger.error(f"произошла ошибка при загрузке регионов: {e}")

if __name__ == "__main__":
    fill_regions()
