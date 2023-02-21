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
    x = 1
    anonymous_inc = &inc/1
    anonymous_unc = &unc/1
    untyped_anonymous_inc = untyped((&inc/1) | (integer -> integer) ~> any)
    untyped_anonymous_unc = untyped((&unc/1) | (any -> any) ~> any)
    inc(x)
    unc(x | integer ~> any)
    anonymous_inc.(x)
    anonymous_unc.(x | integer ~> any)
    (untyped_anonymous_inc | any ~> (any -> any)).(x | integer ~> any)
    (untyped_anonymous_unc | any ~> (any -> any)).(x | integer ~> any)
  end
end