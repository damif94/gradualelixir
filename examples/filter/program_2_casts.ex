defmodule Program do
  use UseCast

  @spec list_length([number]) :: integer
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

  @spec is_positive(number) :: boolean
  def is_positive(x) do
    x >= 0
  end

  @spec filter_positive([number]) :: [number]
  def filter_positive(l) do
    filter((&is_positive/1) | (number -> boolean) ~> (any -> boolean), l | [number] ~> [any])
    | [any] ~> [number]
  end

  @spec untyped(any) :: any
  def untyped(value) do
    value
  end

  @spec main(any) :: any
  def main(options) do
    choice =
      case options do
        %{:choice => v} -> v
        _ -> 1 | integer ~> any
      end

    l =
      case choice do
        1 -> [1 | [2 | [3 | []]]] | [integer] ~> [any]
        2 -> untyped([1 | [2.0 | [3 | []]]] | [number] ~> any) | any ~> [any]
        3 -> [true | []] | [true] ~> [any]
        4 -> untyped(42 | integer ~> any) | any ~> [any]
      end

    filter_positive(l | [any] ~> [number]) | [number] ~> any
  end
end