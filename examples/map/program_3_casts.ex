defmodule Program do
  use UseCast

  @spec map((any -> any), [any]) :: [any]
  def map(f, l) do
    case l do
      [] -> []
      [head | tail] -> [f.(head) | map(f, tail)]
    end
  end

  @spec succ(number) :: number
  def succ(x) do
    x + 1
  end

  @spec map_succ([number]) :: [number]
  def map_succ(l) do
    map((&succ/1) | (number -> number) ~> (any -> any), l | [number] ~> [any]) | [any] ~> [number]
  end

  def untyped(x) do
    x
  end

  def main() do
    map_succ(untyped(true | true ~> any) | any ~> [number]) | [number] ~> any
  end
end