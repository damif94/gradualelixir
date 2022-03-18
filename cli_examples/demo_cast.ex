defmodule Demo do
  @spec foo_cond(integer, any, any) :: integer

  def foo_cond(x, y, b) do
    cond do
      b -> x
      true -> y
    end
  end
end

[x, {y, z}] | {integer, any}  ~> {integer, float}
{x | integer ~> integer, {y, z}| {integer, any}  ~> {integer, float}}