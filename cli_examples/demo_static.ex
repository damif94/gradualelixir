defmodule Demo do
  @spec foo_number_ops(integer, float, number) :: {}

  def foo_number_ops(x, y, z) do
    x + y

    x + x

    max(x, y)

    rem(x, x)

    {}
  end

  @spec foo_cond(integer, integer, boolean) :: integer

  def foo_cond(x, y, b) do
    cond do
      b -> x
      true -> y
    end
  end
end