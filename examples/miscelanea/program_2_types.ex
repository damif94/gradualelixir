defmodule Program do
  use UseCast

  @spec untyped(any) :: any
  def untyped(value) do
    value | any
  end

  @spec sum(integer, integer) :: integer
  def sum(x, y) do
    x + y | integer
  end

  @spec main(any) :: any
  def main(options) do
    untyped_sum = (untyped((&sum/2) | (integer, integer -> integer)) | any) | any
    untyped_sum.(1, 2) | any
  end
end