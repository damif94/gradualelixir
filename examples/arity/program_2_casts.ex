defmodule Program do
  use UseCast

  def untyped(x) do
    x
  end

  @spec assert_function_arity_1((any -> any)) :: {}
  def assert_function_arity_1(x) do
    {}
  end

  @spec foo(atom, atom) :: atom
  def foo(a, b) do
    b
  end

  @spec main() :: {}
  def main() do
    assert_function_arity_1(untyped((&foo/2) | (atom, atom -> atom) ~> any) | any ~> (any -> any))
  end
end