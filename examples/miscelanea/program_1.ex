defmodule Program do
  @spec sum(number, number) :: number
  def sum(x, y) do
    x + y
  end

  def untyped_sum(x, y) do
    x + y
  end

  @spec main() :: integer
  def main do
    sum(1, 2)
  end
end