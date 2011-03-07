from datetime import timedelta
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "username"
BROKER_PASSWORD = "password"
BROKER_VHOST = "molqueue"
CELERY_IMPORTS = ("tiling.tasks", )
CELERYD_OPTS="-B"
CELERYD_CONCURRENCY = 4
CELERY_RESULT_BACKEND = "amqp"
#CELERYD_LOG_FILE = "celery.log"
CELERYBEAT_SCHEDULE = {
    "runs-every-5-minutes": {
        "task": "tiling.tasks.ScanNewLayers",
        "schedule": timedelta(minutes=30)
    },
}
