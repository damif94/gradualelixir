import typing as t
from dataclasses import dataclass

from gradualelixir import expression, gtypes, pattern
from gradualelixir.utils import Bcolors, ordinal


@dataclass
class Spec:
    name: str
    parameter_types: t.List[gtypes.Type]
    return_type: gtypes.Type

    @property
    def arity(self):
        return len(self.parameter_types)

    def __str__(self):
        return f"@spec {self.name}({', '.join([str(param) for param in self.parameter_types])})::{self.return_type}"

    def __hash__(self):
        return hash(",".join([str(type) for type in self.parameter_types + [self.return_type]]))


@dataclass
class Definition:
    name: str
    parameters: t.List[pattern.Pattern]
    body: expression.Expression

    @property
    def arity(self):
        return len(self.parameters)

    def __str__(self):
        return f"def {self.name}({', '.join([str(param) for param in self.parameters])}) do\n" f"  {self.body}\n" "end"

    def __hash__(self):
        return hash(",".join([str(param) for param in self.parameters]) + str(self.body))


@dataclass
class Module:
    name: str
    definitions: t.List[Definition]
    specs: t.List[Spec]

    def __str__(self):
        msg = f"defmodule {self.name} do\n"
        msg += "  use UseCast\n\n"
        unused_specs_by_key = dict([((spec.name, spec.arity), spec) for spec in self.specs])
        for definition in self.definitions:
            if (definition.name, definition.arity) in unused_specs_by_key.keys():
                spec = unused_specs_by_key[(definition.name, definition.arity)]
                msg += f"{spec}\n{definition}\n\n"
                del unused_specs_by_key[(definition.name, definition.arity)]
            else:
                msg += f"{definition}\n\n"
        msg += "end"
        return msg


@dataclass
class DefinitionParameterTypeCheckError:
    definition: Definition
    specs_env: gtypes.SpecsEnv
    error: pattern.PatternMatchError

    def message(self, padding=""):
        from gradualelixir.elixir_port import format_code

        spec = self.specs_env[(self.definition.name, self.definition.arity)]
        msg = f"\n    {Spec(name=self.definition.name, parameter_types=spec[0], return_type=spec[1])}\n"
        msg += "\n".join(["    " + line for line in format_code(str(self.definition)).split("\n")]) + "\n\n"
        msg += self.error.message(padding=padding)
        return msg


@dataclass
class DefinitionBodyTypeCheckError:
    definition: Definition
    env: gtypes.TypeEnv
    specs_env: gtypes.SpecsEnv
    error: expression.ExpressionTypeCheckError

    def message(self, padding=""):
        from gradualelixir.elixir_port import format_code

        spec = self.specs_env[(self.definition.name, self.definition.arity)]
        msg = f"\n    {Spec(name=self.definition.name, parameter_types=spec[0], return_type=spec[1])}\n"
        msg += "\n".join(["    " + line for line in format_code(str(self.definition)).split("\n")]) + "\n\n"
        msg += self.error.message(padding=padding, env=self.env, specs_env=self.specs_env)
        return msg


@dataclass
class DefinitionReturnTypeError:
    definition: Definition
    body_type: gtypes.Type
    return_type: gtypes.Type

    def message(self, padding=""):
        return (
            f"{padding}{Bcolors.FAIL}The type inferred for the body expression, {self.body_type}, "
            f"is not a subtype of {self.return_type}{Bcolors.ENDC}"
        )


@dataclass
class CollectSpecsResultErrors:
    module: Module
    definitions_missing_spec: t.Set[t.Tuple[str, int]]
    specs_missing_definition: t.Set[Spec]
    duplicated_specs: t.Set[t.Tuple[str, int]]
    gradual_specs: t.Set[Spec]

    def __str__(self):
        msg = f"{Bcolors.OKBLUE}Errors collecting specs{Bcolors.ENDC}:\n"
        if self.definitions_missing_spec:
            msg += f"\n  {Bcolors.OKBLUE}> Definitions missing specs{Bcolors.ENDC}\n"
            msg += (
                "    "
                + ", ".join([f"{name}/{str(arity)}" for name, arity in self.definitions_missing_spec])
                + "\n"
            )
        if self.duplicated_specs:
            msg += f"\n  {Bcolors.OKBLUE}> Definitions with multiple specs{Bcolors.ENDC}\n"
            msg += "    " + "\n ".join([f"{name}/{str(arity)}" for name, arity in self.duplicated_specs]) + "\n"
        if self.specs_missing_definition:
            msg += f"\n  {Bcolors.OKBLUE}> Specs pointing to non existing definitions{Bcolors.ENDC}\n"
            msg += "\n".join(["    " + str(spec) for spec in self.specs_missing_definition]) + "\n"
        if self.gradual_specs:
            msg += f"\n  {Bcolors.OKBLUE}> Specs using non-static types{Bcolors.ENDC}\n"
            msg += "\n".join(["    " + str(spec) for spec in self.gradual_specs]) + "\n"
        return msg + f"{Bcolors.ENDC}"


@dataclass
class DefinitionSpecsRefinementErrors:
    definition: Definition
    errors: t.List[t.Tuple[int, pattern.PatternMatchError]]

    def message(self, padding=""):
        msg = ""
        for index, error in self.errors:
            msg += (
                f"{padding}{Bcolors.OKBLUE}Couldn't match {ordinal(index)} argument "
                f"with the corresponding type:{Bcolors.ENDC}\n"
            )
            msg += error.message(padding=padding + "    ")
        return msg


@dataclass
class TypeCheckErrors:
    module: Module
    errors: t.Dict[Definition, t.Union[DefinitionReturnTypeError, DefinitionBodyTypeCheckError]]

    def __str__(self):
        msg = f"{Bcolors.OKBLUE}Type check errors{Bcolors.ENDC}:\n\n"
        for definition, errors in self.errors.items():
            msg += f"    {Bcolors.OKBLUE}On {definition.name}/{definition.arity}{Bcolors.ENDC}: "
            msg += f"\n{errors.message('    ')}\n\n"
        return msg


@dataclass
class CollectSuccess:
    module: Module
    specs_env: gtypes.SpecsEnv

    def __str__(self):
        collect_success_msgs = []
        for definition in self.module.definitions:
            spec = Spec(
                name=definition.name,
                parameter_types=self.specs_env[(definition.name, definition.arity)][0],
                return_type=self.specs_env[(definition.name, definition.arity)][1],
            )
            collect_success_msgs += (
                f"{Bcolors.OKBLUE}Spec for {definition.name}/{definition.arity}:{Bcolors.ENDC}\n"
                f"    {spec}\n"
            )
        return "".join(collect_success_msgs)


@dataclass
class TypeCheckSuccess:
    module: Module
    collect_success: CollectSuccess
    definitions_success: t.Dict[Definition, expression.ExpressionTypeCheckSuccess]

    def message(self, padding=""):
        return (
            f"{padding}{Bcolors.OKBLUE}Type check success for module {self.module.name}!{Bcolors.ENDC}\n\n"
        )


def format_module(module: Module, padding="") -> str:
    from .elixir_port import format_code

    msg = format_code(str(module))
    return "\n\n" + "\n".join([padding + m for m in msg.split("\n")])


def collect_specs(module: Module, static: bool) -> t.Union[CollectSpecsResultErrors, gtypes.SpecsEnv]:
    definition_keys: t.Set[t.Tuple[str, int]] = set()
    for definition in module.definitions:
        definition_keys.add((definition.name, definition.arity))
    specs_by_definition_dict: t.Dict[t.Tuple[str, int], t.List[Spec]] = {
        (name, arity): [] for name, arity in definition_keys
    }
    for spec in module.specs:
        for name, arity in definition_keys:
            if (name, arity) == (spec.name, spec.arity):
                specs_by_definition_dict[(name, arity)].append(spec)
    definitions_missing_spec: t.Set[t.Tuple[str, int]] = set()
    duplicated_specs: t.Set[t.Tuple[str, int]] = set()
    gradual_specs: t.Set[Spec] = set()
    for definition, specs_for_definition in specs_by_definition_dict.items():
        if len(specs_for_definition) == 0 and static:
            definitions_missing_spec.add(definition)
        if len(specs_for_definition) > 1:
            duplicated_specs.add(definition)
        if static:
            for spec in specs_for_definition:
                if not all([gtypes.is_static_type(type) for type in spec.parameter_types + [spec.return_type]]):
                    gradual_specs.add(spec)
    specs_missing_definition: t.Set[Spec] = set()
    for spec in module.specs:
        if (spec.name, spec.arity) not in specs_by_definition_dict.keys():
            specs_missing_definition.add(spec)

    if (
        len(definitions_missing_spec)
        + len(specs_missing_definition)
        + len(duplicated_specs)
        + len(gradual_specs)
    ) > 0:
        return CollectSpecsResultErrors(
            module=module,
            definitions_missing_spec=definitions_missing_spec,
            specs_missing_definition=specs_missing_definition,
            duplicated_specs=duplicated_specs,
            gradual_specs=gradual_specs,
        )
    else:
        module_specs = {
            (spec.name, spec.arity): (spec.parameter_types, spec.return_type) for spec in module.specs
        }
        return gtypes.SpecsEnv(module_specs)


def type_check(
    module: Module, static: bool
) -> t.Union[CollectSpecsResultErrors, TypeCheckErrors, TypeCheckSuccess]:
    collect_result = collect_specs(module, static)
    if isinstance(collect_result, CollectSpecsResultErrors):
        return collect_result

    specs_env = collect_result
    definition_type_check_errors: t.Dict[
        Definition, t.Union[DefinitionReturnTypeError, DefinitionParameterTypeCheckError, DefinitionBodyTypeCheckError]
    ] = {}
    definition_type_check_results: t.Dict[Definition, expression.ExpressionTypeCheckSuccess] = {}

    # enrich with dynamic signatures for expression typing
    specs_env_for_definition = collect_result.copy()
    for definition in module.definitions:
        if specs_env_for_definition.get((definition.name, len(definition.parameters))) is None:
            specs_env_for_definition[(definition.name, len(definition.parameters))] = (
                [gtypes.AnyType() for _ in definition.parameters], gtypes.AnyType()
            )

    for definition in module.definitions:
        parameters_env = gtypes.TypeEnv()
        definition_key = (definition.name, len(definition.parameters))
        if specs_env.get(definition_key) is None:
            continue

        for i in range(len(definition.parameters)):
            parameter_type = specs_env[definition_key][0][i]
            parameter_match_type_result = pattern.type_check(
                definition.parameters[i], parameter_type, parameters_env, gtypes.TypeEnv()
            )

            if isinstance(parameter_match_type_result, pattern.PatternMatchSuccess):
                parameters_env = parameter_match_type_result.exported_env
            else:
                definition_type_check_errors[definition] = DefinitionParameterTypeCheckError(
                    definition=definition,
                    specs_env=specs_env_for_definition,
                    error=parameter_match_type_result,
                )

        body_type_check_result = expression.type_check(definition.body, parameters_env, specs_env_for_definition)
        if isinstance(body_type_check_result, expression.ExpressionTypeCheckError):
            definition_type_check_errors[definition] = DefinitionBodyTypeCheckError(
                definition=definition,
                env=parameters_env,
                specs_env=specs_env_for_definition,
                error=body_type_check_result,
            )
        else:
            body_type = body_type_check_result.type
            if not gtypes.is_subtype(body_type_check_result.type, specs_env[definition_key][1]):
                definition_type_check_errors[definition] = DefinitionReturnTypeError(
                    definition=definition, body_type=body_type, return_type=specs_env[definition_key][1]
                )
            else:
                definition_type_check_results[definition] = body_type_check_result

    if len(definition_type_check_errors.keys()) > 0:
        return TypeCheckErrors(module=module, errors=definition_type_check_errors)
    else:
        return TypeCheckSuccess(module, CollectSuccess(module, collect_result), definition_type_check_results)
