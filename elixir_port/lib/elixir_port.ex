defmodule ElixirPort do
  alias Macro
  alias JSON
  require IEx

  @moduledoc """
  Documentation for `ElixirPort`.
  """

  @doc """
    Checks if the element l is a keyword list
      - its a list
      - all its items are two-component tuples
        - all its first-components are atoms

    Also checks that the keyword list is reserved:
    (it may be a little too much though)
      - At least one of its keys is a reserved atom,
        used in ast translation (like :do: , :else)
  """
  def is_reserved_keyword_list_node(node) do
    reserved_keyword_list_atoms = [:do, :else]

    cond do
      is_list(node) ->
        Enum.reduce_while(node, false, fn item, acc ->
          if !is_tuple(item) or tuple_size(item) != 2 do
            {:cont, false}
          else
            {k, _} = item

            cond do
              !is_atom(k) -> {:halt, false}
              k in reserved_keyword_list_atoms -> {:cont, true}
              true -> {:cont, acc}
            end
          end
        end)

      is_tuple(node) and tuple_size(node) == 2 ->
        {k, _} = node
        k in reserved_keyword_list_atoms

      true ->
        false
    end
  end

  def parse_as_json(code) do
    {:ok, ast} = Code.string_to_quoted(code)
    #    IO.inspect(ast, label: "raw_ast")
    #    Macro.prewalk(ast, fn node -> IO.inspect(node); IO.inspect("---------------"); node end)
    new_ast =
      Macro.prewalk(
        ast,
        fn
          node ->
            if is_reserved_keyword_list_node(node) do
              node
            else
              case node do
                {x, y} -> {:{}, nil, [x, y]}
                otherwise -> otherwise
              end
            end
        end
      )

    {:ok, json_string} = JSON.encode(new_ast)
    IO.write(json_string)
  end

  def main(args) do
    [code] = args

    if String.at(code, 0) == "\"" do
      IO.print("yes")
    end

    parse_as_json(code)
  end
end
