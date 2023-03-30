defmodule Program do
  @spec sum(string, number) :: string
  def sum(x, "y") do
    x <> "y"
  end

  def untyped(x) do
    x
  end

  @spec main() :: number
  def main do
    sum("a", 2)
  end
end