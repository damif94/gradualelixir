defmodule Demo do
  use UseCast

  @spec foo(integer) :: number
  def foo(x) do
    1 + 1 | integer
  end

  @spec baz({integer, number}, {number, integer}) :: integer
  def baz(x, y) do
    {{_, z}, {1.0, z}} = ({x, y} | {{integer, number}, {number, integer}})
    | {{integer, number}, {number, integer}}

    (z | integer) | integer
  end

  @spec gaz({integer, number}, {number, integer}) :: {integer, integer}
  def gaz({x, x}, {y, y}) do
    {x, y} | {integer, integer}
  end

  @spec foo_cond(integer, float, boolean) :: {number, integer}
  def foo_cond(x, y, b) do
    u =
      (cond do
         b -> x | integer
         not b -> y | float
       end
       | number)
    | number

    ({u, x + 1} | {number, integer}) | {number, integer}
  end

  @spec foo_cond_fun((number -> integer), (float -> float)) :: (float -> number)
  def foo_cond_fun(x, y) do
    cond do
      true or false -> x | (number -> integer)
      false and true -> y | (float -> float)
    end
    | (float -> number)
  end

  @spec foo_case({integer, float}) :: number
  def foo_case(p) do
    case p | {integer, float} do
      {x, _} -> x | integer
      {_, y} -> y | float
    end
    | number
  end

  @spec foo_seq({integer, float}) :: number
  def foo_seq(p) do
    {x, y} = (p | {integer, float}) | {integer, float}

    (
      x | integer
      (y | float) | float
    )
    | float
  end
end