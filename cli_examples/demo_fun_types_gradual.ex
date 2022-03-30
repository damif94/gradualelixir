defmodule Demo do
  use UseCast

  @spec list_length([any]) :: integer
  def list_length(l) do
    case l | [any] do
      [] -> 0
      [_ | tail] -> 1 + (list_length(tail | [any]) | integer) | integer
    end
    | integer
  end

  @spec filter((any -> boolean), [any]) :: [any]
  def filter(f, l) do
    case l | [any] do
      [] ->
        []

      [head | tail] ->
        filtered_tail = (filter(f | (any -> boolean), tail | [any]) | [any]) | [any]

        if f.(head | any) | boolean do
          [(head | any) | filtered_tail | [any]] | [any]
        else
          filtered_tail | [any]
        end
        | [any]
    end
    | [any]
  end

  @spec is_positive(integer) :: boolean
  def is_positive(x) do
    x >= 0 | boolean
  end

  @spec untyped(any) :: any
  def untyped(value) do
    value | any
  end

  @spec filter_positive([integer]) :: [integer]
  def filter_positive(l) do
    filter((&is_positive/1) | (integer -> boolean), l | [integer]) | [any]
  end

  @spec main(any) :: any
  def main(options) do
    choice =
      (case options | any do
         %{:choice => v} -> v | any
         _ -> 1
       end
       | any)
    | any

    l =
      (case choice | any do
         1 -> [1 | [2 | [3 | []] | [integer]] | [integer]] | [integer]
         2 -> untyped([1 | [2.0 | [3 | []] | [integer]] | [number]] | [number]) | any
         3 -> [true | []] | [true]
         4 -> untyped(42) | any
       end
       | [any])
    | [any]

    (filter_positive(l | [any]) | [integer]) | [integer]
  end
end