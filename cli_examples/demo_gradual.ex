defmodule Demo do
  @spec foo_cond(integer, any, any) :: any

  def foo_cond(x, y, b) do
    x = max(2.0, x)

    cond do
      b -> x
      true -> y
    end

    x + 1
  end
end