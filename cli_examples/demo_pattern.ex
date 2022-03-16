defmodule Demo do
  @spec foo() :: {}

  def foo() do
    x = 1

    y = 1.0

    z = max(x, y)

    {u, u} = {z, y}

    {1, z}

    %{1 => {u, v}, 2 => v} = %{1 => any_value(), 2 => x}

    {}
  end

  def any_value() do
    {}
  end
end