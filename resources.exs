defmodule Cast do

  def a ||| _b, do: a

  def integer, do: nil
end


defmodule Demo do
  import Cast

  @spec foo(integer) :: integer
  def foo(x) do
    1 + 1 ||| integer
  end

  @spec baz(integer) :: integer
  def baz(b) do
    1 + 1 ||| integer
  end
end
