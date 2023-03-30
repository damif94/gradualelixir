defmodule Program do
  @spec sum(number, number) :: number
  def sum(x, y) do
    x + y
  end

  def untyped(x) do
    x
  end

  @spec main() :: number
  def main do
    sum("1", 2)
  end
end