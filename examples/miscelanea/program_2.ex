defmodule Program do
  def untyped(value) do
    value
  end

  @spec sum(integer, integer) :: integer
  def sum(x, y) do
    x + y
  end

  def main do
    choice = 1
    untyped_sum = untyped(&sum/2)

    case choice do
      1 -> untyped_sum.(1, 2)
      2 -> untyped_sum.(1)
      3 -> untyped_sum.(1, 2.0)
      4 -> untyped_sum.(true, 1)
    end
  end
end