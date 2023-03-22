defmodule Program do
  use UseCast

  @spec sum_x_x(number, integer) :: number
  def sum_x_x(y, x) do
    x + y
  end

  def sum_x_x(x, y) do
    x + x
  end

  @spec sum_x_y(integer, number) :: integer
  def sum_x_y(x, y) do
    x + x
  end

  def sum_x_yz(x, y) do
    (if true do
       &sum_x_x/2
     else
       &sum_x_y/2
     end).(x | any ~> integer, y | any ~> integer)
    | number ~> any
  end

  def main() do
    %{1.0 => 3}
    sum_x_x(1, 2) | number ~> any
  end
end