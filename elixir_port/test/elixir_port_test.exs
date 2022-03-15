defmodule ElixirPortTest do
  use ExUnit.Case
  doctest ElixirPort

  test "greets the world" do
    assert ElixirPort.hello() == :world
  end
end
