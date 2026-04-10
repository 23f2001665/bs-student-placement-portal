from .application import create_app
from .extensions import celery
from .tasks import export as export_tasks  # noqa: F401
from .tasks import send_email as send_email_tasks  # noqa: F401

app = create_app()

app.app_context().push()