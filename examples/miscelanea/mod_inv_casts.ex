defmodule ModInv do
  use UseCast

  def untyped(x) do
    x
  end

  def gcd_1a(a, b) do
    if (a | any ~> number) === 0 do
      {b, 0, 1} | {any, integer, integer} ~> {any, any, any}
    else
      {g, y, x} = gcd_1a(rem(b | any ~> integer, a | any ~> integer) | integer ~> any, a)

      {g,
       (x | any ~> number) -
         ((div(b | any ~> integer, a | any ~> integer) * (y | any ~> number) | number ~> any)
          | any ~> number)
       | number ~> any, y}
    end
    | {any, any, any} ~> any
  end

  def gcd_1b(a, b) do
    if (a | any ~> number) === 0 do
      {b, 0, 1} | {any, integer, integer} ~> {any, any, any}
    else
      {g, y, x} = gcd_1b(rem(b | any ~> integer, a | any ~> integer) | integer ~> any, a)

      untyped(
        {g,
         (x | any ~> number) -
           ((div(b | any ~> integer, a | any ~> integer) * (y | any ~> number) | number ~> any)
            | any ~> number)
         | number ~> any}
        | {any, any} ~> any
      )
      | any ~> {any, any, any}
    end
    | {any, any, any} ~> any
  end

  @spec gcd_2a(any, integer) :: any
  def gcd_2a(a, b) do
    if (a | any ~> number) === 0 do
      {b, 0, 1} | {integer, integer, integer} ~> {any, any, any}
    else
      {g, y, x} = gcd_2a(rem(b, a | any ~> integer) | integer ~> any, a | any ~> integer)

      {g,
       (x | any ~> number) -
         ((div(b, a | any ~> integer) * (y | any ~> number) | number ~> any) | any ~> number)
       | number ~> any, y}
    end
    | {any, any, any} ~> any
  end

  @spec gcd_2b(integer, any) :: any
  def gcd_2b(a, b) do
    if a === 0 do
      {b, 0, 1} | {any, integer, integer} ~> {any, any, any}
    else
      {g, y, x} = gcd_2b(rem(b | any ~> integer, a), a | integer ~> any)

      untyped(
        {g,
         (x | any ~> number) -
           ((div(b | any ~> integer, a) * (y | any ~> number) | number ~> any) | any ~> number)
         | number ~> any}
        | {any, any} ~> any
      )
      | any ~> {any, any, any}
    end
    | {any, any, any} ~> any
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

  @spec mod_inv(integer, integer) :: {atom, integer}
  def mod_inv(a, m) do
    {g, x, _} = gcd_1b(a | integer ~> any, m | integer ~> any)

    if (g | any ~> number) !== 1 do
      {:error, 0}
    else
      {:ok, rem(x | any ~> integer, m)}
    end
  end

  def main() do
    mod_inv(4, 5) | {atom, integer} ~> any
  end
end