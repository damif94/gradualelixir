defmodule Cast do

  defmodule Base do
    defstruct [:type]
  end

  defmodule Elist do
    defstruct []
  end

  defmodule List do
    defstruct [:type]
  end

  defmodule Tuple do
    defstruct [:types]
  end

  defmodule Map do
    defstruct [:types_dict]
  end


  defmodule Fun do
    defstruct [:arg_types, :return_type]
  end

  def build_value_from_ast(value_ast) do
    case value_ast do
      {value_ast_1, value_ast_2} ->
        {:tuple, [build_value_from_ast(value_ast_1), build_value_from_ast(value_ast_2)]}
      {:{}, _, value_list_ast} -> {:tuple, Enum.map(value_list_ast, &build_value_from_ast/1)}
      [{:->, _, [value_list_ast, value_ast]}] ->
        {:fun, Enum.map(value_list_ast, &build_value_from_ast/1), build_value_from_ast(value_ast)}
      {item, _, _} when is_atom(item) -> item
      [] -> :elist
      _ when is_list(value_ast) -> {:list, Enum.map(value_ast, &build_value_from_ast/1)}
    end
  end
  
  def build_type_from_ast(type_ast) do
    case type_ast do
      {type_ast_1, type_ast_2} ->
        {:tuple, [build_type_from_ast(type_ast_1), build_type_from_ast(type_ast_2)]}
      {:{}, _, type_list_ast} -> {:tuple, Enum.map(type_list_ast, &build_type_from_ast/1)}
      [{:->, _, [type_list_ast, type_ast]}] ->
        {:fun, Enum.map(type_list_ast, &build_type_from_ast/1), build_type_from_ast(type_ast)}
      {item, _, _} when is_atom(item) -> item
      [] -> :elist
      _ when is_list(type_ast) -> {:list, Enum.map(type_ast, &build_type_from_ast/1)}
    end
  end

  defguard is_base(type) when is_atom(type) and type != :any

  def cast(type1, type2) do
    case {type1, type2} do
      {type, type} when is_base(type)  -> nil
      {type, :any} when is_base(type)  -> nil
      {{:tuple, type_list_1}, {:tuple, type_list_2}} ->
        Enum.reduce(Enum.zip(type_list_1, type_list_2), fn {type1, type2} -> cast(type1, type2) end)
      _ -> {:error, "Cannot cast #{type1} to #{type2}}"}
    end
  end

  def cast(expr, type1, type2) do
    IO.inspect(expr)
    IO.inspect(type1)
    IO.inspect(type2)
    case {expr, type1, type2} do
      {_, type, type} when is_base(type)  -> expr
      {{:{}, _, expr_list}, {:tuple, [], type_list_1}, {:tuple, [], type_list_2}} -> {:tuple, Enum.map(
        Enum.zip([expr_list, type_list_1, type_list_2]), fn {expr,type1, type2} -> cast(expr, type1, type2) end
      )}
      {f, {:fun, [arg_type1], ret_type1}, {:fun, [arg_type2], ret_type2}} ->
        fn expr -> cast(f.(cast(expr, arg_type1, arg_type2)), ret_type1, ret_type2) end
      {f, {:fun, [], [arg_type11, arg_type12], ret_type1}, {:fun, [arg_type21, arg_type22], ret_type2}} ->
        fn expr1, expr2 ->
          cast(f.(cast(expr1, arg_type11, arg_type21), cast(expr2, arg_type12, arg_type22)), ret_type1, ret_type2)
        end
      {
        f,
        {:fun, [], [[arg_type11, arg_type12, arg_type13], ret_type1]},
        {:fun, [], [[arg_type21, arg_type22,arg_type23], ret_type2]}
      } ->
        fn expr1, expr2, expr3 ->
          cast(
            f.(
              cast(expr1, arg_type11, arg_type21),
              cast(expr2, arg_type12, arg_type22),
              cast(expr3, arg_type13, arg_type23)
            ), ret_type1, ret_type2)
        end
      _ -> {:error, "Cannot cast #{Macro.to_string(expr)} from #{Macro.to_string(type1)} to #{Macro.to_string(type2)}}"}
    end
  end
end


defmodule UseCast do

  defmacro __using__(_opts) do
    quote do
      alias Cast

      defmacro expr_ast | {:~>, _, [type1_ast, type2_ast]}  do
        IO.inspect(type1_ast)
        IO.inspect(type2_ast)
        context = [
          type1: Code.string_to_quoted(inspect(type1_ast)),
          type2: Code.string_to_quoted(inspect(type2_ast)),
          expr_ast: expr_ast
        ]
        quote bind_quoted: [context: context] do
          {:ok, type1} = Keyword.get(context, :type1)
          {:ok, type2} = Keyword.get(context, :type2)
          expr = Keyword.get(context, :expr_ast)
          type1 = Cast.build_type_from_ast(type1)
          type2 = Cast.build_type_from_ast(type2)
          Cast.cast(expr, type1, type2)
        end
      end

      defmacro expr_ast | type_ast do
        quote do
          unquote(expr_ast)
        end
      end

    end
  end

end


defmodule Demo do
  use UseCast

  @spec foo(integer) :: number
  def foo(x) do
    case x do
      0 -> 0
      n -> n + 1
    end | integer ~> float
#    x | ({integer, number, (() -> float), []}, float, [integer] -> integer)
  end

  def baz(f, x) do
    (f | ((integer -> integer) ~> (integer -> integer)))
  end

end
