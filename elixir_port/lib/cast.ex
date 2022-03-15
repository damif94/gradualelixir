defmodule Cast do
  require IEx

  defmodule BadArgumentError do
    defexception message: "Cast function couldn't process this argument tuple",
                 left_type: nil,
                 right_type: nil

    def new(%{left_type: left_type, right_type: right_type} = params) do
      case params do
        _ when is_nil(left_type) or is_nil(right_type) ->
          struct(BadArgumentError, params)

        _ ->
          message =
            "Cast between #{inspect(left_type)} and #{inspect(right_type)} is forbidden because they are not consistent"

          struct(BadArgumentError, Map.put(params, :message, message))
      end
    end
  end

  defmodule CastError do
    defexception message: "Cast error", expression: nil, type: nil

    def new(%{expression: expression, type: type} = params) do
      case params do
        _ when is_nil(expression) or is_nil(type) ->
          struct(CastError, params)

        _ ->
          message = "Couldn't cast #{inspect(expression)} into #{inspect(type)}"
          struct(CastError, Map.put(params, :message, message))
      end
    end
  end

  defguard is_base(type) when is_atom(type) and type != :any

  defguard is_base_value(value)
           when is_atom(value) or is_boolean(value) or is_integer(value) or is_float(value)

  def build_value_from_ast(value_ast) do
    case value_ast do
      value when is_base_value(value) ->
        value

      {value_ast_1, value_ast_2} ->
        {:tuple, [build_value_from_ast(value_ast_1), build_value_from_ast(value_ast_2)]}

      {:{}, _, value_list_ast} ->
        {:tuple, Enum.map(value_list_ast, &build_value_from_ast/1)}

      [{:->, _, [value_list_ast, value_ast]}] ->
        {:fun, Enum.map(value_list_ast, &build_value_from_ast/1), build_value_from_ast(value_ast)}

      {item, _, _} when is_atom(item) ->
        item

      [] ->
        :elist

      _ when is_list(value_ast) ->
        {:list, Enum.map(value_ast, &build_value_from_ast/1)}
    end
  end

  def build_type_from_ast(type_ast) do
    case type_ast do
      {type_ast_1, type_ast_2} ->
        {:tuple, [build_type_from_ast(type_ast_1), build_type_from_ast(type_ast_2)]}

      {:{}, _, type_list_ast} ->
        {:tuple, Enum.map(type_list_ast, &build_type_from_ast/1)}

      [{:->, _, [type_list_ast, type_ast]}] ->
        {:fun, Enum.map(type_list_ast, &build_type_from_ast/1), build_type_from_ast(type_ast)}

      {item, _, _} when is_atom(item) ->
        item

      [] ->
        :elist

      _ when is_list(type_ast) ->
        {:list, Enum.map(type_ast, &build_type_from_ast/1)}
    end
  end

  def ground(type) do
    case type do
      _ when is_base(type) -> type
      :elist -> :elist
      {:list, type} -> {:list, :any}
      {:tuple, type_list} -> {:tuple, 1..length(type_list) |> Enum.map(fn _ -> :any end)}
      {:map, type_map} -> {:map, Enum.into(Enum.map(type_map, fn {k, _} -> {k, :any} end), %{})}
      {:fun, type_list, type} -> {:fun, 1..length(type_list) |> Enum.map(fn _ -> :any end), :any}
    end
  end

  def raise_on_bad_argument_errors(left_type, right_type) do
    #    IO.inspect(left_type)
    #    IO.inspect(right_type)
    case {left_type, right_type} do
      {type, type} when is_base(type) ->
        nil

      {type, :any} when is_base(type) ->
        nil

      {left_type, right_type} when is_base(left_type) and is_base(right_type) ->
        raise BadArgumentError.new(%{left_type: left_type, right_type: right_type})

      {{:tuple, right_type_list}, {:tuple, left_type_list}} ->
        Enum.reduce(Enum.zip(right_type_list, left_type_list), fn {left_type, right_type} ->
          raise_on_bad_argument_errors(left_type, right_type)
        end)

      _ ->
        raise BadArgumentError.new(%{left_type: left_type, right_type: right_type})
    end
  end

  def cast(expr, left_type, right_type) do
    case {expr, left_type, right_type} do
      {_, :any, :any} ->
        expr

      {_, type, :any} ->
        cast(expr, type, ground(type))

      {_, :any, type} ->
        cast(expr, ground(type), type)

      {_, type, type} when is_base(type) ->
        case {expr, type} do
          {_, :atom} when is_atom(expr) -> expr
          {_, :boolean} when is_boolean(expr) -> expr
          {_, :integer} when is_integer(expr) -> expr
          {_, :float} when is_float(expr) -> expr
          _ -> raise CastError.new(%{expression: expr, type: right_type})
        end

      {[], :elist, :elist} ->
        {:list, []}

      {expr, {:list, left_type}, {:list, right_type}} when is_list(expr) ->
        {:list, Enum.map(expr, fn expr -> cast(expr, left_type, right_type) end)}

      {expr, {:tuple, left_type_list}, {:tuple, right_type_list}} when is_tuple(expr) ->
        List.to_tuple(
          Enum.map(
            Enum.zip([Tuple.to_list(expr), left_type_list, right_type_list]),
            fn {expr, left_type, right_type} -> cast(expr, left_type, right_type) end
          )
        )

      {f, {:fun, [left_arg_type], left_ret_type}, {:fun, [right_arg_type], right_ret_type}}
      when is_function(f, 1) ->
        fn expr ->
          cast(f.(cast(expr, left_arg_type, right_arg_type)), left_ret_type, right_ret_type)
        end

      {f, {:fun, [], [left_arg_type1, left_arg_type2], left_ret_type},
       {:fun, [right_arg_type1, right_arg_type2], right_ret_type}}
      when is_function(f, 2) ->
        fn expr1, expr2 ->
          cast(
            f.(
              cast(expr1, left_arg_type1, right_arg_type1),
              cast(expr2, left_arg_type2, right_arg_type2)
            ),
            left_ret_type,
            right_ret_type
          )
        end

      {
        f,
        {:fun, [], [[left_arg_type1, left_arg_type2, left_arg_type3], left_ret_type]},
        {:fun, [], [[right_arg_type1, right_arg_type2, right_arg_type3], right_ret_type]}
      }
      when is_function(f, 3) ->
        fn expr1, expr2, expr3 ->
          cast(
            f.(
              cast(expr1, left_arg_type1, right_arg_type1),
              cast(expr2, left_arg_type2, right_arg_type2),
              cast(expr3, left_arg_type3, right_arg_type3)
            ),
            left_ret_type,
            right_ret_type
          )
        end

      _ ->
        raise CastError.new(%{expression: expr, type: right_type})
    end
  end
end

 defmodule UseCast do
  defmacro __using__(_opts) do
    quote do
      alias Cast

      defmacro expr_ast | {:~>, _, [left_type_ast, right_type_ast]} do
        context = [
          left_type: Code.string_to_quoted(inspect(left_type_ast)),
          right_type: Code.string_to_quoted(inspect(right_type_ast)),
          expr_ast: expr_ast
        ]

        quote bind_quoted: [context: context] do
          {:ok, left_type} = Keyword.get(context, :left_type)
          {:ok, right_type} = Keyword.get(context, :right_type)
          expr = Keyword.get(context, :expr_ast)

          left_type = Cast.build_type_from_ast(left_type)
          right_type = Cast.build_type_from_ast(right_type)

          Cast.cast(expr, left_type, right_type)
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
