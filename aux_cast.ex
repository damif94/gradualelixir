defmodule Demo do
  use UseCast

  @spec id_boolean(boolean) :: boolean
  def id_boolean(x) do
    x
  end

  @spec main(any) :: any
  def main(x) do
    z = &id_boolean/1
    (z | (boolean -> boolean) ~> (any -> boolean)).(x)
  end


  def main() do
    y | number
    z | any
#    ({x, x, u, u} = ({1, z, 1, y} | ~> {integer, any, integer, integer}) | {any, any, integer, integer})

    # {any, any, integer, integer} consistent  {} subtype {integer, any, integer, number}
#                              {integer, any, integer, integer}

# {any, any, integer, integer} ~> {integer, any, integer, integer}
  end


end
