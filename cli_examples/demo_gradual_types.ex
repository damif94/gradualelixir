defmodule Demo do
  use UseCast

  @spec foo_cond(integer, any, any) :: any

  def foo_cond(x, y, b) do
    x = (max(2.0 | float, x | integer) | number) | number

    cond do
      b | any -> x | number
      true -> y | any
    end
    | number

    ((x | number) + (1 | integer) | number) | number
  end
end