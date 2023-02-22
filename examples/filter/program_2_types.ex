defmodule Program do
  use UseCast

  @spec filter((any -> boolean), [any]) :: [any]
  def filter(f, l) do
    case l | [any] do
      [] ->
        []

      [head | tail] ->
        filtered_tail = (filter(f | (any -> boolean), tail | [any]) | [any]) | [any]

        if (f | (any -> boolean)).(head | any) | boolean do
          [(head | any) | filtered_tail | [any]] | [any]
        else
          filtered_tail | [any]
        end
        | [any]
    end
    | [any]
  end

  @spec is_positive(number) :: boolean
  def is_positive(x) do
    x >= 0 | boolean
  end

  @spec filter_positive([number]) :: [number]
  def filter_positive(l) do
    f = (filter((&is_positive/1) | (number -> boolean), l | [number]) | [any]) | [any]
    f | [any]
  end

  @spec untyped(any) :: any
  def untyped(value) do
    value | any
  end

  @spec main() :: any
  def main() do
    choice = 1 | integer

    l =
      (case choice | integer do
         1 -> [1 | [(-(2 | integer) | integer) | [3 | []] | [integer]] | [integer]] | [integer]
         2 -> untyped([1 | [2.0 | [3 | []] | [integer]] | [number]] | [number]) | any
         3 -> [true | []] | [true]
         4 -> untyped(42) | any
       end
       | [any])
    | [any]

    (filter_positive(l | [any]) | [number]) | [number]
  end
end