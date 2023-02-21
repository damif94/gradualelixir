defmodule Program do
  use UseCast

  @spec untyped(any) :: any
  def untyped(x) do
    x
  end

  @spec inc(integer) :: integer
  def inc(x) do
    x + 1
  end

  @spec unc(any) :: any
  def unc(x) do
    (x | any ~> number) + 1 | number ~> any
  end

  @spec main() :: any
  def main() do
    x = untyped(:a | :a ~> any)
    anonymous_inc = &inc/1
    anonymous_unc = &unc/1
    untyped_anonymous_inc = untyped((&inc/1) | (integer -> integer) ~> any)
    untyped_anonymous_unc = untyped((&unc/1) | (any -> any) ~> any)
    inc(x | any ~> integer)
    unc(x)
    anonymous_inc.(x | any ~> integer)
    anonymous_unc.(x)
    (untyped_anonymous_inc | any ~> (any -> any)).(x)
    (untyped_anonymous_unc | any ~> (any -> any)).(x)
  end
end