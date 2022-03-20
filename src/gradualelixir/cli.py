import os
import sys

from dotenv import find_dotenv, set_key
from gradualelixir import cast, module
from gradualelixir.elixir_port import (
    SyntacticLevel,
    format_code,
    to_internal_representation,
)
from gradualelixir.exception import CommandError, SevereCommandError
from gradualelixir.utils import Bcolors
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.erlang import ElixirLexer

dotenv_path = find_dotenv()


def configure_command(arguments):
    if len(arguments) != 2:
        raise SevereCommandError("no option given for configuration")
    if arguments[0] not in ["-elixir-path", "-working-dir"]:
        raise CommandError(f"{arguments[0]} is not a configurable option")

    set_key(dotenv_path, arguments[0][1:].replace("-", "_").upper(), arguments[1])


def print_command(arguments):
    if len(arguments) == 0:
        raise SevereCommandError("no input for <filename> given")

    name = arguments[0]
    working_dir = os.environ["WORKING_DIR"]
    with open(f"{working_dir}/{name}", "r") as f:
        code = "\n".join(f.readlines())
        code = format_code(code)
    with open(f"{working_dir}/{name}", "w") as f:
        f.write(code)
    formatter = Terminal256Formatter(style="rrt")
    lex = ElixirLexer()
    print(highlight(code, lex, formatter))


def check_command(arguments):
    if len(arguments) == 0:
        raise SevereCommandError("no modality given for annotate")
    if arguments[0] not in ["-static", "-gradual"]:
        raise CommandError(f"{arguments[0]} is not a modality")
    if len(arguments) == 1:
        raise CommandError("no <filename> specified")
    static = arguments[0] == "-static"
    filename = arguments[1]

    base_path = os.path.join(os.environ.get("WORKING_DIR", ""), "")
    with open(f"{base_path}{filename}", "r") as f:
        code = "\n".join(f.readlines())
        mod = to_internal_representation(code, SyntacticLevel.module)
        code = format_code(str(mod))
    with open(f"{base_path}{filename}", "w") as f:
        f.write(code)

    type_check_result = module.type_check(mod, static)
    if isinstance(type_check_result, module.CollectResultErrors):
        print(f"{Bcolors.OKBLUE}Definitions collection errors for module {mod.name}{Bcolors.ENDC}\n")
        print(type_check_result)
        return

    if isinstance(type_check_result, module.TypeCheckErrors):
        print(f"{Bcolors.OKBLUE}Type check errors for module {mod.name}{Bcolors.ENDC}\n")
        print(type_check_result)
        return

    print(type_check_result.message())


def annotate_types_command(arguments):
    if len(arguments) == 0:
        raise SevereCommandError("no modality given for annotate")
    if arguments[0] not in ["-static", "-gradual"]:
        raise CommandError(f"{arguments[0]} is not a modality")
    if len(arguments) == 1:
        raise CommandError("no <filename> specified")
    filename = arguments[1]
    static = arguments[0] == "-static"

    base_path = os.path.join(os.environ.get("WORKING_DIR", ""), "")
    base_name, mime = filename.split(".")
    with open(f"{base_path}{base_name}.{mime}", "r") as f:
        code = "".join(f.readlines())

    mod = to_internal_representation(code, syntactic_level=SyntacticLevel.module)
    type_check_result = module.type_check(mod, static=static)
    if isinstance(type_check_result, module.CollectResultErrors):
        print(f"{Bcolors.OKBLUE}Definitions collection errors for module {mod.name}{Bcolors.ENDC}\n")
        print(type_check_result)
        return

    if isinstance(type_check_result, module.SpecsRefinementErrors):
        print(f"{Bcolors.OKBLUE}Definitions collection errors for module {mod.name}{Bcolors.ENDC}\n")
        print(type_check_result)
        return

    if isinstance(type_check_result, module.TypeCheckErrors):
        print(f"{Bcolors.OKBLUE}Type check errors for module {mod.name}{Bcolors.ENDC}\n")
        print(type_check_result)
        return

    print(type_check_result.message())
    annotated_code = str(cast.annotate_module(type_check_result, casts=False))
    print(
        f"{Bcolors.OKBLUE}An annotated version of {type_check_result.module.name} module was "
        f"generated in {base_name}_types_{'static' if static else 'gradual'}.{mime}{Bcolors.ENDC}\n"
    )
    formatted_code = format_code(code)
    formatted_annotated_code = format_code(annotated_code)

    with open(f"{base_path}{base_name}.{mime}", "w") as f:
        f.write(formatted_code)

    with open(f"{base_path}{base_name}_types_{'static' if static else 'gradual'}.{mime}", "w") as f:
        f.write(formatted_annotated_code)


def annotate_casts_command(arguments):
    if len(arguments) == 0:
        raise CommandError("no <filename> specified")
    filename = arguments[0]

    base_path = os.path.join(os.environ.get("WORKING_DIR", ""), "")
    base_name, mime = filename.split(".")
    with open(f"{base_path}{base_name}.{mime}", "r") as f:
        code = "".join(f.readlines())

    mod = to_internal_representation(code, syntactic_level=SyntacticLevel.module)
    type_check_result = module.type_check(mod, static=False)
    if isinstance(type_check_result, module.CollectResultErrors):
        print(f"{Bcolors.OKBLUE}Definitions collection errors for module {mod.name}{Bcolors.ENDC}\n")
        print(type_check_result)
        return

    if isinstance(type_check_result, module.SpecsRefinementErrors):
        print(f"{Bcolors.OKBLUE}Definitions collection errors for module {mod.name}{Bcolors.ENDC}\n")
        print(type_check_result)
        return

    if isinstance(type_check_result, module.TypeCheckErrors):
        print(f"{Bcolors.OKBLUE}Type check errors for module {mod.name}{Bcolors.ENDC}\n")
        print(type_check_result)
        return

    print(type_check_result.message())

    annotated_code = str(cast.annotate_module(type_check_result, casts=True))
    print(
        f"{Bcolors.OKBLUE}An annotated version of {type_check_result.module.name} module was "
        f"generated in {base_name}_cast.{mime}{Bcolors.ENDC}\n"
    )
    formatted_code = format_code(code)
    formatted_annotated_code = format_code(annotated_code)

    with open(f"{base_path}{base_name}.{mime}", "w") as f:
        f.write(formatted_code)

    with open(f"{base_path}{base_name}_cast.{mime}", "w") as f:
        f.write(formatted_annotated_code)


def help_command():
    print(
        "\nUsage:\n  gradualelixir <command> options\n\n"
        "Commands:\n"
        "  --configure (-elixir-path | -working-dir) <value>\n"
        "    sets the variables needed by the other commands\n"
        "  --print <filename>\n"
        "    prints an elixir source file to standard output \n"
        "  --check (-static | -gradual) <filename>\n"
        "    type checks a mini elixir file either in a static or gradual modality\n"
        "  --annotate-types (-static | -gradual) <filename> (-output <output_filename>)?\n"
        "    type checks a mini elixir file with path <filename>, and outputs its content annotated with types\n"
        "  --annotate-casts <filename> (-output <output_filename>)?\n"
        "    gradually type checks a mini elixir file with path <filename>, and outputs its "
        "content after inserting casts\n"
        "  --run <filename>\n"
        "    annotated with types into output_filename or standard output\n"
        "  --help\n"
        "    shows help for commands.\n"
    )


def run_command(arguments):
    import pty
    import shutil

    base_path = os.path.join(os.environ.get("WORKING_DIR", ""), "")
    filename = os.path.join(base_path, arguments[0])
    mix_project_path = os.path.join(os.environ.get("PROJECT_PATH", ""), "elixir_port")
    shutil.copy(filename, os.path.join(mix_project_path, ".iex.exs"))
    os.chdir(mix_project_path)
    pty.spawn(["iex", "--erl", "-kernel shell_history enabled", "-S", "mix"])
    os.remove(".iex.exs")


def _main():
    if len(sys.argv[1:]) == 0:
        raise CommandError("no command selected")

    command, arguments = sys.argv[1], sys.argv[2:]

    if not command.startswith("--"):
        raise SevereCommandError(f"couldn't parse command command: {command}")
    command = command[2:]

    if command not in ["print", "configure", "check", "annotate-types", "annotate-casts", "run", "help"]:
        raise CommandError(f"no such command: {command}")

    if command == "print":
        print_command(arguments)
    elif command == "configure":
        configure_command(arguments)
    elif command == "check":
        check_command(arguments)
    elif command == "annotate-types":
        annotate_types_command(arguments)
    elif command == "annotate-casts":
        annotate_casts_command(arguments)
    elif command == "run":
        run_command(arguments)
    elif command == "help":
        help_command()


def main():
    try:
        _main()
    except CommandError as ce:
        print(f"\n{ce.args[0]}")
        print("Usage:\n  gradualelixir <command> options\n")
    except SevereCommandError as ce:
        print(f"\n{ce.args[0]}\n")
        help_command()
    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    main()
