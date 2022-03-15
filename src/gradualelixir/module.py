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
        msg = f"defmodule {self.name} do\n\n"
        for definition in self.definitions:
            for spec in self.specs:
                if spec.name == definition.name:
                    msg += str(spec) + "\n"
            msg += str(definition) + "\n\n"
        msg += "end\n"
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
class CollectResultErrors:
    module: Module
    definitions_missing_specs: t.List[Definition]
    duplicated_definitions: t.List[Definition]
    specs_missing_definitions: t.List[Spec]
    duplicated_specs: t.List[Spec]
    gradual_specs: t.List[Spec]

    def __str__(self):
        msg = f"{Bcolors.OKBLUE}Errors collecting specs{Bcolors.ENDC}:\n"
        if self.definitions_missing_specs:
            msg += f"\n  {Bcolors.OKBLUE}> Definitions missing specs{Bcolors.ENDC}\n"
            msg += (
                "    "
                + ", ".join([f"{definition.name}/{definition.arity}" for definition in self.definitions_missing_specs])
                + "\n"
            )
        if self.duplicated_definitions:
            msg += f"\n  {Bcolors.OKBLUE}> Definitions with multiple declarations{Bcolors.ENDC}\n"
            msg += (
                "    "
                + ", ".join([f"{definition.name}/{definition.arity}" for definition in self.duplicated_definitions])
                + "\n"
            )
        if self.duplicated_definitions:
            msg += f"\n  {Bcolors.OKBLUE}> Definitions with multiple specs{Bcolors.ENDC}\n"
            definitions_with_multiple_specs = set((spec.name, spec.arity) for spec in self.duplicated_specs)
            msg += "    " + ", ".join([f"{name}/{arity}" for name, arity in definitions_with_multiple_specs]) + "\n"
        if self.specs_missing_definitions:
            msg += f"\n  {Bcolors.OKBLUE}> Specs pointing to non existing definitions{Bcolors.ENDC}\n"
            msg += ", ".join(["    " + str(spec) for spec in self.specs_missing_definitions]) + "\n"
        if self.gradual_specs:
            msg += f"\n  {Bcolors.OKBLUE}> Specs using non-static types{Bcolors.ENDC}\n"
            msg += "\n ".join(["    " + str(spec) for spec in self.gradual_specs]) + "\n"
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
class SpecsRefinementErrors:
    module: Module
    errors: t.Dict[Definition, DefinitionSpecsRefinementErrors]

    def __str__(self):
        msg = f"{Bcolors.OKBLUE}Errors refining specs{Bcolors.ENDC}:\n\n"
        for definition, errors in self.errors.items():
            msg += f"    {Bcolors.OKBLUE}On {definition.name}/{definition.arity}{Bcolors.ENDC}: "
            msg += f"\n{errors.message(padding='    ')}\n\n"
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
class SpecsRefinementSuccess:
    module: Module
    specs_env: gtypes.SpecsEnv
    refined_specs_env: gtypes.SpecsEnv
    pattern_match_spec_success: t.Dict[Definition, t.List[pattern.PatternMatchSuccess]]

    def __str__(self):
        refinement_success_msgs = []
        for definition in self.module.definitions:
            spec = Spec(
                name=definition.name,
                parameter_types=self.specs_env[(definition.name, definition.arity)][0],
                return_type=self.specs_env[(definition.name, definition.arity)][1],
            )
            refined_spec = Spec(
                name=spec.name,
                parameter_types=[result.type for result in self.pattern_match_spec_success[definition]],
                return_type=spec.return_type,
            )
            if refined_spec != spec:
                refinement_success_msgs += (
                    f"{Bcolors.OKBLUE}Spec for {definition.name}/{definition.arity} was refined:{Bcolors.ENDC}\n"
                    f"    From {spec}\n"
                    f"    Into {refined_spec}\n"
                )
        return "".join(refinement_success_msgs)


@dataclass
class TypeCheckSuccess:
    module: Module
    specs_refinement_success: SpecsRefinementSuccess
    definitions_success: t.Dict[Definition, expression.ExpressionTypeCheckSuccess]

    def message(self, padding=""):
        return (
            f"{padding}{Bcolors.OKBLUE}Type check success for module {self.module.name}!{Bcolors.ENDC}\n\n"
            f"{self.specs_refinement_success}\n"
        )


def collect_specs(module: Module, static: bool) -> t.Union[CollectResultErrors, gtypes.SpecsEnv]:
    specs_by_definitions_dict: t.Dict[Definition, t.List[Spec]] = {definition: [] for definition in module.definitions}
    definitions_by_spec_dict: t.Dict[Spec, t.List[Definition]] = {spec: [] for spec in module.specs}

    for spec in module.specs:
        for definition in module.definitions:
            if (definition.name, definition.arity) == (spec.name, spec.arity):
                specs_by_definitions_dict[definition].append(spec)
                definitions_by_spec_dict[spec].append(definition)

    definitions_missing_spec = []
    duplicated_definitions = []
    gradual_specs = []
    for definition, specs_for_definition in specs_by_definitions_dict.items():
        if len(specs_for_definition) == 0 and static:
            definitions_missing_spec.append(definition)
        elif len(specs_for_definition) > 1:
            duplicated_definitions.append(definition)
        elif static:
            spec = specs_for_definition[0]
            if not all([gtypes.is_static_type(type) for type in spec.parameter_types + [spec.return_type]]):
                gradual_specs.append(spec)

    specs_missing_definition = []
    duplicated_specs = []
    for spec, definitions_for_spec in definitions_by_spec_dict.items():
        if len(definitions_for_spec) == 0:
            specs_missing_definition.append(spec)
        if len(definitions_for_spec) > 1:
            duplicated_specs.append(spec)

    if (
        len(definitions_missing_spec)
        + len(specs_missing_definition)
        + len(duplicated_specs)
        + len(duplicated_definitions)
        + len(gradual_specs)
    ) > 0:
        return CollectResultErrors(
            module=module,
            definitions_missing_specs=definitions_missing_spec,
            duplicated_definitions=duplicated_definitions,
            specs_missing_definitions=specs_missing_definition,
            duplicated_specs=duplicated_specs,
            gradual_specs=gradual_specs,
        )
    else:

        extended_module_specs = {
            (spec.name, spec.arity): (spec.parameter_types, spec.return_type) for spec in module.specs
        }
        for definition in module.definitions:
            if len(specs_by_definitions_dict[definition]) == 0:
                extended_module_specs[(definition.name, definition.arity)] = (
                    [gtypes.AnyType() for _ in range(definition.arity)],
                    gtypes.AnyType(),
                )
        # relation is: (name, arity) - at most one spec exist
        return gtypes.SpecsEnv(extended_module_specs)


def refine_specs(module: Module, specs_env: gtypes.SpecsEnv) -> t.Union[SpecsRefinementSuccess, SpecsRefinementErrors]:
    refine_specs_results: t.Dict[Definition, t.List[pattern.PatternMatchSuccess]] = {}
    refine_specs_errors: t.Dict[Definition, DefinitionSpecsRefinementErrors] = {}

    for definition in module.definitions:
        definition_key = (definition.name, definition.arity)
        parameters_match_type_errors = []
        parameters_match_type_results = []
        for i in range(len(definition.parameters)):
            parameter_type = specs_env[definition_key][0][i]
            parameters_match_type_result = pattern.pattern_match(
                definition.parameters[i], parameter_type, gtypes.TypeEnv(), gtypes.TypeEnv()
            )

            if isinstance(parameters_match_type_result, pattern.PatternMatchSuccess):
                parameters_match_type_results.append(parameters_match_type_result)
            else:
                parameters_match_type_errors.append((i, parameters_match_type_result))

        if len(parameters_match_type_errors) > 0:
            refine_specs_errors[definition] = DefinitionSpecsRefinementErrors(
                definition=definition, errors=parameters_match_type_errors
            )
        else:
            refine_specs_results[definition] = parameters_match_type_results

    if len(refine_specs_errors) > 0:
        return SpecsRefinementErrors(module, refine_specs_errors)
    else:
        refined_specs_env = gtypes.SpecsEnv()
        annotated_definitions = []
        for definition in module.definitions:
            parameter_types = [result.type for result in refine_specs_results[definition]]
            return_type = specs_env[(definition.name, definition.arity)][1]
            refined_specs_env[(definition.name, definition.arity)] = (parameter_types, return_type)
            annotated_definitions.append((Spec(definition.name, parameter_types, return_type), definition))
        return SpecsRefinementSuccess(
            module=module,
            specs_env=specs_env,
            refined_specs_env=refined_specs_env,
            pattern_match_spec_success=refine_specs_results,
        )


def type_check_aux(specs_refinement_success: SpecsRefinementSuccess) -> t.Union[TypeCheckErrors, TypeCheckSuccess]:
    module = specs_refinement_success.module
    definition_type_check_errors: t.Dict[
        Definition, t.Union[DefinitionReturnTypeError, DefinitionBodyTypeCheckError]
    ] = {}
    definition_type_check_results: t.Dict[Definition, expression.ExpressionTypeCheckSuccess] = {}

    for definition in module.definitions:
        spec = specs_refinement_success.specs_env[(definition.name, definition.arity)]
        pattern_match_success_list = specs_refinement_success.pattern_match_spec_success[definition]
        initial_env: t.Dict[str, gtypes.Type] = {}
        for pattern_match_success in pattern_match_success_list:
            initial_env = {**initial_env, **pattern_match_success.exported_env.env}
        body_type_check_result = expression.type_check(
            definition.body, gtypes.TypeEnv(initial_env), specs_refinement_success.specs_env
        )
        if isinstance(body_type_check_result, expression.ExpressionTypeCheckError):
            definition_type_check_errors[definition] = DefinitionBodyTypeCheckError(
                definition=definition,
                env=gtypes.TypeEnv(initial_env),
                specs_env=specs_refinement_success.refined_specs_env,
                error=body_type_check_result,
            )
        else:
            body_type = body_type_check_result.type
            if not gtypes.is_subtype(body_type_check_result.type, spec[1]):
                definition_type_check_errors[definition] = DefinitionReturnTypeError(
                    definition=definition, body_type=body_type, return_type=spec[1]
                )
            else:
                definition_type_check_results[definition] = body_type_check_result

    if len(definition_type_check_errors.keys()) > 0:
        return TypeCheckErrors(module=module, errors=definition_type_check_errors)
    else:
        return TypeCheckSuccess(module, specs_refinement_success, definition_type_check_results)


def type_check(
    module: Module, static: bool
) -> t.Union[CollectResultErrors, SpecsRefinementErrors, TypeCheckErrors, TypeCheckSuccess]:
    collect_result = collect_specs(module, static)
    if isinstance(collect_result, CollectResultErrors):
        return collect_result

    specs_refine_results = refine_specs(module, collect_result)
    if isinstance(specs_refine_results, SpecsRefinementErrors):
        return specs_refine_results

    type_check_result = type_check_aux(specs_refine_results)
    return type_check_result
