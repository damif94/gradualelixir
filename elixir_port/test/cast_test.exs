defmodule ElixirPortTest do
  use ExUnit.Case
  use UseCast
  alias Cast
  alias Code
  require Cast
  require Inspect
  doctest ElixirPort

  defmacro assert_raise_error(error_module_ast, expr_ast) do
    quote do
      assert_raise unquote(error_module_ast), fn -> unquote(expr_ast) end
    end
  end

  defmacro assert_raise_error_with_message(error_module_ast, message_ast, expr_ast) do
    quote do
      assert_raise unquote(error_module_ast), unquote(message_ast), fn -> unquote(expr_ast) end
    end
  end

  def assert_is_true_unit(f), do: assert f.() === true
  def assert_is_false_unit(f), do: assert f.() === false

  @tag disabled: true
  test "build_type_from_ast" do
    assert Cast.build_type_from_ast(Code.string_to_quoted!("true")) == {:atom, true}
    assert Cast.build_type_from_ast(Code.string_to_quoted!(":one")) == {:atom, :one}
    assert Cast.build_type_from_ast(Code.string_to_quoted!("integer")) == :integer

    assert Cast.build_type_from_ast(Code.string_to_quoted!("[]")) == :elist
    assert Cast.build_type_from_ast(Code.string_to_quoted!("[integer]")) == {:list, :integer}

    assert Cast.build_type_from_ast(Code.string_to_quoted!("{}")) == {:tuple, []}
    assert Cast.build_type_from_ast(Code.string_to_quoted!("{integer}")) == {:tuple, [:integer]}
    assert Cast.build_type_from_ast(Code.string_to_quoted!("{integer, float}")) == {:tuple, [:integer, :float]}
    assert Cast.build_type_from_ast(Code.string_to_quoted!("{integer, float, any}")) == {:tuple, [:integer, :float, :any]}

    assert Cast.build_type_from_ast(Code.string_to_quoted!("%{}")) == {:map, []}
    assert Cast.build_type_from_ast(Code.string_to_quoted!("%{1 => integer}")) == {:map, [{1, :integer}]}
    assert Cast.build_type_from_ast(Code.string_to_quoted!("%{1 => integer, :one => float, 3.0 => :two}")) == {:map, [{1, :integer}, {:one, :float}, {3.0, {:atom, :two}}]}

    assert Cast.build_type_from_ast(Code.string_to_quoted!("( -> integer)")) == {:fun, [], :integer}
    assert Cast.build_type_from_ast(Code.string_to_quoted!("(float -> integer)")) == {:fun, [:float], :integer}
    assert Cast.build_type_from_ast(Code.string_to_quoted!("(float, atom -> integer)")) == {:fun, [:float, :atom], :integer}

    assert Cast.build_type_from_ast(Code.string_to_quoted!("( -> {float, [%{1 => integer}]})")) == {:fun, [], {:tuple, [:float, {:list, {:map, [{1, :integer}]}}]}}
  end

  @tag disabled: true
  test "is_base" do
    assert Cast.is_base(:integer)
    assert Cast.is_base(:float)
    assert Cast.is_base(:number)
    assert Cast.is_base(:atom)
    assert Cast.is_base({:atom, true})
    assert Cast.is_base({:atom, :one})
    assert Cast.is_base({:atom, :atom})

    assert not Cast.is_base(:any)
    assert not Cast.is_base(:string)
    assert not Cast.is_base(:elist)
    assert not Cast.is_base({:list, true})
    assert not Cast.is_base({:tuple, [true]})
    assert not Cast.is_base({:tuple, [true, true]})
    assert not Cast.is_base({:map, [{1, true}]})
    assert not Cast.is_base({:fun, [], true})
    assert not Cast.is_base({:fun, [true, true], true})
  end

  @tag disabled: true
  test "ground_type_for_value" do
    assert Cast.ground_type_for_value(1) == :integer
    assert Cast.ground_type_for_value(-122) == :integer
    assert Cast.ground_type_for_value(-122.0) == :float
    assert Cast.ground_type_for_value(1.32) == :float
    assert Cast.ground_type_for_value(true) == {:atom, true}
    assert Cast.ground_type_for_value(:one) == {:atom, :one}

    assert Cast.ground_type_for_value([]) == :elist

    assert Cast.ground_type_for_value([1]) == {:list, :any}
    assert Cast.ground_type_for_value([:one, 1, -122.0]) == {:list, :any}

    assert Cast.ground_type_for_value({}) == {:tuple, []}
    assert Cast.ground_type_for_value({1}) == {:tuple, [:any]}
    assert Cast.ground_type_for_value({1, :one, -122.0}) == {:tuple, [:any, :any, :any]}

    assert Cast.ground_type_for_value(%{}) == {:map, []}
    assert Cast.ground_type_for_value(%{1 => :one}) == {:map, [{1, :any}]}
    assert Cast.ground_type_for_value(%{1 => :one, :one => -122.0}) == {:map, [{1, :any}, {:one, :any}]}

    assert Cast.ground_type_for_value(fn -> :one end) == {:fun, [], :any}
    assert Cast.ground_type_for_value(fn _x -> :one end) == {:fun, [:any], :any}
    assert Cast.ground_type_for_value(fn 1, :one, y -> {y, :one} end) == {:fun, [:any, :any, :any], :any}

    assert Cast.ground_type_for_value((fn -> :one end | (-> :atom) ~> ( -> :boolean))) == {:fun, [], :any}
    assert Cast.ground_type_for_value((fn _ -> :one end | (:integer -> :atom) ~> (:integer -> :boolean))) == {:fun, [:any], :any}
    assert Cast.ground_type_for_value((fn _, 1 -> :one end | (:integer, :atom -> :atom) ~> (:integer, :atom -> :boolean))) == {:fun, [:any, :any], :any}
  end

  @tag disabled: true
  test "ground_type_for_type" do
    assert Cast.ground_type_for_type(:integer) == :integer
    assert Cast.ground_type_for_type(:float) == :float
    assert Cast.ground_type_for_type(:number) == :number
    assert Cast.ground_type_for_type(:atom) == :atom
    assert Cast.ground_type_for_type({:atom, true}) == {:atom, true}
    assert Cast.ground_type_for_type({:atom, :one}) == {:atom, :one}

    assert_raise_error(CaseClauseError, Cast.ground_type_for_type(:any))

    assert Cast.ground_type_for_type(:elist) == :elist
    assert Cast.ground_type_for_type({:list, :integer}) == {:list, :any}

    assert Cast.ground_type_for_type({:tuple, []}) == {:tuple, []}
    assert Cast.ground_type_for_type({:tuple, [:integer, :number, :any]}) == {:tuple, [:any, :any, :any]}

    assert Cast.ground_type_for_type({:map, []}) == {:map, []}
    assert Cast.ground_type_for_type({:map, [{1, :integer}, {:one, :any}]}) == {:map, [{1, :any}, {:one, :any}]}

    assert Cast.ground_type_for_type({:fun, [], :integer}) == {:fun, [], :any}
    assert Cast.ground_type_for_type({:fun, [:integer, :number], :any}) == {:fun, [:any, :any], :any}
  end

  @tag disabled: true
  test "is_subtype" do
    assert Cast.is_subtype(:integer, :number)
    assert not Cast.is_subtype(:integer, :float)
    assert not Cast.is_subtype(:float, :integer)
    assert not Cast.is_subtype(:number, :integer)
    assert not Cast.is_subtype(:number, :float)

    assert Cast.is_subtype({:atom, :one}, :atom)
    assert Cast.is_subtype({:atom, true}, :atom)
    assert not Cast.is_subtype({:atom, true}, {:atom, :one})
    assert not Cast.is_subtype({:atom, :one}, {:atom, true})

    assert Cast.is_subtype(:any, :any)
    assert not Cast.is_subtype(:any, :number)
    assert not Cast.is_subtype(:number, :any)
    assert not Cast.is_subtype(:any, :atom)
    assert not Cast.is_subtype(:atom, :any)

    assert Cast.is_subtype(:elist, :elist)
    assert Cast.is_subtype(:elist, {:list, :number})
    assert Cast.is_subtype(:elist, {:list, :any})
    assert Cast.is_subtype({:list, :integer}, {:list, :number})
    assert not Cast.is_subtype({:list, :number}, :elist)
    assert not Cast.is_subtype({:list, :number}, {:list, :integer})

    assert Cast.is_subtype({:tuple, []}, {:tuple, []})
    assert Cast.is_subtype({:tuple, [:integer, {:atom, :one}]}, {:tuple, [:number, :atom]})
    assert not Cast.is_subtype({:tuple, []}, {:tuple, [:number, :atom]})
    assert not Cast.is_subtype({:tuple, [:number, :atom]}, {:tuple, []})
    assert not Cast.is_subtype({:tuple, [:number, {:atom, :one}]}, {:tuple, [:integer, :atom]})
    assert not Cast.is_subtype({:tuple, [:integer, :atom]}, {:tuple, [:number, {:atom, :one}]})
    
    assert Cast.is_subtype({:map, []}, {:map, []})
    assert Cast.is_subtype({:map, [{1, :number}, {2, :atom}]}, {:map, []})
    assert Cast.is_subtype({:map, [{1, :number}, {2, :atom}]}, {:map, [{2, :atom}]})
    assert Cast.is_subtype({:map, [{1, :integer}, {2, {:atom, :one}}]}, {:map, [{1, :number}, {2, :atom}]})
    assert Cast.is_subtype({:map, [{1, :integer}, {2, {:atom, :one}}]}, {:map, [{2, :atom}, {1, :number}]})
    assert not Cast.is_subtype({:map, []}, {:map, [{1, :number}, {2, :atom}]})
    assert not Cast.is_subtype({:map, [{2, :atom}]}, {:map, [{1, :number}, {2, :atom}]})
    assert not Cast.is_subtype({:map, [{1, :number}, {2, {:atom, :one}}]}, {:map, [{1, :integer}, {2, :atom}]})
    assert not Cast.is_subtype({:map, [{1, :integer}, {2, :atom}]}, {:map, [{1, :number}, {2, {:atom, :one}}]})
    
    assert Cast.is_subtype({:fun, [], :integer}, {:fun, [], :integer})
    assert Cast.is_subtype({:fun, [:number, :atom], :integer}, {:fun, [:integer, {:atom, :one}], :number})
    assert not Cast.is_subtype({:fun, [], :integer}, {:fun, [:number, :atom], :integer})
    assert not Cast.is_subtype({:fun, [:number, :atom], :integer}, {:fun, [], :integer})
    assert not Cast.is_subtype({:fun, [:integer, :atom], :integer}, {:fun, [:number, {:atom, :one}], :number})
    assert not Cast.is_subtype({:fun, [:number, {:atom, :one}], :integer}, {:fun, [:integer, :atom], :number})
    assert not Cast.is_subtype({:fun, [:number, :atom], :number}, {:fun, [:integer, {:atom, :one}], :integer})
  end

  @tag disabled: true
  test "d_lit_cast" do
    assert (1 | integer ~> integer) === 1
    assert (1 | number ~> number) === 1
    assert (1 | any  ~> any) === 1
    assert (1 | any  ~> integer) === 1
    assert (1 | any  ~> number) === 1
    assert (1.0 | float ~> float) === 1.0
    assert (1.0 | any ~> number) === 1.0
    assert (1.0 | any  ~> float) === 1.0

    assert_raise_error(Cast.CastError, 1 | any ~> float)
    assert_raise_error(Cast.CastError, 1.0 | any ~> integer)

    assert_raise_error(Cast.BadArgumentError, 1 | integer ~> number)
    assert_raise_error(Cast.BadArgumentError, 1 | number ~> integer)
    assert_raise_error(Cast.BadArgumentError, 1 | integer ~> float)
    assert_raise_error(Cast.BadArgumentError, 1 | number ~> float)
    assert_raise_error(Cast.BadArgumentError, 1 | float ~> float)
    assert_raise_error(Cast.BadArgumentError, 1 | float ~> any)
  end

#  @tag disabled: true
  test "d_elist_cast" do
    assert ([]| [] ~> []) == []
    assert ([]| [{integer, any}] ~> [{integer, any}]) == []
    assert ([]| [] ~> [{integer, any}]) == []
    assert ([]| [{integer, any}] ~> []) == []
    assert ([]| any ~> any) == []
    assert ([]| any ~> [{integer, any}]) == []
    assert ([]| [{integer, any}] ~> any) == []

    assert_raise_error(Cast.CastError, [] | any ~> integer)

    assert_raise_error(Cast.BadArgumentError, [] | integer ~> [])
    assert_raise_error(Cast.BadArgumentError, [] | [] ~> integer)
    assert_raise_error(Cast.BadArgumentError, [] | integer ~> [{integer, any}])
    assert_raise_error(Cast.BadArgumentError, [] | [{integer, any}] ~> integer)
  end

#  @tag disabled: true
  test "d_list_cast" do
    assert ([1] | [integer] ~> [integer]) == [1]
    assert ([1] | [number] ~> [number]) == [1]
    assert ([1] | any ~> any) == [1]
    assert ([1] | [any] ~> any) == [1]
    assert ([1] | any ~> [any]) == [1]
    assert ([1] | any ~> [integer]) == [1]
    assert ([1] | [any] ~> [integer]) == [1]
    assert ([1] | [any] ~> [number]) == [1]
    assert ([2.0] | [float] ~> [float]) == [2.0]
    assert ([2.0] | [any] ~> [float]) == [2.0]
    assert ([2.0] | [any] ~> [number]) == [2.0]
    assert ([2.0] | [number] ~> [number]) == [2.0]
    assert ([1, 2.0] | [number] ~> [number]) == [1, 2.0]

    assert_raise_error(Cast.CastError, [1] | [any] ~> [float])
    assert_raise_error(Cast.CastError, [2.0] | [any] ~> [integer])
    assert_raise_error(Cast.CastError, [1, 2.0] | [any] ~> [integer])
    assert_raise_error(Cast.CastError, [1, 2.0] | [any] ~> [float])

    assert_raise_error(Cast.BadArgumentError, [1] | [float] ~> [float])
    assert_raise_error(Cast.BadArgumentError, [1] | [float] ~> [integer])
    assert_raise_error(Cast.BadArgumentError, [1] | [float] ~> [any])
    assert_raise_error(Cast.BadArgumentError, [1] | [integer] ~> [float])
    assert_raise_error(Cast.BadArgumentError, [1] | [integer] ~> [number])
    assert_raise_error(Cast.BadArgumentError, [1] | [number] ~> [integer])
    assert_raise_error(Cast.BadArgumentError, [2.0] | [integer] ~> [integer])
    assert_raise_error(Cast.BadArgumentError, [1, 2.0] | [integer] ~> [integer])
    assert_raise_error(Cast.BadArgumentError, [1, 2.0] | [float] ~> [float])
  end

  @tag disabled: true
  test "d_cast_error" do
    assert_raise_error(Cast.CastError, [] | any ~> integer)
  end


  @tag disabled: true
  test "d_ground_any" do
    assert (1 | integer ~> any) === 1
    assert (1 | number ~> any) === 1

    assert (1.0 | float ~> any) === 1.0
    assert (1.0 | number ~> any) === 1.0

    assert (:a | :a ~> any) === :a
    assert (:a | atom ~> any) === :a

    assert (true | true ~> any) === true
    assert (false | false ~> any) === false
    assert (true | boolean ~> any) === true
    assert (false | boolean ~> any) === false
    assert (true | atom ~> any) === true
    assert (false | atom ~> any) === false

    assert ([] | [] ~> any) === []
    assert ([1, 1.0] | [integer] ~> any) === [1, 1.0]

    assert ({} | {} ~> any) === {}
    assert ({1} | {integer} ~> any) === {1}
    assert ({1} | {any} ~> any) === {1}
    assert ({1, 1.0} | {integer, float} ~> any) === {1, 1.0}
    assert ({1, 1.0} | {any, any} ~> any) === {1, 1.0}
    assert ({1, {1.0, 2.0}} | {any, {any, float}} ~> any) === {1, {1.0, 2.0}}

    assert (%{} | %{} ~> any) === %{}
    assert (%{1 => :one} | %{} ~> any) === %{1 => :one}
    assert (%{1 => :one} | %{1 => atom} ~> any) === %{1 => :one}
#
#    result = ([true_unit] | [( -> any)] ~> [( -> true)])
#    [v] = result
#    assert_is_true_unit(v)
#
#    result = ([true_unit] | [( -> any)] ~> [( -> true)])
#    [v] = result
#    assert_is_true_unit(v)

#    assert_raise_error(Cast.BadArgumentError, {} | {any} ~> any)
  end
#
#  @tag disabled: true
#  test "base_values_from_any" do
#    assert (1 | any ~> integer) === 1
#    assert (1 | any ~> number) === 1
#
#    assert (1.0 | float ~> any) === 1.0
#    assert (1.0 | number ~> any) === 1.0
#
#    assert (:a | any ~> :a) === :a
#    assert (:a | any ~> atom) === :a
#
#    assert (true | any ~> true) === true
#    assert (false | any ~> false) === false
#    assert (true | any ~> boolean) === true
#    assert (false | any ~> boolean) === false
#    assert (true | any ~> atom) === true
#    assert (false | any ~> atom) === false
#
#    assert_raise_error(Cast.CastError, 1 | any ~> float)
#    assert_raise_error(Cast.CastError, 1.0 | any ~> integer)
#    assert_raise_error(Cast.CastError, 1 | any ~> atom)
#    assert_raise_error(Cast.CastError, 1.0 | any ~> atom)
#
#    assert_raise_error(Cast.CastError, :a | any ~> :b)
#    assert_raise_error(Cast.CastError, :a | any ~> boolean)
#    assert_raise_error(Cast.CastError, :a | any ~> number)
#
#    assert_raise_error(Cast.CastError, true | any ~> :a)
#    assert_raise_error(Cast.CastError, false | any ~> :a)
#    assert_raise_error(Cast.CastError, true | any ~> false)
#    assert_raise_error(Cast.CastError, false | any ~> true)
#    assert_raise_error(Cast.CastError, false | any ~> integer)
#  end
#

#  @tag disabled: true
#  test "any_id" do
#    assert (1 | any ~> any) === 1
#    assert (1 | any ~> any) == 1
#
#    assert (1.0 | any ~> any) === 1.0
#    assert (1.0 | any ~> any) == 1.0
#
#    assert (:a | any ~> any) === :a
#    assert (:a | any ~> any) === :a
#
#    assert (true | any ~> any) === true
#    assert (false | any ~> any) === false
#    assert (true | any ~> any) === true
#    assert (false | any ~> any) === false
#    assert (true | any ~> any) === true
#    assert (false | any ~> any) === false
#
#    assert ([] | any ~> any) === []
#    assert ([1, 1.0] | any ~> any) === [1, 1.0]
#
#    assert ({} | any ~> any) === {}
#    assert ({1} | any ~> any) === {1}
#    assert ({1, 1.0} | any ~> any) === {1, 1.0}
#    assert ({1, 1.0, true} | any ~> any) === {1, 1.0, true}
#
#    assert (%{} | any ~> any) === %{}
#    assert (%{:a => 1} | any ~> any) === %{:a => 1}
#  end
#
#
#  @tag disabled: true
#  test "ground_fail" do
##    assert_raise_error(Cast.CastError, 1 | any ~> float)
##    assert_raise_error(Cast.CastError, 1 | integer ~> float)
##    assert_raise_error(Cast.CastError, :a | :a ~> :b)
##    assert_raise_error(Cast.CastError, :a | atom ~> :b)
##
##    assert_raise_error(Cast.BadArgumentError, :a | integer ~> :a)
##    assert_raise_error(Cast.BadArgumentError, :a | integer ~> :b)
##
##    assert_raise_error(Cast.CastError, [] | [integer] ~> [atom])
##    assert_raise_error(Cast.CastError, [] | [integer] ~> integer)
##    assert_raise_error(Cast.CastError, [] | [integer] ~> {any})
##    assert_raise_error(Cast.CastError, [1, 2] | [integer] ~> [float])
##    assert_raise_error(Cast.CastError, [1, 2] | [integer] ~> [])
##
##    assert_raise_error(Cast.BadArgumentError, {} | [] ~> any)
##    assert_raise_error(Cast.BadArgumentError, [] | {any} ~> [])
##    assert_raise_error(Cast.BadArgumentError, [1, 2] | [] ~> [])
#
#    IO.inspect({} | any ~> {any, any})
#    assert_raise_error(Cast.CastError, {} | {} ~> {any, any})
#    assert_raise_error(Cast.CastError, {1} | {any} ~> {any, any})
#    assert_raise_error(Cast.CastError, {1, 2} | {integer, float} ~> {integer})
#    assert_raise_error(Cast.CastError, {1, 2} | {any, any} ~> {any})
#    assert_raise_error(Cast.CastError, {1, 2} | {any, any} ~> {any})
#
#    assert_raise_error(Cast.BadArgumentError, {} | {any} ~> {any, any})
#    assert_raise_error(Cast.BadArgumentError, {1} | {any, any} ~> {any})
#    assert_raise_error(Cast.BadArgumentError, {1} | {any, any} ~> {any, any, any})
#
#    assert_raise_error(Cast.CastError, %{:a => 1} | %{} ~> %{:a => integer})
#    assert_raise_error(Cast.CastError, %{:a => 1} | %{:a => any} ~> %{})
#    assert_raise_error(Cast.CastError, %{:a => 1} | %{:a => any} ~> %{:b => any})
#    assert_raise_error(Cast.CastError, %{:a => 1} | %{:a => integer} ~> %{:b => integer})
#    assert_raise_error(Cast.CastError, %{:a => 1} | %{:a => integer} ~> %{:b => float})
#    assert_raise_error(Cast.CastError, %{:a => {1}} | %{:a => {any}} ~> %{:a => {any, any}})
#
#    assert_raise_error(Cast.BadArgumentError, %{:a => 1} | %{:b => any} ~> %{:a => integer})
#    assert_raise_error(Cast.BadArgumentError, %{:a => 1} | %{:b => integer} ~> %{:a => integer})
#
#    assert (1 | integer ~> number) === 1
#  end
#
#  @tag disabled: true
#  test "factor_app" do
#    untyped_plus1 = (fn x -> x + 1 end | (any -> any) ~> (any -> any))
#    integer_plus1_to_untyped = (fn x -> x + 1 end | (integer -> integer) ~> (any -> any))
#    integer_number_plus1_to_untyped = (fn x -> x + 1 end | (integer -> number) ~> (any -> any))
#    number_integer_plus1_to_untyped = (fn x -> x + 1 end | (number -> integer) ~> (any -> any))
#    number_plus1_to_untyped = (fn x -> x + 1 end | (number -> number) ~> (any -> any))
#    untyped_plus1_to_integer = (fn x -> x + 1 end | (any -> any) ~> (integer -> integer))
#    untyped_plus1_to_integer_number = (fn x -> x + 1 end | (any -> any) ~> (integer -> number))
#    untyped_plus1_to_number_integer = (fn x -> x + 1 end | (any -> any) ~> (number -> integer))
#    untyped_plus1_to_number = (fn x -> x + 1 end | (any -> any) ~> (number -> number))
#
#    for {function, input, result} <- [
#          # input 1
#          {untyped_plus1, 1, {:ok, 2}},
#          {integer_plus1_to_untyped, 1, {:ok, 2}},
#          {integer_number_plus1_to_untyped, 1, {:ok, 2}},
#          {number_integer_plus1_to_untyped, 1, {:ok, 2}},
#          {number_plus1_to_untyped, 1, {:ok, 2}},
#          {untyped_plus1_to_integer, 1, {:ok, 2}},
#          {untyped_plus1_to_integer_number, 1, {:ok, 2}},
#          {untyped_plus1_to_number_integer, 1, {:ok, 2}},
#          {untyped_plus1_to_number, 1, {:ok, 2}},
#          # input 1.0
#          {untyped_plus1, 1.0, {:ok, 2.0}},
#          {integer_plus1_to_untyped, 1.0, {:cast_error, "Couldn't cast 1.0 from type :any into :integer"}},
#          {integer_number_plus1_to_untyped, 1.0, {:cast_error, "Couldn't cast 1.0 from type :any into :integer"}},
#          {number_integer_plus1_to_untyped, 1.0, {:cast_error, "Couldn't cast 2.0 from type :integer into :any"}},
#          {number_plus1_to_untyped, 1.0, {:ok, 2.0}},
#          {untyped_plus1_to_integer, 1.0, {:cast_error, "Couldn't cast 1.0 from type :integer into :any"}},
#          {untyped_plus1_to_integer_number, 1.0, {:cast_error, "Couldn't cast 1.0 from type :integer into :any"}},
#          {untyped_plus1_to_number_integer, 1.0, {:cast_error, "Couldn't cast 2.0 from type :any into :integer"}},
#          {untyped_plus1_to_number, 1.0, {:ok, 2.0}},
#          # input :a
#          {untyped_plus1, :a, {:arithmethic_error, "bad argument in arithmetic expression"}},
#          {integer_plus1_to_untyped, :a, {:cast_error, "Couldn't cast :a from type :any into :integer"}},
#          {integer_number_plus1_to_untyped, :a, {:cast_error, "Couldn't cast :a from type :any into :integer"}},
#          {number_integer_plus1_to_untyped, :a, {:cast_error, "Couldn't cast :a from type :any into :number"}},
#          {number_plus1_to_untyped, :a, {:cast_error, "Couldn't cast :a from type :any into :number"}},
#          {untyped_plus1_to_integer, :a, {:cast_error, "Couldn't cast :a from type :integer into :any"}},
#          {untyped_plus1_to_integer_number, :a, {:cast_error, "Couldn't cast :a from type :integer into :any"}},
#          {untyped_plus1_to_number_integer, :a, {:cast_error, "Couldn't cast :a from type :number into :any"}},
#          {untyped_plus1_to_number, :a, {:cast_error, "Couldn't cast :a from type :number into :any"}}
#        ] do
#      case result do
#        {:ok, output} ->
#          assert function.(input) == output
#
#        {:cast_error, message} ->
#          assert_raise_error_with_message(Cast.CastError, message, function.(input))
#
#        {:arithmethic_error, message} ->
#          assert_raise_error_with_message(ArithmeticError, message, function.(input))
#      end
#    end
##
##    untyped_evaluator = (fn f, x -> f.(x) end | ({(any -> any), any} -> any) ~> ({(any -> any), any} -> any))
##    assert untyped_evaluator.(untyped_plus1, 1) = 2
#  end
#
#  @tag disabled: true
#  test "wip" do
#    untyped_plus1 = (fn x -> x + 1 end | (any -> any) ~> (any -> any))
#    untyped_duplicator = (fn f, x -> f.(x) + f.(x) end | ((any -> any), any -> any) ~> ((any -> any), any -> any))
#    untyped_duplicator_into_integer_integer_untyped = (
#      fn f, x -> f.(x) + f.(x) end | ((any -> any), any -> any) ~> ((integer -> integer), any -> any)
#    )
#    untyped_duplicator_into_integer_number_untyped = (
#      fn f, x -> f.(x) + f.(x) end | ((any -> any), any -> any) ~> ((integer -> integer), any -> any)
#    )
#    untyped_duplicator_into_number_integer_untyped = (
#      fn f, x -> f.(x) + f.(x) end | ((any -> any), any -> any) ~> ((number -> integer), any -> any)
#    )
#    untyped_duplicator_into_number_number_untyped = (
#      fn f, x -> f.(x) + f.(x) end | ((any -> any), any -> any) ~> ((number -> number), any -> any)
#    )
#
#
#    for {function, {input1, input2}, result} <- [
#      # input untyped_plus1, 1
#      {untyped_duplicator, {untyped_plus1, 1}, {:ok, 4}},
#      {untyped_duplicator_into_integer_integer_untyped, {untyped_plus1, 1}, {:ok, 4}},
#      {untyped_duplicator_into_integer_number_untyped, {untyped_plus1, 1}, {:ok, 4}},
#      {untyped_duplicator_into_number_integer_untyped, {untyped_plus1, 1}, {:ok, 4}},
#      {untyped_duplicator_into_number_number_untyped, {untyped_plus1, 1}, {:ok, 4}},
#      # input untyped_plus1, 1.0
#      {untyped_duplicator, {untyped_plus1, 1.0}, {:ok, 4.0}},
#      {untyped_duplicator_into_integer_integer_untyped, {untyped_plus1, 1.0}, {:cast_error, "Couldn't cast 1.0 from type :any into :integer"}},
#      {untyped_duplicator_into_integer_number_untyped, {untyped_plus1, 1.0}, {:cast_error, "Couldn't cast 1.0 from type :any into :integer"}},
#      {untyped_duplicator_into_number_integer_untyped, {untyped_plus1, 1.0}, {:cast_error, "Couldn't cast 2.0 from type :integer into :any"}},
#      {untyped_duplicator_into_number_number_untyped, {untyped_plus1, 1.0}, {:ok, 4.0}},
#      # input untyped_plus1, :a
#      {untyped_duplicator, {untyped_plus1, :a}, {:arithmethic_error, "bad argument in arithmetic expression"}},
#      {untyped_duplicator_into_integer_integer_untyped, {untyped_plus1, :a}, {:cast_error, "Couldn't cast :a from type :any into :integer"}},
#      {untyped_duplicator_into_integer_number_untyped, {untyped_plus1, :a}, {:cast_error, "Couldn't cast :a from type :any into :integer"}},
#      {untyped_duplicator_into_number_integer_untyped, {untyped_plus1, :a}, {:cast_error, "Couldn't cast :a from type :any into :number"}},
#      {untyped_duplicator_into_number_number_untyped, {untyped_plus1, :a}, {:cast_error, "Couldn't cast :a from type :any into :number"}}
#    ] do
#      case result do
#        {:ok, output} ->
#          assert function.(input1, input2) == output
#
#        {:cast_error, message} ->
#          assert_raise_error_with_message(Cast.CastError, message, function.(input1, input2))
#
#        {:arithmethic_error, message} ->
#          assert_raise_error_with_message(ArithmeticError, message, function.(input1, input2))
#      end
#    end
##
#  end
end
