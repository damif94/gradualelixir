defmodule Demo do
  use UseCast

  @spec foo_data() :: {}
  def foo_data() do
    {1 + 1 | integer, 1 + 1.0 | float} | {integer, float}
    {1 + 1 | integer, max(1, 1.0) | number} | {integer, number}
    []
    [(1 + 1 | integer) | []] | [integer]
    [1 | [1.0 | []] | [float]] | [number]
    [(1 + 1 | integer) | [(max(1, 1.0) | number) | []] | [number]] | [number]
    [:a | [true | [false | []] | [false]] | [boolean]] | [atom]
    %{1 => [true | []] | [true], :a => {1} | {integer}} | %{1 => [true], :a => {integer}}
    ({} | {}) | {}
  end

  @spec foo_pattern({integer, number}, {number, integer}) :: integer
  def foo_pattern(x, y) do
    {{_, z}, {1.0, z}} = ({x, y} | {{integer, number}, {number, integer}})
    | {{integer, integer}, {float, integer}}

    z | integer
  end

  @spec gaz({integer, number}, {number, integer}) :: {integer, integer}
  def gaz({x, x}, {y, y}) do
    {x, y} | {integer, integer}
  end

  @spec foo_cond(integer, float, boolean) :: {number, integer}
  def foo_cond(x, y, b) do
    u =
      (cond do
         b | boolean -> x | integer
         not (b | boolean) | boolean -> y | float
       end
       | number)
    | number

    {u, x + 1 | integer} | {number, integer}
  end

  @spec foo_cond_fun((number -> integer), (float -> float)) :: (float -> number)
  def foo_cond_fun(x, y) do
    cond do
      true or false | true -> x | (number -> integer)
      false and true | false -> y | (float -> float)
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
    x | integer
    (y | float) | float
  end

  @spec foo_fun() :: {}
  def foo_fun() do
    x = ((&foo_seq/1) | ({integer, float} -> number)) | ({integer, float} -> number)
    x.({4, 2.0} | {integer, float}) | number
    ({} | {}) | {}
  end
end