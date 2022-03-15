defmodule Demo do
  @spec foo_cond(integer, any, any) :: integer

  def foo_cond(x, y, b) do
    cond do
      b -> x
      true -> y
    end

    x + 1
  end
end