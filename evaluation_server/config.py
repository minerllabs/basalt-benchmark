import os


def get_database_url(use_postgres: bool):
    """
    Returns the correct DATABASE_URL (sqlite / postgres)
    """
    if use_postgres:
        try:
            return construct_postgres_url()
        except:
            pass

    return os.getenv("DATABASE_URL", "sqlite:///./local_database.db")


def construct_postgres_url():
    """
    Constructs the pg database url

    Raises:
        ValueError if all properties not configured
    """
    pg_db = os.getenv("POSTGRES_DB")
    pg_user = os.getenv("POSTGRES_USER")
    pg_password = os.getenv("POSTGRES_PASSWORD")
    pg_host = os.getenv("DATABASE_URL")

    if not pg_db or not pg_user or not pg_password or not pg_host:
        raise ValueError("POSTGRES not configured")

    return f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}/{pg_db}"


class Config:
    USE_POSTGRES = os.getenv("USE_POSTGRES", False) == "true"
    DATABASE_URL = get_database_url(USE_POSTGRES)

    # Any value other other than "local" would be treated as "s3"
    FILES_STORAGE_BACKEND = os.getenv("FILES_STORAGE_BACKEND", "local")

    AWS_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_KEY")
    AWS_S3_BUCKET_NAME = os.getenv("S3_BUCKET", "basalt-uploads")
    AWS_S3_BUCKET_KEY_PREFIX = os.getenv("S3_KEY_PREFIX", "episode/")
    AWS_S3_REGION_NAME = os.getenv("S3_REGION")
    AWS_S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT")

    # For local development purpose
    UPLOADS_DIR = os.getenv("UPLOADS_DIR", "static/uploads")
    UPLOADS_BASE_URI = os.getenv("UPLOADS_BASE_URI", "/static/uploads/")

    MATCH_EXPIRY_TIME_MINS = 30
    SESSION_EXPIRY_TIME_MINS = 30

    UNIQUE_SALT = os.getenv("UNIQUE_SALT")
    ANTIBOT_ENABLED = os.getenv("ANTIBOT_ENABLED", False) == "true"

    BASALT_TASKS = [
        "FindCave",
        "MakeWaterfall",
        "CreateVillageAnimalPen",
        "BuildVillageHouse",
    ]

    BASALT_ENV_NAMES = [
        "MineRLBasaltFindCave-v0",
        "MineRLBasaltMakeWaterfall-v0",
        "MineRLBasaltCreateVillageAnimalPen-v0",
        "MineRLBasaltBuildVillageHouse-v0",
    ]

    BASALT_ENV_NAME_TO_TASK = {
        "MineRLBasaltFindCave-v0": "FindCave",
        "MineRLBasaltMakeWaterfall-v0": "MakeWaterfall",
        "MineRLBasaltCreateVillageAnimalPen-v0": "CreateVillageAnimalPen",
        "MineRLBasaltBuildVillageHouse-v0": "BuildVillageHouse",
    }

    BASALT_ENV_NAMES = [
        "MineRLBasaltFindCave-v0",
        "MineRLBasaltMakeWaterfall-v0",
        "MineRLBasaltCreateVillageAnimalPen-v0",
        "MineRLBasaltBuildVillageHouse-v0",
    ]

    BASALT_ENV_TO_EXPECTED_SEEDS = {
        "MineRLBasaltFindCave-v0": [14169, 65101, 78472, 76379, 39802, 95099, 63686, 49077, 77533, 31703, 73365],
        "MineRLBasaltMakeWaterfall-v0": [95674, 39036, 70373, 84685, 91255, 56595, 53737, 12095, 86455, 19570, 40250],
        "MineRLBasaltCreateVillageAnimalPen-v0": [21212, 85236, 14975, 57764, 56029, 65215, 83805, 35884, 27406, 5681265, 20848],
        "MineRLBasaltBuildVillageHouse-v0": [52216, 29342, 67640, 73169, 86898, 70333, 12658, 99066, 92974, 32150, 78702],
    }


    EVAL_QUESTIONS_REQUIRED = os.getenv(
        "EVAL_QUESTIONS_REQUIRED", False) == "true"

    MATCH_BUFFER_SIZE = 10
    BUFFER_REFILL_THRESHOLD = 10

    DOMAIN_NAME = os.getenv("DOMAIN_NAME", "http://localhost:8000")
