import os
from dotenv import find_dotenv, set_key
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.erlang import ElixirLexer
from gradualelixir import module, cast
import sys
from gradualelixir.elixir_port import to_internal_representation, format_code, SyntacticLevel
from gradualelixir.exception import CommandException, SevereCommandException
from gradualelixir.utils import Bcolors


dotenv_path = find_dotenv()


def configure_command(arguments):
    if len(arguments) != 2:
        raise SevereCommandException("no option given for configuration")
    if arguments[0] not in ["-elixir-path", "-mix-path", "-working-dir"]:
        raise CommandException(f"{arguments[0]} is not a configurable option")

    set_key(dotenv_path, arguments[0][1:].replace("-", "_").upper(), arguments[1])


def print_command(arguments):
    if len(arguments) == 0:
        raise SevereCommandException("no input for <filename> given")

    name = arguments[0]
    working_dir = os.environ['WORKING_DIR']
    with open(f"{working_dir}/{name}", "r") as f:
        code = "\n".join(f.readlines())
        code = format_code(code)
    with open(f"{working_dir}/{name}", "w") as f:
        f.write(code)
    formatter = Terminal256Formatter(style='rrt')
    lex = ElixirLexer()
    print(highlight(code, lex, formatter))


def check_command(arguments):
    if len(arguments) == 0:
        raise SevereCommandException("no modality given for annotate")
    if arguments[0] not in ["-static", "-command"]:
        raise CommandException(f"{arguments[0]} is not a modality")
    if len(arguments) == 1:
        raise CommandException("no <filename> specified")
    modality, filename = arguments[0], arguments[1]

    path, name = os.path.split(filename)
    with open(f"{path}/{name}", "r") as f:
        code = "\n".join(f.readlines())
        mod = to_internal_representation(code, SyntacticLevel.module)
        code = format_code(str(mod))
    with open(f"{path}/{name}", "w") as f:
        f.write(code)

    formatter = Terminal256Formatter(style='rrt')
    lex = ElixirLexer()
    type_check_result = module.type_check(mod)
    if isinstance(type_check_result, module.TypeCheckErrors):
        print(f"{Bcolors.OKBLUE}Type check errors for module {mod.name}{Bcolors.ENDC}\n\n")
        for definition_key, errors in type_check_result.errors.items():
            print(f"     {Bcolors.OKBLUE}On {definition_key[0]}/{definition_key[1]}\n")
            print(errors.message(padding="    "))
    print(highlight(code, lex, formatter))


def annotate_command(arguments):
    if len(arguments) == 0:
        raise CommandException("no input for <filename> given")

    file_path = arguments[1]
    path, name = os.path.split(file_path)
    base_name, mime = name.split(".")

    with open(f"{path}/{base_name}_cast/{mime}", "r") as f:
        code = "\n".join(f.readlines())

    mod = to_internal_representation(code, syntactic_level=SyntacticLevel.module)
    type_check_result = module.type_check(mod)
    if isinstance(type_check_result, module.TypeCheckSuccess):
        print(type_check_result.message())

        annotated_code = cast.annotate_module(type_check_result)

        code = format_code(code)
        annotated_code = format_code(str(annotated_code))

        with open(f"{path}/{base_name}/{mime}", "w") as f:
            f.write(code)
        with open(f"{path}/{base_name}_cast/{mime}", "w") as f:
            f.write(annotated_code)


def help_command():
    print(
        "\nUsage:\n  gradualelixir <command> options\n\n"
        "Commands:\n"
        "  --configure (-elixir-path | -mix-path | -working-dir) <value>"
        "  --print <filename>     Prints an elixir source file to STDOUT \n"
        "  --check         Type checks a mini elixir file either in a static or gradual modality\n"
        "    (-static | -gradual)? <filename>\n"
        "  --annotate      Type checks a mini elixir file with path <filename>, "
        "and outputs its content annotated with types into output_filename or stdout\n"
        "    (-static | -gradual)? <filename> (-output <output_filename>)?\n"
        "  --help           Show help for commands.\n"
    )


def _main():
    if len(sys.argv[1:]) == 0:
        raise CommandException("no command selected")

    command, arguments = sys.argv[1], sys.argv[2:]

    if not command.startswith("--"):
        raise SevereCommandException(f"couldn't parse command command: {command}")
    command = command[2:]

    if command not in ["print", "configure", "check", "annotate", "help"]:
        raise CommandException(f"no such command: {command}")

    if command == "print":
        print_command(arguments)
    elif command == "configure":
        configure_command(arguments)
    elif command == "check":
        check_command(arguments)
    elif command == "annotate":
        annotate_command(arguments)
    elif command == "help":
        help_command()


def main():
    try:
        _main()
    except CommandException as ce:
        print(f"\n{ce.args[0]}")
        print("Usage:\n  gradualelixir <command> options\n")
    except SevereCommandException as ce:
        print(f"\n{ce.args[0]}\n")
        help_command()


if __name__ == '__main__':
    main()
