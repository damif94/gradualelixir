defmodule ElixirPortTest do
  use ExUnit.Case
  use UseCast
  alias Cast
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

  @tag disabled: true
  test "base_values_into_any" do
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

    assert_raise_error(Cast.CastError, 1 | float ~> any)
    assert_raise_error(Cast.CastError, 1.0 | integer ~> any)
    assert_raise_error(Cast.CastError, 1 | atom ~> any)
    assert_raise_error(Cast.CastError, 1.0 | atom ~> any)

    assert_raise_error(Cast.CastError, :a | :b ~> any)
    assert_raise_error(Cast.CastError, :a | boolean ~> any)
    assert_raise_error(Cast.CastError, :a | number ~> any)

    assert_raise_error(Cast.CastError, true | :a ~> any)
    assert_raise_error(Cast.CastError, false | :a ~> any)
    assert_raise_error(Cast.CastError, true | false ~> any)
    assert_raise_error(Cast.CastError, false | true ~> any)
    assert_raise_error(Cast.CastError, false | integer ~> any)
  end

  @tag disabled: true
  test "base_values_from_any" do
    assert (1 | any ~> integer) === 1
    assert (1 | any ~> number) === 1

    assert (1.0 | float ~> any) === 1.0
    assert (1.0 | number ~> any) === 1.0

    assert (:a | any ~> :a) === :a
    assert (:a | any ~> atom) === :a

    assert (true | any ~> true) === true
    assert (false | any ~> false) === false
    assert (true | any ~> boolean) === true
    assert (false | any ~> boolean) === false
    assert (true | any ~> atom) === true
    assert (false | any ~> atom) === false

    assert_raise_error(Cast.CastError, 1 | any ~> float)
    assert_raise_error(Cast.CastError, 1.0 | any ~> integer)
    assert_raise_error(Cast.CastError, 1 | any ~> atom)
    assert_raise_error(Cast.CastError, 1.0 | any ~> atom)

    assert_raise_error(Cast.CastError, :a | any ~> :b)
    assert_raise_error(Cast.CastError, :a | any ~> boolean)
    assert_raise_error(Cast.CastError, :a | any ~> number)

    assert_raise_error(Cast.CastError, true | any ~> :a)
    assert_raise_error(Cast.CastError, false | any ~> :a)
    assert_raise_error(Cast.CastError, true | any ~> false)
    assert_raise_error(Cast.CastError, false | any ~> true)
    assert_raise_error(Cast.CastError, false | any ~> integer)
  end

  @tag disabled: true
  test "base_id" do
    assert (1 | integer ~> integer) === 1
    assert (1 | number ~> number) == 1

    assert (1.0 | float ~> float) === 1.0
    assert (1.0 | number ~> number) == 1.0

    assert (:a | :a ~> :a) === :a
    assert (:a | atom ~> atom) === :a

    assert (true | true ~> true) === true
    assert (false | false ~> false) === false
    assert (true | boolean ~> boolean) === true
    assert (false | boolean ~> boolean) === false
    assert (true | atom ~> atom) === true
    assert (false | atom ~> atom) === false

    assert_raise_error(Cast.BadArgumentError, 1 | float ~> float)
  end

  @tag disabled: true
  test "any_id" do
    assert (1 | any ~> any) === 1
    assert (1 | any ~> any) == 1

    assert (1.0 | any ~> any) === 1.0
    assert (1.0 | any ~> any) == 1.0

    assert (:a | any ~> any) === :a
    assert (:a | any ~> any) === :a

    assert (true | any ~> any) === true
    assert (false | any ~> any) === false
    assert (true | any ~> any) === true
    assert (false | any ~> any) === false
    assert (true | any ~> any) === true
    assert (false | any ~> any) === false

    assert ([] | any ~> any) === []
    assert ([1, 1.0] | any ~> any) === [1, 1.0]

    assert ({} | any ~> any) === {}
    assert ({1} | any ~> any) === {1}
    assert ({1, 1.0} | any ~> any) === {1, 1.0}
    assert ({1, 1.0, true} | any ~> any) === {1, 1.0, true}

    assert (%{} | any ~> any) === %{}
    assert (%{:a => 1} | any ~> any) === %{:a => 1}
  end

  @tag disabled: true
  test "ground_id" do
    assert (({} | {} ~> any) | any ~> {}) === {}
    assert (({1} | {any} ~> any) | any ~> {any}) === {1}
    assert ({1, 1.0} | any ~> {any, any}) === {1, 1.0}
    assert ({1, 1.0} | {any, any} ~> any) == {1, 1.0}
    assert (({1, 1.0} | {any, any} ~> any) | any ~> {any, any}) === {1, 1.0}
    assert (({1, 1.0, true} | {any, any, any} ~> any) | any ~> {any, any, any}) === {1, 1.0, true}

    assert (%{} | %{} ~> any) === %{}
    assert ({1, 1.0} | {any, any} ~> {any, any}) === {1, 1.0}

    x = fn z -> z end
    cast_x_1 = x | (any -> any) ~> (any -> any)
    cast_x_2 = (fn z -> x.(z | any ~> any) end | any ~> any)
    assert cast_x_1.(1) == cast_x_2.(1) and cast_x_1.({1, 1.0}) == cast_x_2.({1, 1.0})

    assert_raise_error(Cast.BadArgumentError, {} | {any} ~> {any})
  end

#  @tag disabled: true
  test "ground_fail" do
#    assert_raise_error(Cast.CastError, 1 | any ~> float)
#    assert_raise_error(Cast.CastError, 1 | integer ~> float)
#    assert_raise_error(Cast.CastError, :a | :a ~> :b)
#    assert_raise_error(Cast.CastError, :a | atom ~> :b)
#
#    assert_raise_error(Cast.BadArgumentError, :a | integer ~> :a)
#    assert_raise_error(Cast.BadArgumentError, :a | integer ~> :b)
#
#    assert_raise_error(Cast.CastError, [] | [integer] ~> [atom])
#    assert_raise_error(Cast.CastError, [] | [integer] ~> integer)
#    assert_raise_error(Cast.CastError, [] | [integer] ~> {any})
#    assert_raise_error(Cast.CastError, [1, 2] | [integer] ~> [float])
#    assert_raise_error(Cast.CastError, [1, 2] | [integer] ~> [])
#
#    assert_raise_error(Cast.BadArgumentError, {} | [] ~> any)
#    assert_raise_error(Cast.BadArgumentError, [] | {any} ~> [])
#    assert_raise_error(Cast.BadArgumentError, [1, 2] | [] ~> [])

    IO.inspect({} | any ~> {any, any})
    assert_raise_error(Cast.CastError, {} | {} ~> {any, any})
    assert_raise_error(Cast.CastError, {1} | {any} ~> {any, any})
    assert_raise_error(Cast.CastError, {1, 2} | {integer, float} ~> {integer})
    assert_raise_error(Cast.CastError, {1, 2} | {any, any} ~> {any})
    assert_raise_error(Cast.CastError, {1, 2} | {any, any} ~> {any})

    assert_raise_error(Cast.BadArgumentError, {} | {any} ~> {any, any})
    assert_raise_error(Cast.BadArgumentError, {1} | {any, any} ~> {any})
    assert_raise_error(Cast.BadArgumentError, {1} | {any, any} ~> {any, any, any})

    assert_raise_error(Cast.CastError, %{:a => 1} | %{} ~> %{:a => integer})
    assert_raise_error(Cast.CastError, %{:a => 1} | %{:a => any} ~> %{})
    assert_raise_error(Cast.CastError, %{:a => 1} | %{:a => any} ~> %{:b => any})
    assert_raise_error(Cast.CastError, %{:a => 1} | %{:a => integer} ~> %{:b => integer})
    assert_raise_error(Cast.CastError, %{:a => 1} | %{:a => integer} ~> %{:b => float})
    assert_raise_error(Cast.CastError, %{:a => {1}} | %{:a => {any}} ~> %{:a => {any, any}})

    assert_raise_error(Cast.BadArgumentError, %{:a => 1} | %{:b => any} ~> %{:a => integer})
    assert_raise_error(Cast.BadArgumentError, %{:a => 1} | %{:b => integer} ~> %{:a => integer})

    assert (1 | integer ~> number) === 1
  end

  @tag disabled: true
  test "factor_app" do
    untyped_plus1 = (fn x -> x + 1 end | (any -> any) ~> (any -> any))
    integer_plus1_to_untyped = (fn x -> x + 1 end | (integer -> integer) ~> (any -> any))
    integer_number_plus1_to_untyped = (fn x -> x + 1 end | (integer -> number) ~> (any -> any))
    number_integer_plus1_to_untyped = (fn x -> x + 1 end | (number -> integer) ~> (any -> any))
    number_plus1_to_untyped = (fn x -> x + 1 end | (number -> number) ~> (any -> any))
    untyped_plus1_to_integer = (fn x -> x + 1 end | (any -> any) ~> (integer -> integer))
    untyped_plus1_to_integer_number = (fn x -> x + 1 end | (any -> any) ~> (integer -> number))
    untyped_plus1_to_number_integer = (fn x -> x + 1 end | (any -> any) ~> (number -> integer))
    untyped_plus1_to_number = (fn x -> x + 1 end | (any -> any) ~> (number -> number))

    for {function, input, result} <- [
          # input 1
          {untyped_plus1, 1, {:ok, 2}},
          {integer_plus1_to_untyped, 1, {:ok, 2}},
          {integer_number_plus1_to_untyped, 1, {:ok, 2}},
          {number_integer_plus1_to_untyped, 1, {:ok, 2}},
          {number_plus1_to_untyped, 1, {:ok, 2}},
          {untyped_plus1_to_integer, 1, {:ok, 2}},
          {untyped_plus1_to_integer_number, 1, {:ok, 2}},
          {untyped_plus1_to_number_integer, 1, {:ok, 2}},
          {untyped_plus1_to_number, 1, {:ok, 2}},
          # input 1.0
          {untyped_plus1, 1.0, {:ok, 2.0}},
          {integer_plus1_to_untyped, 1.0, {:cast_error, "Couldn't cast 1.0 from type :any into :integer"}},
          {integer_number_plus1_to_untyped, 1.0, {:cast_error, "Couldn't cast 1.0 from type :any into :integer"}},
          {number_integer_plus1_to_untyped, 1.0, {:cast_error, "Couldn't cast 2.0 from type :integer into :any"}},
          {number_plus1_to_untyped, 1.0, {:ok, 2.0}},
          {untyped_plus1_to_integer, 1.0, {:cast_error, "Couldn't cast 1.0 from type :integer into :any"}},
          {untyped_plus1_to_integer_number, 1.0, {:cast_error, "Couldn't cast 1.0 from type :integer into :any"}},
          {untyped_plus1_to_number_integer, 1.0, {:cast_error, "Couldn't cast 2.0 from type :any into :integer"}},
          {untyped_plus1_to_number, 1.0, {:ok, 2.0}},
          # input :a
          {untyped_plus1, :a, {:arithmethic_error, "bad argument in arithmetic expression"}},
          {integer_plus1_to_untyped, :a, {:cast_error, "Couldn't cast :a from type :any into :integer"}},
          {integer_number_plus1_to_untyped, :a, {:cast_error, "Couldn't cast :a from type :any into :integer"}},
          {number_integer_plus1_to_untyped, :a, {:cast_error, "Couldn't cast :a from type :any into :number"}},
          {number_plus1_to_untyped, :a, {:cast_error, "Couldn't cast :a from type :any into :number"}},
          {untyped_plus1_to_integer, :a, {:cast_error, "Couldn't cast :a from type :integer into :any"}},
          {untyped_plus1_to_integer_number, :a, {:cast_error, "Couldn't cast :a from type :integer into :any"}},
          {untyped_plus1_to_number_integer, :a, {:cast_error, "Couldn't cast :a from type :number into :any"}},
          {untyped_plus1_to_number, :a, {:cast_error, "Couldn't cast :a from type :number into :any"}}
        ] do
      case result do
        {:ok, output} ->
          assert function.(input) == output

        {:cast_error, message} ->
          assert_raise_error_with_message(Cast.CastError, message, function.(input))

        {:arithmethic_error, message} ->
          assert_raise_error_with_message(ArithmeticError, message, function.(input))
      end
    end
#
#    untyped_evaluator = (fn f, x -> f.(x) end | ({(any -> any), any} -> any) ~> ({(any -> any), any} -> any))
#    assert untyped_evaluator.(untyped_plus1, 1) = 2
  end

  @tag disabled: true
  test "wip" do
    untyped_plus1 = (fn x -> x + 1 end | (any -> any) ~> (any -> any))
    untyped_duplicator = (fn f, x -> f.(x) + f.(x) end | ((any -> any), any -> any) ~> ((any -> any), any -> any))
    untyped_duplicator_into_integer_integer_untyped = (
      fn f, x -> f.(x) + f.(x) end | ((any -> any), any -> any) ~> ((integer -> integer), any -> any)
    )
    untyped_duplicator_into_integer_number_untyped = (
      fn f, x -> f.(x) + f.(x) end | ((any -> any), any -> any) ~> ((integer -> integer), any -> any)
    )
    untyped_duplicator_into_number_integer_untyped = (
      fn f, x -> f.(x) + f.(x) end | ((any -> any), any -> any) ~> ((number -> integer), any -> any)
    )
    untyped_duplicator_into_number_number_untyped = (
      fn f, x -> f.(x) + f.(x) end | ((any -> any), any -> any) ~> ((number -> number), any -> any)
    )


    for {function, {input1, input2}, result} <- [
      # input untyped_plus1, 1
      {untyped_duplicator, {untyped_plus1, 1}, {:ok, 4}},
      {untyped_duplicator_into_integer_integer_untyped, {untyped_plus1, 1}, {:ok, 4}},
      {untyped_duplicator_into_integer_number_untyped, {untyped_plus1, 1}, {:ok, 4}},
      {untyped_duplicator_into_number_integer_untyped, {untyped_plus1, 1}, {:ok, 4}},
      {untyped_duplicator_into_number_number_untyped, {untyped_plus1, 1}, {:ok, 4}},
      # input untyped_plus1, 1.0
      {untyped_duplicator, {untyped_plus1, 1.0}, {:ok, 4.0}},
      {untyped_duplicator_into_integer_integer_untyped, {untyped_plus1, 1.0}, {:cast_error, "Couldn't cast 1.0 from type :any into :integer"}},
      {untyped_duplicator_into_integer_number_untyped, {untyped_plus1, 1.0}, {:cast_error, "Couldn't cast 1.0 from type :any into :integer"}},
      {untyped_duplicator_into_number_integer_untyped, {untyped_plus1, 1.0}, {:cast_error, "Couldn't cast 2.0 from type :integer into :any"}},
      {untyped_duplicator_into_number_number_untyped, {untyped_plus1, 1.0}, {:ok, 4.0}},
      # input untyped_plus1, :a
      {untyped_duplicator, {untyped_plus1, :a}, {:arithmethic_error, "bad argument in arithmetic expression"}},
      {untyped_duplicator_into_integer_integer_untyped, {untyped_plus1, :a}, {:cast_error, "Couldn't cast :a from type :any into :integer"}},
      {untyped_duplicator_into_integer_number_untyped, {untyped_plus1, :a}, {:cast_error, "Couldn't cast :a from type :any into :integer"}},
      {untyped_duplicator_into_number_integer_untyped, {untyped_plus1, :a}, {:cast_error, "Couldn't cast :a from type :any into :number"}},
      {untyped_duplicator_into_number_number_untyped, {untyped_plus1, :a}, {:cast_error, "Couldn't cast :a from type :any into :number"}}
    ] do
      case result do
        {:ok, output} ->
          assert function.(input1, input2) == output

        {:cast_error, message} ->
          assert_raise_error_with_message(Cast.CastError, message, function.(input1, input2))

        {:arithmethic_error, message} ->
          assert_raise_error_with_message(ArithmeticError, message, function.(input1, input2))
      end
    end
#
  end
end
