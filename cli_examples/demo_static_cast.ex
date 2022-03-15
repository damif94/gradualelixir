defmodule Demo do
  use UseCast

  @spec foo_number_ops(integer, float, number) :: {}

  def foo_number_ops(x, y, z) do
    (x | integer) + (y | float) | float

    (x | integer) + (x | integer) | integer

    max(x | integer, y | float) | number

    rem(x | integer, x | integer) | integer

    {} | {}
  end

  @spec foo_cond(integer, integer, boolean) :: integer

  def foo_cond(x, y, b) do
    cond do
      b | boolean -> x | integer
      true -> y | integer
    end
    | integer
  end
end