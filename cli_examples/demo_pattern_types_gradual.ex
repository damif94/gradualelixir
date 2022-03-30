defmodule Demo do
  use UseCast

  @spec foo() :: {}

  def foo() do
    x = 1 | integer

    y = 1.0 | float

    z = (max(x | integer, y | float) | number) | number

    {u, u} = ({z, y} | {number, float}) | {float, float}

    {1, z} | {integer, number}

    %{1 => {u, v}, 2 => v} = %{1 => any_value(), 2 => x} | %{1 => {any, integer}, 2 => integer}

    ({} | {}) | {}
  end

  @spec any_value() :: any

  def any_value() do
    {} | {}
  end
end