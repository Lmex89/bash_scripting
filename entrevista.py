from typing import List
from functools import wraps

STRING_INPUT = "palabra"

def format_dict_tuple(func):
    @wraps(func)
    def wrapper(*args, **kwargs) -> List[tuple[str, int]]:
        result = func(*args, **kwargs)

        if not isinstance(result, dict):
            raise ValueError("Decorated function must return a dict")

        return list(result.items())
    return wrapper


def count_string(string_input: str) -> dict[str, int]:
    if not isinstance(string_input, str):
        raise ValueError(f"input '{string_input}' is not a string MUST BE string")

    if not string_input:
        return {}

    contador: dict[str, int] = {}

    for char in string_input:
        contador[char] = contador.get(char, 0) + 1
    return contador


# Call format_dict_tuple inline without @ symbol
count_string_formatted = format_dict_tuple(count_string)
result = count_string_formatted(STRING_INPUT)
print(result)
# [('p', 1), ('a', 3), ('l', 1), ('b', 1), ('r', 1)]
