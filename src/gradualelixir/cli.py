import logging
import os
import subprocess

import click
import pytest
from dotenv import find_dotenv, get_key, set_key
from gradualelixir import cast, module
from gradualelixir.elixir_port import SyntacticLevel, ast_transform, format_code, run
from gradualelixir.exception import ElixirProcessError
from gradualelixir.utils import Bcolors
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.erlang import ElixirLexer

dotenv_path = find_dotenv()

logger = logging.getLogger("dotenv.main")
logger.disabled = True


class ClickWorkingDirAwarePath(click.Path):
    """a hacky version of click.Path that does the validation logic
    against the WORKING_DIR environment variable"""

    def convert(self, *args, **kwargs):
        original_path = os.getcwd()
        if not bool(working_dir := get_key(dotenv_path, "WORKING_DIR")):
            self.fail("The WORKING_DIR variable is not configured. Please configure!")
        os.chdir(working_dir)
        out = super(ClickWorkingDirAwarePath, self).convert(*args, **kwargs)
        os.chdir(original_path)
        return out


@click.group()
def cli():
    pass


@cli.command("configure", short_help="sets the variables needed by the other commands")
@click.option("--elixir-path", type=click.Path(exists=True, file_okay=True))
@click.option("--working-dir", type=click.Path(exists=True, dir_okay=True))
def configure_command(elixir_path, working_dir):
    if bool(get_key(dotenv_path, "DOCKER")):
        raise click.ClickException("This command is not available when running through docker\n")
    if elixir_path is not None:
        set_key(dotenv_path, "ELIXIR_PATH", elixir_path)
    if working_dir is not None:
        set_key(dotenv_path, "WORKING_DIR", working_dir)


@cli.command("print", short_help="prints a linted version of the mini elixir source file <filename> to standard output")
@click.argument("filename", metavar="<filename>", type=ClickWorkingDirAwarePath(exists=True, file_okay=True))
def print_command(filename):
    working_dir = get_key(dotenv_path, "WORKING_DIR")
    with open(f"{working_dir}/{filename}", "r") as f:
        code = "\n".join(f.readlines())
        code = format_code(code)
    with open(f"{working_dir}/{filename}", "w") as f:
        f.write(code)
    formatter = Terminal256Formatter(style="rrt")
    lex = ElixirLexer()
    print(highlight(code, lex, formatter))


@cli.command(
    "type_check",
    short_help=(
        "gradually type checks a mini elixir file with path <filename>, " "optionally generating an annotated version"
    ),
)
@click.option("--gradual", is_flag=True, default=False, help="Used to toggle the type checker with the gradual modality.")
@click.option(
    "--annotate",
    default=None,
    type=click.Choice(["types", "casts"]),
    help="Generates an annotated version of <filename> and optionally annotates it with types or casts.",
)
@click.argument("filename", metavar="<filename>", type=ClickWorkingDirAwarePath(exists=True, file_okay=True))
def type_check_command(gradual, annotate, filename):
    casts = annotate == "casts"
    annotate = bool(annotate)
    base_path = os.path.join(get_key(dotenv_path, "WORKING_DIR"), "")
    base_name, mime = filename.split(".")

    with open(f"{base_path}{base_name}.{mime}", "r") as f:
        code = "".join(f.readlines())

    try:
        mod, ok = ast_transform(code, syntactic_level=SyntacticLevel.module)
        if not ok:
            print(f"{Bcolors.FAIL}Failed to run because the file couldn't be parsed as elixir code from the fragment{Bcolors.ENDC}\n")
            return
    except ElixirProcessError as e:
        raise click.ClickException(e.args[0])

    type_check_result = module.type_check(mod, static=not gradual)
    if isinstance(type_check_result, module.CollectSpecsResultErrors):
        print(f"{Bcolors.OKBLUE}Definitions collection errors for module {mod.name}{Bcolors.ENDC}\n")
        print(type_check_result)
        return

    if isinstance(type_check_result, module.TypeCheckErrors):
        print(f"{Bcolors.OKBLUE}Type check errors for module {mod.name}{Bcolors.ENDC}\n")
        print(type_check_result)
        return

    print(type_check_result.message())

    if not annotate:
        return

    annotated_code = str(cast.translate_module(type_check_result, casts=casts))
    print(
        f"{Bcolors.OKBLUE}An annotated version of {type_check_result.module.name} module was "
        f"generated in {base_name}_{'casts' if casts else 'types'}.{mime}{Bcolors.ENDC}\n"
    )
    formatted_code = format_code(code)
    formatted_annotated_code = format_code(annotated_code)

    with open(f"{base_path}{base_name}.{mime}", "w") as f:
        f.write(formatted_code)

    with open(f"{base_path}{base_name}_{'casts' if casts else 'types'}.{mime}", "w") as f:
        f.write(formatted_annotated_code)


@cli.command("run", short_help="runs a module's main/0 declaration")
@click.option("--gradual", is_flag=True, default=False, help="Used to toggle the gradual evaluation semantics.")
@click.argument("filename", metavar="<filename>", type=ClickWorkingDirAwarePath(exists=True, file_okay=True))
def run_command(filename, gradual):
    base_path = os.path.join(get_key(dotenv_path, "WORKING_DIR"), "")
    base_name, mime = filename.split(".")
    with open(f"{base_path}{base_name}.{mime}", "r") as f:
        code = "".join(f.readlines())

    try:
        mod, ok = ast_transform(code, syntactic_level=SyntacticLevel.module)
        if not ok:
            print(f"{Bcolors.FAIL}Failed to run because the file couldn't be parsed as elixir code from the fragment{Bcolors.ENDC}\n")
            return
    except ElixirProcessError as e:
        raise click.ClickException(e.args[0])

    if gradual:
        type_check_result = module.type_check(mod, static=False)
        if not isinstance(type_check_result, module.TypeCheckSuccess):
            print(f"{Bcolors.OKBLUE}Failed to run with gradual semantics because {mod.name} has type errors{Bcolors.ENDC}\n")
            return
        mod = cast.translate_module(type_check_result, casts=True)

    try:
        runner_output, ok = run(str(mod))
        if not ok:
            print(f"{Bcolors.FAIL}Failed to run because {mod.name} no main/0 is declared{Bcolors.ENDC}\n")
            return

        print(f"{Bcolors.OKBLUE}{runner_output}{Bcolors.ENDC}")
    except ElixirProcessError as e:
        print(f"{Bcolors.FAIL}Failed to run: {str(e)}{Bcolors.ENDC}\n")


@cli.command("iex", short_help="spawns an elixir shell (iex) loaded with the content of <filename>")
@click.argument("filename", metavar="<filename>", type=ClickWorkingDirAwarePath(exists=True, file_okay=True))
def iex_command(filename):
    import pty
    import shutil

    base_path = os.path.join(get_key(dotenv_path, "WORKING_DIR"), "")
    filename = os.path.join(base_path, filename)
    mix_project_path = os.path.join(get_key(dotenv_path, "PROJECT_PATH"), "elixir_port")
    shutil.copy(filename, os.path.join(mix_project_path, ".iex.exs"))
    os.chdir(mix_project_path)
    pty.spawn(["iex", "--erl", "-kernel shell_history enabled", "-S", "mix"])
    os.remove(".iex.exs")


@cli.command("test", short_help="run the tests for the included modules and display the results")
@click.option("--include", multiple=True, type=click.Choice(['gtypes', 'pattern', 'expression', 'cast']))
@click.option("--display-results", is_flag=True, default=False, help="Displays the results visually.")
def test_command(include, display_results):
    for item in include:
        test_path = os.path.join(os.path.join(os.path.dirname(__file__), "tests"), f"test_{item}.py")
        if display_results:
            pytest.main(["--display-results", "-s", "-v", test_path])
        else:
            pytest.main(["-s", "-v", test_path])


if __name__ == "__main__":
    cli()
