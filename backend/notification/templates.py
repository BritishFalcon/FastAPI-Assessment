from enum import unique, Enum
import os

# BASE TEMPLATE TAKEN FROM
# https://github.com/leemunroe/responsive-html-email-template


@unique
class NotificationType(str, Enum):
    AI_RESPONSE = "ai_response"


def load_template(file: str) -> str:
    file_path = os.path.join(os.path.dirname(__file__), "templates", file)
    with open(file_path, "r") as file:
        return file.read()


TEMPLATES = {
    NotificationType.AI_RESPONSE: {
        "subject": "Your AI Summary is Ready!",
        "html": load_template("ai_response.html"),
    },
}
