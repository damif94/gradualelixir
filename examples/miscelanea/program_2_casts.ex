defmodule Program do
  use UseCast

  @spec untyped(any) :: any
  def untyped(value) do
    value
  end

  @spec sum(integer, integer) :: integer
  def sum(x, y) do
    x + y
  end

  @spec main(any) :: any
  def main(options) do
    choice = 1
    untyped_sum = untyped((&sum/2) | (integer, integer -> integer) ~> any)

    case choice do
      1 -> (untyped_sum | any ~> (any, any -> any)).(1 | integer ~> any, 2 | integer ~> any)
      2 -> (untyped_sum | any ~> (any -> any)).(1 | integer ~> any)
      3 -> (untyped_sum | any ~> (any, any -> any)).(1 | integer ~> any, 2.0 | float ~> any)
      4 -> (untyped_sum | any ~> (any, any -> any)).(true | true ~> any, 1 | integer ~> any)
    end
  end
end