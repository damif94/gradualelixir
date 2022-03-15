defmodule Demo do
  use UseCast

  @spec foo(integer) :: number
  def foo(x) do
    case x do
      0 -> 0
      n -> n + 1
    end
    | any ~> integer
    x | ({integer, number, (() -> float), []}, float, [integer] -> integer)
  end

  def baz(f, x) do
    f | (integer -> integer) ~> (integer -> integer)
  end

  def gaz(x) do
    x | any ~> (integer -> integer)
  end

  def gaz(x, y, z) do
    x | any ~> integer
    y | {any, any} ~> {integer, integer}
    z | any ~> {integer, integer}
  end
 end
