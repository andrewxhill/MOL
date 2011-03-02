from datetime import timedelta
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "username"
BROKER_PASSWORD = "password"
BROKER_VHOST = "molqueue"
CELERY_IMPORTS = ("tiling.tasks", )
CELERYD_CONCURRENCY = 4
CELERY_RESULT_BACKEND = "amqp"
#CELERYD_LOG_FILE = "celery.log"
CELERYBEAT_SCHEDULE = {
    "runs-every-30-seconds": {
        "task": "tiling.tasks.ScanNewLayers",
        "schedule": timedelta(seconds=3)
    },
}
