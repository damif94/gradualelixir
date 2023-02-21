defmodule Program do
  use UseCast

  @spec iterate((any -> any), integer, any) :: any
  def iterate(f, 0, x) do
    x
  end

  def iterate(f, n, x) do
    ff = &iterate/3
    f.(ff.(f, n - 1, x))
  end

  @spec inc(number) :: number
  def inc(x) do
    x + 1
  end

  @spec main() :: any
  def main() do
    iterate((&inc/1) | (number -> number) ~> (any -> any), 10, 4 | integer ~> any)
  end
end