
defmodule Demo do

  @spec list_length([any]) :: integer
  def list_length(l) do
    case l do
      [] -> 0
      [_ | tail] -> 1 + list_length(tail)
    end
  end

  @spec function_sum_aux((number -> number), (number -> number), number) :: number
  def function_sum_aux(f, g, x) do
    f.(x) + g.(x)
  end


  @spec function_sum((number -> (atom -> number))) :: (atom -> number)
  def apply_one(f) do
    f.(1)
  end

  def atom_to_integer_aux(x, i) do
    aux = [{:one, 1}, {:two, 2}, {:three, 3}]
  end

  @spec main(integer, any):: any
  def main(x, y) do

  end
end