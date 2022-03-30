defmodule Demo do
  use UseCast

  @spec foo(integer) :: number

  def foo(x) do
    1 + 1 | integer ~> number
  end

  @spec baz({integer, number}, {number, integer}) :: integer

  def baz(x, y) do
    {{_, z}, {1.0, z}} = {x, y}

    z
  end

  @spec gaz({integer, number}, {number, integer}) :: {integer, integer}

  def gaz({x, x}, {y, y}) do
    {x, y}
  end

  @spec foo_cond(integer, float, boolean) :: {number, integer}

  def foo_cond(x, y, b) do
    u =
      cond do
        b -> x
        not b -> y
      end

    {u, x + 1}
  end

  @spec foo_cond_fun((number -> integer), (float -> float)) :: (float -> number)

  def foo_cond_fun(x, y) do
    cond do
      true or (false | false ~> true) -> x | (number -> integer) ~> (float -> number)
      false and (true | true ~> false) -> y | (float -> float) ~> (float -> number)
    end
  end

  @spec foo_case({integer, float}) :: number

  def foo_case(p) do
    case p do
      {x, _} -> x
      {_, y} -> y
    end
  end

  @spec foo_seq({integer, float}) :: number

  def foo_seq(p) do
    {x, y} = p

    x

    y | float ~> number
  end
end