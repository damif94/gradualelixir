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
    choice =
      case options do
        %{:choice => v} -> v
        _ -> 1 | integer ~> any
      end

    untyped_sum = untyped((&sum/2) | (integer, integer -> integer) ~> any)

    case choice do
      1 -> (untyped_sum | any ~> (any, any -> any)).(1 | integer ~> any, 2 | integer ~> any) | any
      2 -> (untyped_sum | any ~> (any -> any)).(1 | integer ~> any) | any
      3 -> (untyped_sum | any ~> (any -> any)).(1.0 | float ~> any) | any
    end
  end
end