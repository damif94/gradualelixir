defmodule ModInv do
  def untyped(x) do
    x
  end

  def gcd_1a(a, b) do
    if a === 0 do
      {b, 0, 1}
    else
      {g, y, x} = gcd_1a(rem(b, a), a)
      {g, x - div(b, a) * y, y}
    end
  end

  def gcd_1b(a, b) do
    if a === 0 do
      {b, 0, 1}
    else
      {g, y, x} = gcd_1b(rem(b, a), a)
      untyped({g, x - div(b, a) * y})
    end
  end

  @spec gcd_2a(any, integer) :: any
  def gcd_2a(a, b) do
    if a === 0 do
      {b, 0, 1}
    else
      {g, y, x} = gcd_2a(rem(b, a), a)
      {g, x - div(b, a) * y, y}
    end
  end

  @spec gcd_2b(integer, any) :: any
  def gcd_2b(a, b) do
    if a === 0 do
      {b, 0, 1}
    else
      {g, y, x} = gcd_2b(rem(b, a), a)
      untyped({g, x - div(b, a) * y})
    end
  end

  @spec gcd_3a(integer, integer) :: {integer, integer, integer}
  def gcd_3a(a, b) do
    if a === 0 do
      {b, 0, 1}
    else
      {g, y, x} = gcd_3a(rem(b, a), a)
      {g, x - div(b, a) * y, y}
    end
  end

  #  this doesn't type check
  #  @spec gcd_3b(integer, integer) :: {integer, integer, integer}
  #  def gcd_3b(a, b) do
  #    if a === 0 do
  #      {b, 0, 1}
  #    else
  #       {g, y, x} = gcd_3b(rem(b, a), a)
  #       {g, x - div(b, a) * y}
  #    end
  #  end

  #  @spec gcd_3c(integer, integer) :: {integer, integer}
  #  def gcd_3c(a, b) do
  #    if a === 0 do
  #      {b, 0, 1}
  #    else
  #       {g, y, x} = gcd_3c(rem(b, a), a)
  #       {g, x - div(b, a) * y, y}
  #    end
  #  end

  #  @spec gcd_3d(integer, integer) :: {integer, integer}
  #  def gcd_3d(a, b) do
  #    if a === 0 do
  #      {b, 0, 1}
  #    else
  #       {g, y} = gcd_3d(rem(b, a), a)
  #       {g, y - div(b, a) * y, y}
  #    end
  #  end

  @spec mod_normalize(integer, integer) :: integer
  def mod_normalize(x, m) do
    case {x < 0, x >= m} do
      {false, false} -> x
      {true, _} -> mod_normalize(x + m, m)
      {_, true} -> mod_normalize(x - m, m)
    end
  end


#  @spec mod_inv(integer, integer) :: integer
  def mod_inv(a, m) do
    {g, x, _} = gcd_3a(a, m)

    if g !== 1 do
      {:error, 0}
    else
      {:ok, mod_normalize(rem(x, m), m)}
    end
  end

  def main do
    mod_inv(:a, 5)
  end
end