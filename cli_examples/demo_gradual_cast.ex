defmodule Demo do
  use UseCast

  @spec foo_cond(integer, any, any) :: integer

  def foo_cond(x, y, b) do
    cond do
      b -> x | integer ~> any
      true -> y
    end

    x + 1
  end
end