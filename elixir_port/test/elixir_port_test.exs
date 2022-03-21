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
#
  @tag disabled: false
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

    assert_raise_error(Cast.BadArgumentError, 1 | float ~> any)
    assert_raise_error(Cast.BadArgumentError, 1.0 | integer ~> any)
    assert_raise_error(Cast.BadArgumentError, 1 | atom ~> any)
    assert_raise_error(Cast.BadArgumentError, 1.0 | atom ~> any)

    assert_raise_error(Cast.BadArgumentError, :a | :b ~> any)
    assert_raise_error(Cast.BadArgumentError, :a | boolean ~> any)
    assert_raise_error(Cast.BadArgumentError, :a | number ~> any)

    assert_raise_error(Cast.BadArgumentError, true | :a ~> any)
    assert_raise_error(Cast.BadArgumentError, false | :a ~> any)
    assert_raise_error(Cast.BadArgumentError, true | false ~> any)
    assert_raise_error(Cast.BadArgumentError, false | true ~> any)
    assert_raise_error(Cast.BadArgumentError, false | integer ~> any)
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

    assert_raise_error(Cast.BadArgumentError, 1 | any ~> float)
    assert_raise_error(Cast.BadArgumentError, 1.0 | any ~> integer)
    assert_raise_error(Cast.BadArgumentError, 1 | any ~> atom)
    assert_raise_error(Cast.BadArgumentError, 1.0 | any ~> atom)

    assert_raise_error(Cast.BadArgumentError, :a | any ~> :b)
    assert_raise_error(Cast.BadArgumentError, :a | any ~> boolean)
    assert_raise_error(Cast.BadArgumentError, :a | any ~> number)

    assert_raise_error(Cast.BadArgumentError, true | any ~> :a)
    assert_raise_error(Cast.BadArgumentError, false | any ~> :a)
    assert_raise_error(Cast.BadArgumentError, true | any ~> false)
    assert_raise_error(Cast.BadArgumentError, false | any ~> true)
    assert_raise_error(Cast.BadArgumentError, false | any ~> integer)
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
    assert (({1, 1.0} | {any, any} ~> any) | any ~> {any, any}) === {1, 1.0}
    assert (({1, 1.0, true} | {any, any, any} ~> any) | any ~> {any, any, any}) === {1, 1.0, true}

    assert (%{} | %{} ~> any) === %{}
    assert ({1, 1.0} | {any, any} ~> {any, any}) === {1, 1.0}

    x = fn z -> z end
    cast_x_1 = x | (any -> any) ~> (any -> any)
    cast_x_2 = ((fn z -> x.(z | any ~> any) end) | any ~> any)
    assert (cast_x_1.(1) == cast_x_2.(1)) and (cast_x_1.({1, 1.0}) == cast_x_2.({1, 1.0}))

    assert_raise_error(Cast.BadArgumentError, {} | {any} ~> {any})
  end

#  @tag disabled: true
  test "ground_fail" do
    assert_raise_error(Cast.CastError, 1 | integer ~> float)
    assert_raise_error(Cast.CastError, :a | :a ~> :b)
    assert_raise_error(Cast.CastError, :a | atom ~> :b)

    assert_raise_error(Cast.BadArgumentError, :a | integer ~> :a)
    assert_raise_error(Cast.BadArgumentError, :a | integer ~> :b)

    assert_raise_error(Cast.CastError, {1, 2} | {integer, float} ~> {integer})
    assert_raise_error(Cast.CastError, {1, 2} | {any, any} ~> {any})
    assert_raise_error(Cast.CastError, {1, 2} | {any, any} ~> {any})
    assert_raise_error(Cast.CastError, {1} | {any} ~> {any, any})

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


end
