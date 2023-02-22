defmodule Program do
  use UseCast

  @spec filter((number -> boolean), [number]) :: [number]
  def filter(f, l) do
    case l | [number] do
      [] ->
        []

      [head | tail] ->
        filtered_tail = (filter(f | (number -> boolean), tail | [number]) | [number]) | [number]

        if (f | (number -> boolean)).(head | number) | boolean do
          [(head | number) | filtered_tail | [number]] | [number]
        else
          filtered_tail | [number]
        end
        | [number]
    end
    | [number]
  end

  @spec is_positive(number) :: boolean
  def is_positive(x) do
    x >= 0 | boolean
  end

  @spec filter_positive([number]) :: [number]
  def filter_positive(l) do
    filter((&is_positive/1) | (number -> boolean), l | [number]) | [number]
  end

  @spec main() :: any
  def main() do
    filter_positive(
      [1 | [(-(2 | integer) | integer) | [3 | []] | [integer]] | [integer]]
      | [integer]
    )
    | [number]
  end
end