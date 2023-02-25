defmodule Program do
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
    map(&succ/1, l)
  end

  def untyped(x) do
    x
  end

  def main do
#    map_succ(untyped([true]))
    map_succ(untyped(true))
  end
end