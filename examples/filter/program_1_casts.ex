defmodule Program do
  use UseCast

  @spec filter((number -> boolean), [number]) :: [number]
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
    filter(&is_positive/1, l)
  end

  @spec main() :: [number]
  def main() do
    choice = 1

    l =
      case choice do
        1 -> [1 | [-2 | [3 | []]]]
        2 -> [1 | [2.0 | [3 | []]]]
      end

    filter_positive(l)
  end
end