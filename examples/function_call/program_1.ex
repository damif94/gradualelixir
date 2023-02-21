defmodule Program do
  def untyped(x) do
    x
  end

  @spec inc(integer) :: integer
  def inc(x) do
    x + 1
  end

  def unc(x) do
    x + 1
  end

  def main do
    x = untyped(:a)
    anonymous_inc = &inc/1
    anonymous_unc = &unc/1
    untyped_anonymous_inc = untyped(&inc/1)
    untyped_anonymous_unc = untyped(&unc/1)
    inc(x)
    unc(x)
    anonymous_inc.(x)
    anonymous_unc.(x)
    untyped_anonymous_inc.(x)
    untyped_anonymous_unc.(x)
  end
end