defmodule Program do
  use UseCast

  @spec map((any, any -> any), [{any, any}]) :: [any]
  def map(f, l) do
    case l | [{any, any}] do
      [] ->
        []

      [{head1, head2} | tail] ->
        [
          ((f | (any, any -> any)).(head1 | any, head2 | any) | any)
          | map(f | (any, any -> any), tail | [{any, any}])
          | [any]
        ]
        | [any]
    end
    | [any]
  end

  @spec plus(number, number) :: number
  def plus(x, y) do
    x + y | number
  end

  @spec map_plus([{number, number}]) :: [number]
  def map_plus(l) do
    map((&plus/2) | (number, number -> number), l | [{number, number}]) | [any]
  end

  @spec main() :: [number]
  def main() do
    map_plus(
      [
        ({1, 2} | {integer, integer})
        | [
            ({2, 3.0} | {integer, float})
            | [
                ({3.0, 3} | {float, integer})
                | [({4.0, 5.1} | {float, float}) | []]
                | [{float, float}]
              ]
            | [{float, number}]
          ]
        | [{number, number}]
      ]
      | [{number, number}]
    )
    | [number]
  end
end