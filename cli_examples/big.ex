defmodule Demo do
  @spec foo_data() :: {}
  def foo_data() do
    {1 + 1, 1 + 1.0}
    {1 + 1, max(1, 1.0)}
    []
    [1 + 1]
    [1, 1.0]
    [1 + 1, max(1, 1.0)]
    [:a, true, false]
    %{1 => [true], :a => {1}}
    {}
  end

  @spec foo_pattern({integer, number}, {number, integer}) :: integer

  def foo_pattern(x, y) do
    {{_, z}, {1.0, z}} = {x, y}

    z
  end

  @spec gaz({integer, number}, {number, integer}) :: {integer, integer}

  def gaz({x, x}, {y, y}) do
    {x, y}
  end

  @spec foo_cond(integer, float, boolean) :: {number, integer}

  def foo_cond(x, y, b) do
    u =
      cond do
        b -> x
        not b -> y
      end

    {u, x + 1}
  end

  @spec foo_cond_fun((number -> integer), (float -> float)) :: (float -> number)

  def foo_cond_fun(x, y) do
    cond do
      true or false -> x
      false and true -> y
    end
  end

  @spec foo_case({integer, float}) :: number

  def foo_case(p) do
    case p do
      {x, _} -> x
      {_, y} -> y
    end
  end

  @spec foo_seq({integer, float}) :: number

  def foo_seq(p) do
    {x, y} = p

    x

    y
  end

  @spec foo_fun() :: {}
  def foo_fun() do
    x = &foo_seq/1
    x.({4, 2.0})
    {}
  end
end