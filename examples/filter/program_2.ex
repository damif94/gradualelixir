defmodule Program do
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
    f = filter(&is_positive/1, l)
    f
  end

  def untyped(value) do
    value
  end

  def main do
    choice = 4

    l =
      case choice do
        1 -> [1 | [-2 | [3 | []]]]
        2 -> untyped([1 | [2.0 | [3 | []]]])
        3 -> [true | []]
        4 -> untyped(42)
      end

    filter_positive(l)
  end
end