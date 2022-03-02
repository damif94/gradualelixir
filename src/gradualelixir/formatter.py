import os
import subprocess
import tempfile

from gradualelixir import PROJECT_PATH


def format_elixir_code(code: str) -> str:
    with open(f"{PROJECT_PATH}/format.ex", "w") as f:
        f.write(code)

    format_output = subprocess.run(
        ["mix", "format", f"{PROJECT_PATH}/format.ex"], capture_output=False
    )

    if error := format_output.stderr:
        raise Exception(error)

    with open(f"{PROJECT_PATH}/format.ex", "r") as f:
        text = "".join(f.readlines())
        return text
