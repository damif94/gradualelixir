defmodule Demo do
  @spec id_boolean(boolean) :: boolean
  def id_boolean(x) do
    x
  end

  def main(x) do
    {x, x} = {1, true}
  end
end