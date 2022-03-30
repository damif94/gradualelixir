defmodule Demo do
  use UseCast

  @spec list_length([any]) :: integer
  def list_length(l) do
    case l do
      [] -> 0
      [_ | tail] -> 1 + list_length(tail)
    end
  end

  @spec filter((any -> boolean), [any]) :: [any]
  def filter(f, l) do
    case l do
      [] ->
        []

      [head | tail] ->
        filtered_tail = filter(f, tail)

        if f.(head) do
          [head | filtered_tail]
        else
          filtered_tail
        end
    end
  end

  @spec is_positive(integer) :: boolean
  def is_positive(x) do
    (x | integer ~> boolean) >= (0 | integer ~> boolean)
  end

  @spec untyped(any) :: any
  def untyped(value) do
    value
  end

  @spec filter_positive([integer]) :: [integer]
  def filter_positive(l) do
    filter((&is_positive/1) | (integer -> boolean) ~> (any -> boolean), l | [integer] ~> [any])
    | [any] ~> [integer]
  end

  @spec main(any) :: any
  def main(options) do
    choice =
      case options do
        %{:choice => v} -> v
        _ -> 1
      end

    IO.inspect(choice)
    l =
      case choice do
        1 -> [1 | [2 | [3 | []]]]
        2 -> untyped([1 | [2.0 | [3 | []]]])
        3 -> [true | []]
        4 -> untyped(42)
      end
      IO.inspect(l)

    filter_positive(l | [any] ~> [integer]) | [integer] ~> any
  end
end