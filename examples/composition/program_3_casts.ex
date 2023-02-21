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

  @spec inc(any) :: any
  def inc(x) do
    (x | any ~> number) + 1 | number ~> any
  end

  @spec main() :: any
  def main() do
    iterate(&inc/1, 10, 4 | integer ~> any)
  end
end