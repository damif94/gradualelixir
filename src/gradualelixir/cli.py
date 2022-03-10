import os
import sys

from dotenv import find_dotenv, set_key
from gradualelixir import cast, module
from gradualelixir.elixir_port import SyntacticLevel, format_code, to_internal_representation
from gradualelixir.exception import CommandError, SevereCommandError
from gradualelixir.utils import Bcolors
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.erlang import ElixirLexer

dotenv_path = find_dotenv()


def configure_command(arguments):
    if len(arguments) != 2:
        raise SevereCommandError('no option given for configuration')
    if arguments[0] not in ['-elixir-path', '-mix-path', '-working-dir']:
        raise CommandError(f'{arguments[0]} is not a configurable option')

    set_key(dotenv_path, arguments[0][1:].replace('-', '_').upper(), arguments[1])


def print_command(arguments):
    if len(arguments) == 0:
        raise SevereCommandError('no input for <filename> given')

    name = arguments[0]
    working_dir = os.environ['WORKING_DIR']
    with open(f'{working_dir}/{name}', 'r') as f:
        code = '\n'.join(f.readlines())
        code = format_code(code)
    with open(f'{working_dir}/{name}', 'w') as f:
        f.write(code)
    formatter = Terminal256Formatter(style='rrt')
    lex = ElixirLexer()
    print(highlight(code, lex, formatter))


def check_command(arguments):
    if len(arguments) == 0:
        raise SevereCommandError('no modality given for annotate')
    if arguments[0] not in ['-static', '-command']:
        raise CommandError(f'{arguments[0]} is not a modality')
    if len(arguments) == 1:
        raise CommandError('no <filename> specified')
    static = arguments[0] == '-static'
    filename = arguments[1]

    path, name = os.path.split(filename)
    with open(f'{path}/{name}', 'r') as f:
        code = '\n'.join(f.readlines())
        mod = to_internal_representation(code, SyntacticLevel.module)
        code = format_code(str(mod))
    with open(f'{path}/{name}', 'w') as f:
        f.write(code)

    formatter = Terminal256Formatter(style='rrt')
    lex = ElixirLexer()
    type_check_result = module.type_check_module(mod, static)
    if isinstance(type_check_result, module.CollectResultErrors):
        print(f'{Bcolors.OKBLUE}Definitions collection errors for module {mod.name}{Bcolors.ENDC}\n')
        print(type_check_result)
        return

    if isinstance(type_check_result, module.TypeCheckErrors):
        print(f'{Bcolors.OKBLUE}Type check errors for module {mod.name}{Bcolors.ENDC}\n')
        print(type_check_result)
        return

    print(type_check_result.message())
    print(highlight(code, lex, formatter))


def annotate_command(arguments):
    if len(arguments) == 0:
        raise SevereCommandError('no modality given for annotate')
    if arguments[0] not in ['-static', '-command']:
        raise CommandError(f'{arguments[0]} is not a modality')
    if len(arguments) == 1:
        raise CommandError('no <filename> specified')
    static = arguments[0] == '-static'
    filename = arguments[1]

    path, name = os.path.split(filename)
    base_name, mime = name.split('.')
    with open(f'{path}/{base_name}.{mime}', 'r') as f:
        code = '\n'.join(f.readlines())

    mod = to_internal_representation(code, syntactic_level=SyntacticLevel.module)
    type_check_result = module.type_check_module(mod, static)
    if isinstance(type_check_result, module.TypeCheckSuccess):
        print(type_check_result.message())

        annotated_code = cast.annotate_module(type_check_result)
        print(
            f'{Bcolors.OKBLUE}An annotated version of {type_check_result.module.name} module was '
            f'generated in {base_name}_cast.{mime}{Bcolors.ENDC}\n'
        )
        code = format_code(code)
        annotated_code = format_code(str(annotated_code))

        with open(f'{path}/{base_name}.{mime}', 'w') as f:
            f.write(code)

        with open(f'{path}/{base_name}_cast.{mime}', 'w') as f:
            f.write(annotated_code)


def help_command():
    print(
        '\nUsage:\n  gradualelixir <command> options\n\n'
        'Commands:\n'
        '  --configure (-elixir-path | -mix-path | -working-dir) <value>\n'
        '  --print <filename>\n'
        '    prints an elixir source file to STDOUT \n'
        '  --check (-static | -gradual)? <filename>\n'
        '    type checks a mini elixir file either in a static or gradual modality\n'
        '  --annotate (-static | -gradual)? <filename> (-output <output_filename>)?\n'
        '    type checks a mini elixir file with path <filename>, and outputs its content '
        'annotated with types into output_filename or stdout\n'
        '  --help\n'
        '    shows help for commands.\n'
    )


def _main():
    if len(sys.argv[1:]) == 0:
        raise CommandError('no command selected')

    command, arguments = sys.argv[1], sys.argv[2:]

    if not command.startswith('--'):
        raise SevereCommandError(f"couldn't parse command command: {command}")
    command = command[2:]

    if command not in ['print', 'configure', 'check', 'annotate', 'help']:
        raise CommandError(f'no such command: {command}')

    if command == 'print':
        print_command(arguments)
    elif command == 'configure':
        configure_command(arguments)
    elif command == 'check':
        check_command(arguments)
    elif command == 'annotate':
        annotate_command(arguments)
    elif command == 'help':
        help_command()


def main():
    try:
        _main()
    except CommandError as ce:
        print(f'\n{ce.args[0]}')
        print('Usage:\n  gradualelixir <command> options\n')
    except SevereCommandError as ce:
        print(f'\n{ce.args[0]}\n')
        help_command()


if __name__ == '__main__':
    main()
