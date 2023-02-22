defmodule Program do
  use UseCast

  @spec sum_x_x(number, integer) :: number
  def sum_x_x(y, x) do
    x + y | number
  end

  def sum_x_x(x, y) do
    x + x | number
  end

  @spec sum_x_y(integer, number) :: integer
  def sum_x_y(x, y) do
    x + x | integer
  end

  @spec sum_x_yz(any, any) :: any
  def sum_x_yz(x, y) do
    ((if true do
        (&sum_x_x/2) | (number, integer -> number)
      else
        (&sum_x_y/2) | (integer, number -> integer)
      end)
     | (integer, integer -> number)).(x | any, y | any)
    | number
  end

  @spec main() :: any
  def main() do
    sum_x_x(1, 2) | number
  end
end