defmodule Program do
  def untyped_sum(x, y) do
    z = 1
    z = 1
    z = 1
    x + (y + 1 + 1 + 1)
    1
    1
  end

  def main() do
    x = &untyped_sum/2
    x.(1, :a)
  end
end