defmodule Demo do
  use UseCast

  @spec foo_cond() :: {}

  def foo_cond() do
    x = 1 | integer

    y = 1.0 | float

    z = (max(x | integer, y | float) | number) | number

    {u, u} = {z, y} | {float, float}

    u | float

    {} | {}
  end
end