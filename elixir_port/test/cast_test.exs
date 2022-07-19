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

  def sum(x, y), do: x + y

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

  # @tag disabled: true
  test "d_tuple_cast" do
    assert ({} | {} ~> {}) == {}
    assert ({} | any ~> any) == {}
    assert ({} | {} ~> any) == {}
    assert ({} | any ~> {}) == {}
    assert ({1, 2.0} | {integer, float} ~> {integer, float}) == {1, 2.0}
    assert ({1, 2.0} | {integer, float} ~> any) == {1, 2.0}
    assert ({1, 2.0} | {integer, float} ~> {any, any}) == {1, 2.0}
    assert ({1, 2.0} | {integer, float} ~> {integer, any}) == {1, 2.0}
    assert ({1, 2.0} | {integer, float} ~> {any, float}) == {1, 2.0}
    assert ({1, 2.0} | {number, number} ~> {number, number}) == {1, 2.0}
    assert ({1, 2.0} | {number, number} ~> any) == {1, 2.0}
    assert ({1, 2.0} | {number, number} ~> {any, any}) == {1, 2.0}
    assert ({1, 2.0} | {number, number} ~> {any, number}) == {1, 2.0}
    assert ({1, 2.0} | {number, number} ~> {number, any}) == {1, 2.0}
    assert ({1, 2.0} | any ~> any) == {1, 2.0}
    assert ({1, 2.0} | any ~> {integer, float}) == {1, 2.0}
    assert ({1, 2.0} | {any, float} ~> {integer, float}) == {1, 2.0}
    assert ({1, 2.0} | {integer, any} ~> {integer, float}) == {1, 2.0}

    assert_raise_error(Cast.CastError, {} | any ~> [])
    assert_raise_error(Cast.CastError, {} | any ~> {any})
    assert_raise_error(Cast.CastError, {1, 2.0} | any ~> {integer, integer})
    assert_raise_error(Cast.CastError, {1, 2.0} | any ~> {float, number})
    assert_raise_error(Cast.CastError, {1, 2.0} | any ~> {number, integer})
    assert_raise_error(Cast.CastError, {1, 2.0} | {any, any} ~> {number, integer})
    assert_raise_error(Cast.CastError, {1, 2.0} | {number, any} ~> {number, integer})

    assert_raise_error(Cast.BadArgumentError, {} | {any} ~> {})
    assert_raise_error(Cast.BadArgumentError, {1, 2.0} | {integer, integer} ~> any)
    assert_raise_error(Cast.BadArgumentError, {1, 2.0} | {float, float} ~> any)
    assert_raise_error(Cast.BadArgumentError, {1, 2.0} | {integer, integer} ~> {integer, integer})
    assert_raise_error(Cast.BadArgumentError, {1, 2.0} | {float, float} ~> {float, float})
    assert_raise_error(Cast.BadArgumentError, {1, 2.0} | {integer, float} ~> {number, float})
    assert_raise_error(Cast.BadArgumentError, {1, 2.0} | {integer, float} ~> {integer, number})
    assert_raise_error(Cast.BadArgumentError, {1, 2.0} | {integer, float} ~> {integer, float, any})
    assert_raise_error(Cast.BadArgumentError, {1, 2.0} | {integer, float, any} ~> {integer, float, any})
  end

  # @tag disabled: true
  test "d_map_cast" do
    assert (%{} | %{} ~> %{}) == %{}
    assert (%{} | any ~> any) == %{}
    assert (%{} | %{} ~> any) == %{}
    assert (%{} | any ~> %{}) == %{}
    assert (%{:a => 1} | %{} ~> %{}) == %{:a => 1}

    assert (%{:a => 1, :b => 2.0} | %{:a => integer, :b => float} ~> %{:a => integer, :b => float}) == %{:a => 1, :b => 2.0}
    assert (%{:a => 1, :b => 2.0} | %{:a => integer} ~> %{:a => integer}) == %{:a => 1, :b => 2.0}
    assert (%{:a => 1, :b => 2.0} | %{:a => number} ~> %{:a => number}) == %{:a => 1, :b => 2.0}
    assert (%{:a => 1, :b => 2.0} | %{:b => float} ~> %{:b => float}) == %{:a => 1, :b => 2.0}
    assert (%{:a => 1, :b => 2.0} | any ~> any) == %{:a => 1, :b => 2.0}
    assert (%{:a => 1, :b => 2.0} | any ~> %{:a => integer}) == %{:a => 1, :b => 2.0}
    assert (%{:a => 1, :b => 2.0} | any ~> %{:a => integer, :b => any}) == %{:a => 1, :b => 2.0}
    assert (%{:a => 1, :b => 2.0} | %{:a => integer} ~> any) == %{:a => 1, :b => 2.0}
    assert (%{:a => 1, :b => 2.0} | %{:a => integer, :b => any} ~> any) == %{:a => 1, :b => 2.0}

    assert_raise_error(Cast.CastError, %{:a => 1, :b => 2.0} | any ~> %{:a => float})
    assert_raise_error(Cast.CastError, %{:a => 1, :b => 2.0} | any ~> %{:b => integer})
    assert_raise_error(Cast.CastError, %{:a => 1, :b => 2.0} | %{:b => any} ~> %{:b => integer})
    assert_raise_error(Cast.CastError, %{:a => 1, :b => 2.0} | any ~> %{:c => any})

    assert_raise_error(Cast.BadArgumentError, %{} | %{:a => any} ~> %{:a => any})
    assert_raise_error(Cast.BadArgumentError, %{:a => 1} | %{:b => any} ~> %{:b => any})
    assert_raise_error(Cast.BadArgumentError, %{:a => 1} | %{:b => any} ~> any)
    assert_raise_error(Cast.BadArgumentError, %{:a => 1, :b => 2.0} | %{:a => integer} ~> %{:b => number})
    assert_raise_error(Cast.BadArgumentError, %{:a => 1, :b => 2.0} | %{:a => any} ~> %{:b => any})
    assert_raise_error(Cast.BadArgumentError, %{:a => 1, :b => 2.0} | %{:b => any} ~> %{:a => any})
    assert_raise_error(Cast.BadArgumentError, %{:a => 1, :b => 2.0} | %{:b => any} ~> %{:a => any, :b => any})
  end


#  # @tag disabled: true
  test "d_fun_cast" do
    untyped_plus1 = (fn x -> x + 1 end | (any -> any) ~> (any -> any))
    integer_integer_plus1_to_untyped = (fn x -> x + 1 end | (integer -> integer) ~> (any -> any))
    integer_number_plus1_to_untyped = (fn x -> x + 1 end | (integer -> number) ~> (any -> any))
    number_integer_plus1_to_untyped = (fn x -> x + 1 end | (number -> integer) ~> (any -> any))
    number_number_plus1_to_untyped = (fn x -> x + 1 end | (number -> number) ~> (any -> any))
    untyped_plus1_to_integer_integer= (fn x -> x + 1 end | (any -> any) ~> (integer -> integer))
    untyped_plus1_to_integer_number = (fn x -> x + 1 end | (any -> any) ~> (integer -> number))
    untyped_plus1_to_number_integer = (fn x -> x + 1 end | (any -> any) ~> (number -> integer))
    untyped_plus1_to_number_number = (fn x -> x + 1 end | (any -> any) ~> (number -> number))

    for {function, input, result} <- [
          # input 1
          {untyped_plus1, 1, {:ok, 2}},
          {integer_integer_plus1_to_untyped, 1, {:ok, 2}},
          {integer_number_plus1_to_untyped, 1, {:ok, 2}},
          {number_integer_plus1_to_untyped, 1, {:ok, 2}},
          {number_number_plus1_to_untyped, 1, {:ok, 2}},
          {untyped_plus1_to_integer_integer,1, {:ok, 2}},
          {untyped_plus1_to_integer_number, 1, {:ok, 2}},
          {untyped_plus1_to_number_integer, 1, {:ok, 2}},
          {untyped_plus1_to_number_number, 1, {:ok, 2}},
#          # input 1.0
          {untyped_plus1, 1.0, {:ok, 2.0}},
          {integer_integer_plus1_to_untyped, 1.0, {:cast_error, "Couldn't cast 1.0 from type :float into :integer"}},
          {integer_number_plus1_to_untyped, 1.0, {:cast_error, "Couldn't cast 1.0 from type :float into :integer"}},
          {number_integer_plus1_to_untyped, 1.0, {:bad_argument_error, "Cast is forbidden: 2.0 is not of type :integer"}},
          {number_number_plus1_to_untyped, 1.0, {:ok, 2.0}},
          {untyped_plus1_to_integer_integer,1.0, {:bad_argument_error, "Cast is forbidden: 1.0 is not of type :integer"}},
          {untyped_plus1_to_integer_number, 1.0, {:bad_argument_error, "Cast is forbidden: 1.0 is not of type :integer"}},
          {untyped_plus1_to_number_integer, 1.0, {:cast_error, "Couldn't cast 2.0 from type :float into :integer"}},
          {untyped_plus1_to_number_number, 1.0, {:ok, 2.0}},
#          # input :a
          {untyped_plus1, :a, {:arithmethic_error, "bad argument in arithmetic expression"}},
          {integer_integer_plus1_to_untyped, :a, {:cast_error, "Couldn't cast :a from type {:atom, :a} into :integer"}},
          {integer_number_plus1_to_untyped, :a, {:cast_error, "Couldn't cast :a from type {:atom, :a} into :integer"}},
          {number_number_plus1_to_untyped, :a, {:cast_error, "Couldn't cast :a from type {:atom, :a} into :number"}},
          {untyped_plus1_to_integer_integer,:a, {:bad_argument_error, "Cast is forbidden: :a is not of type :integer"}},
          {untyped_plus1_to_integer_number, :a, {:bad_argument_error, "Cast is forbidden: :a is not of type :integer"}},
          {untyped_plus1_to_number_integer, :a, {:bad_argument_error, "Cast is forbidden: :a is not of type :number"}},
          {untyped_plus1_to_number_number, :a, {:bad_argument_error, "Cast is forbidden: :a is not of type :number"}}
        ] do
      case result do
        {:ok, output} ->
          assert function.(input) == output

        {:cast_error, message} ->
          assert_raise_error_with_message(Cast.CastError, message, function.(input))

        {:bad_argument_error, message} ->
          assert_raise_error_with_message(Cast.BadArgumentError, message, function.(input))

        {:arithmethic_error, message} ->
          assert_raise_error_with_message(ArithmeticError, message, function.(input))
      end
    end


    # arity related asserts
    sum = &sum/2
    assert (((sum | any ~> (any, any -> any)))).(1, 2) === 3
    assert_raise_error(Cast.CastError, (((sum | any ~> (any -> any)))))
    assert (((sum | ((integer, integer) -> integer) ~> any) | any ~> (any, any -> any))).(1, 2) === 3
    assert_raise_error(Cast.CastError, (((sum | ((integer, integer) -> integer) ~> any) | any ~> (any -> any))))

    assert_raise_error(Cast.BadArgumentError, (((sum | (any -> any) ~> any))))
    assert_raise_error(Cast.BadArgumentError, (((sum | (any -> any) ~> (any -> any)))))
    assert_raise_error(Cast.BadArgumentError, (((sum | ((any, any) -> any) ~> (any -> any)))))
  end

  test "miscellanea" do
    assert (1.0 + 1 | any ~> float) == 2.0
    assert_raise_error(Cast.CastError,
       cond do
         1 | any ~> boolean -> true
       end
     )
  end
end
