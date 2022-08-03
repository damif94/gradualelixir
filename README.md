# A Gradual Type Checker for the (Mini) Elixir Language

[comment]: <> (# The Type Checker)

[comment]: <> (### Allowed Types And Their Semantics)

[comment]: <> (### Subtyping)

[comment]: <> (### Examples)

[comment]: <> (# The Runtime Semantics for Type Checked Modules)

[comment]: <> (## Annotations Under The Hood)

[comment]: <> (## The Extended Semantics For Annotations)

# Introduction

This project was carried out in the context of my bachelor 's degree thesis at the Engineering Faculty of UDELAR (Universidad de la República, Uruguay). The main objective was to adapt the gradual typing discipline to the [Elixir programming language](https://elixir-lang.org/), in a careful way so as to endow the designed type system with:
- **Type Safety** that guarantees typing errors won't occur when running type-checked programs
- **The Static Gradual Guarantee**, which constitutes a crucial quality standard about gradual type-checkers, and implies "well-behavior" of the type-checked programs as they get more heavily type-annotated.

Moreover, a cast enrichment translation was defined for the type-checked programs, in a similar fashion to the cast calculus for the gradually-typed languages found in the literature. Running the translated version of the program makes type safety possible for any gradually typed program, at the cost of possibly introducing cast errors, that are less severe and more desirable for a number of reasons. Even if we don't bring the proof (hopefully in the future!), we believe that the design of the cast enrichment translation will make the Dynamic Gradual Guarantee to also hold.

Instead of setting the whole Elixir syntax as our aim, we decided to focus on a restricted portion of the language -which is still Turing-complete, though- for two different reasons:
- In order to establish the desirable formal properties for our system, deeper research should be carried out to make our design still correct for some constructs that are available on the full syntax (multiple clauses for function definitions, for instance).
- The time and resources that were available prevent us from including a lot of extra portions of the full syntax that would nevertheless follow mostly straightforward from the current design.


# Implementation Overview

The implementation of the project can be considered as divided in these main components:
- **The type checker** was implemented in python for personal convenience in the context of a tight schedule.
- **The cast enrichment** translation was written in python as it constitutes a plugin for the type checker.
- **The cast semantics** was implemented indirectly by defining a macro on the elixir language.

Even if it was possible to write the type checker and the cast enrichment as a single process, they were build separately because we think it will easier for a reader to understand them in isolation; the type checker as the _core_ process and the cast enrichment as a _consumer_ of the former.

I am conscious that the implementation is far from being ready to be used for real-world codebases, because it wasn't built with a focus on efficiency. My view is that its value lies more on the methodology than anything else.


# Setup
## Normal Setup
We assume that you have a recent version of `elixir` installed (>= 1.11) and a recent version of `python` (>= 3.8)
in your system. 

1. Clone this repository and open a terminal on the root directory.
2. Turn the `gradualelixir` file into an executable by running
```bash
$  chmod +x gradualelixir
```
3. Execute the cli for the first time to set up the python virtualenv with the project dependencies.
```bash
$  ./gradualelixir --help
```
This will also display all the available commands.

4. The usage of each command is also documented. Before using it, run:
```bash
$  ./gradualelixir <command_name> --help
```

# Mini Elixir
## Allowed Expressions And Their Semantics
### Literals
### Pattern Match
#### Patterns
### Control Flow Operators
### Function Definitions
## Single Module Restriction


# The Type Checker
### Allowed Types And Their Semantics
### Subtyping
### Examples

# The Runtime Semantics for Type Checked Modules
## Annotations Under The Hood
## The Extended Semantics For Annotations


[comment]: <> (Lyskov Substitution Principle)

[comment]: <> (## - Static Type Checker)

[comment]: <> (## - Gradual Type Checker)

### Running instructions

In order to start the gradualelixir container, choose a `working_dir` folder to use
as root for the gradualelixir cli. For example, I am using `/Users/damian/Documents` on my macos. 

Execute
```bash
$  alias gradualelixir="docker run -it -v <working_dir>:/resources/ --rm gradualelixir"
```

Every time you start a new session or want to change the `working_dir` folder, you must execute this command again.

You can try interacting with the cli, by executing
```bash
$  gradualelixir --help
```

