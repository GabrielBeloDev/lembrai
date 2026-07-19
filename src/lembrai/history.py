Message = dict[str, object]

MAX_MESSAGES = 40


def trimmed(history: list[Message], max_messages: int = MAX_MESSAGES) -> list[Message]:
    # slicing with -0 would return the whole list instead of nothing
    if max_messages == 0:
        return []
    return history[-max_messages:]
