defmodule Program do
  use UseCast

  @spec untyped_sum(any, any) :: any
  def untyped_sum(x, y) do
    z = 1
    z = 1
    z = 1

    (x | any ~> number) +
      (((((((y | any ~> number) + 1 | number ~> any) | any ~> number) + 1 | number ~> any)
         | any ~> number) + 1
        | number ~> any)
       | any ~> number)
    | number ~> any

    1
    1 | integer ~> any
  end

  @spec main() :: any
  def main() do
    x = &untyped_sum/2
    x.(1 | integer ~> any, :a | :a ~> any)
  end
end