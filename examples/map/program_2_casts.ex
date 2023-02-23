defmodule Program do
  use UseCast

  @spec map((any, any -> any), [{any, any}]) :: [any]
  def map(f, l) do
    case l do
      [] -> []
      [{head1, head2} | tail] -> [f.(head1, head2) | map(f, tail)]
    end
  end

  @spec plus(number, number) :: number
  def plus(x, y) do
    x + y
  end

  @spec map_plus([{number, number}]) :: [number]
  def map_plus(l) do
    map(
      (&plus/2) | (number, number -> number) ~> (any, any -> any),
      l | [{number, number}] ~> [{any, any}]
    )
    | [any] ~> [number]
  end

  @spec main() :: [number]
  def main() do
    map_plus([{1, 2} | [{2, 3.0} | [{3.0, 3} | [{4.0, 5.1} | []]]]])
  end
end