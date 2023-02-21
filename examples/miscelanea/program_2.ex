defmodule Program do
  def untyped(value) do
    value
  end

  @spec sum(integer, integer) :: integer

  def untyped_apply(f, x) do
    f.(x)
  end

  def main(options) do
    choice =
      case options do
        %{:choice => v} -> v
        _ -> 1
      end

    untyped_sum = untyped(&sum/2)

    case choice do
      1 -> untyped_sum.(1, 2)
      2 -> untyped_sum.(1)
      3 -> untyped_sum.(1.0)
    end
  end
end