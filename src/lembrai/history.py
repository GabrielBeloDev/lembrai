Message = dict[str, str]

MAX_MESSAGES = 40


def trimmed(history: list[Message], max_messages: int = MAX_MESSAGES) -> list[Message]:
    if len(history) <= max_messages:
        return history
    return history[-max_messages:]
