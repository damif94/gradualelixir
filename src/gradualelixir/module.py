import typing as t
from dataclasses import dataclass

from gradualelixir import expression, gtypes, pattern


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


@dataclass
class Module:
    name: str
    definitions: t.List[Definition]
    specs: t.List[Spec]


@dataclass
class TypedModule:
    name: str
    annotated_definitions: t.List[t.Tuple[Spec, Definition]]

    def __str__(self):
        msg = f"def {self.name} do\n\n"
        for definition in self.annotated_definitions:
            msg += f"{definition[0]}\n{definition[1]}\n\n"
        msg += "end"
        return msg


@dataclass
class CollectResultErrors:
    definitions_missing_specs: t.List[t.Tuple[str, int]]
    duplicated_definitions: t.List[t.Tuple[str, int]]
    specs_missing_definitions: t.List[Spec]
    duplicated_specs: t.List[Spec]


@dataclass
class TypeCheckSuccess:
    module: Module
    specs: gtypes.SpecsEnv
    definitions_success: t.Dict[Definition, expression.ExpressionTypeCheckSuccess]


@dataclass
class TypeCheckErrors:
    module: Module
    errors: t.Dict[Definition, expression.ExpressionTypeCheckError]


def collect_specs(module: Module) -> t.Union[CollectResultErrors, gtypes.SpecsEnv]:
    definitions_keys = list(set([(definition.name, definition.arity) for definition in module.definitions]))
    definitions_missing_specs = definitions_keys.copy()
    specs_missing_definitions = module.specs.copy()
    duplicated_specs = []

    specs_env = gtypes.SpecsEnv()
    for spec in module.specs:
        if specs_env.get((spec.name, spec.arity)) is not None:
            if spec not in duplicated_specs:
                duplicated_specs.append(spec)

        for definition_key in definitions_missing_specs:
            if definition_key == (spec.name, spec.arity):
                specs_env[definition_key] = (spec.parameter_types, spec.return_type)
                definitions_missing_specs.remove(definition_key)
                specs_missing_definitions.remove(spec)

    duplicated_definitions = [(definition.name, definition.arity) for definition in module.definitions]
    for definition_key in definitions_keys:
        duplicated_definitions.remove(definition_key)
    duplicated_definitions = list(set(duplicated_definitions))

    if (
        len(definitions_missing_specs)
        + len(specs_missing_definitions)
        + len(duplicated_specs)
        + len(duplicated_definitions)
    ) > 0:
        return CollectResultErrors(
            definitions_missing_specs=definitions_missing_specs,
            duplicated_definitions=duplicated_definitions,
            specs_missing_definitions=specs_missing_definitions,
            duplicated_specs=duplicated_specs,
        )
    else:
        return specs_env


def type_check(module: Module) -> t.Union[CollectResultErrors, TypeCheckErrors, TypeCheckSuccess]:
    specs_env = collect_specs(module)
    if isinstance(specs_env, CollectResultErrors):
        return specs_env

    errors: t.Dict[Definition, expression.ExpressionTypeCheckError] = {}
    definition_type_check_results: t.Dict[Definition, expression.ExpressionTypeCheckSuccess] = {}
    for definition in module.definitions:
        definition_type_check_result = expression.type_check(definition.body, gtypes.TypeEnv(), specs_env)
        if isinstance(definition_type_check_result, expression.ExpressionTypeCheckError):
            errors[definition] = definition_type_check_result
        else:
            definition_type_check_results[definition] = definition_type_check_result

    if len(errors.keys()) > 0:
        return TypeCheckErrors(module=module, errors=errors)
    else:
        return TypeCheckSuccess(module=module, definitions_success=definition_type_check_results, specs=specs_env)
