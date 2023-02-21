defmodule Program do
  use UseCast

  @spec list_length([number]) :: integer
  def list_length(l) do
    case l | [number] do
      [] -> 0
      [_ | tail] -> 1 + (list_length(tail | [number]) | integer) | integer
    end
    | integer
  end

  @spec filter((number -> boolean), [number]) :: [number]
  def filter(f, l) do
    case l | [number] do
      [] ->
        []

      [head | tail] ->
        filtered_tail = (filter(f | (number -> boolean), tail | [number]) | [number]) | [number]

        if (f | (number -> boolean)).(head | number) | boolean do
          [(head | number) | filtered_tail | [number]] | [number]
        else
          filtered_tail | [number]
        end
        | [number]
    end
    | [number]
  end

  @spec is_positive(number) :: boolean
  def is_positive(x) do
    x >= 0 | boolean
  end

  @spec filter_positive([number]) :: [number]
  def filter_positive(l) do
    filter((&is_positive/1) | (number -> boolean), l | [number]) | [number]
  end

  @spec main(%{:choice => integer}) :: [number]
  def main(options) do
    choice =
      (case options | %{:choice => integer} do
         %{:choice => v} -> v | integer
         _ -> 1
       end
       | integer)
    | integer

    l =
      (case choice | integer do
         1 -> [1 | [2 | [3 | []] | [integer]] | [integer]] | [integer]
         2 -> [2.0 | []] | [float]
       end
       | [number])
    | [number]

    (filter_positive(l | [number]) | [number]) | [number]
  end
end