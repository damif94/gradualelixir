defmodule Cast do
  require IEx

  defmodule BadArgumentError do
    defexception message: "Cast function couldn't process this argument tuple",
                 value: nil,
                 left_type: nil,
                 right_type: nil

    def new(%{reason: reason, value: value, left_type: left_type, right_type: right_type} = params) do
      message =
        case reason do
          "type_error" ->
            "#{inspect(value)} is not of type #{inspect(left_type)}"

          "inconsistent_types" ->
            "#{inspect(left_type)} is not consistent with #{inspect(right_type)}"
        end

      message =
        "Cast #{inspect(value)} from #{inspect(left_type)} into #{inspect(right_type)} is forbidden:\n #{message}"

      struct(BadArgumentError, Map.put(params, :message, message))
    end
  end

  defmodule CastError do
    defexception message: "Cast error", expression: nil, left_type: nil, right_type: nil

    def new(%{value: value, left_type: left_type, right_type: right_type} = params) do
      message =
        "Couldn't cast #{inspect(value)} from type #{inspect(left_type)} into #{inspect(right_type)}"

      struct(CastError, Map.put(params, :message, message))
    end
  end

  defguard is_base(type)
           when (is_atom(type) and type != :any) or
                  (tuple_size(type) == 2 and elem(type, 0) == :atom and is_atom(elem(type, 1)))

  defguard is_base_value(value)
           when is_atom(value) or is_boolean(value) or is_integer(value) or is_float(value)

  def build_type_from_ast(type_ast) do
    #    IO.inspect(type_ast)
    case type_ast do
      {type_ast_1, type_ast_2} ->
        {:tuple, [build_type_from_ast(type_ast_1), build_type_from_ast(type_ast_2)]}

      {:{}, _, type_list_ast} ->
        {:tuple, Enum.map(type_list_ast, &build_type_from_ast/1)}

      [{:->, _, [type_list_ast, type_ast]}] ->
        {:fun, Enum.map(type_list_ast, &build_type_from_ast/1), build_type_from_ast(type_ast)}

      [] ->
        :elist

      _ when is_list(type_ast) and length(type_ast) == 1 ->
        [item] = type_ast
        {:list, build_type_from_ast(item)}

      {:%{}, _, key_type_list} ->
        aux = Enum.map(key_type_list, fn {key, type} -> {key, build_type_from_ast(type)} end)
        {:map, Enum.into(aux, %{})}

      {item, _, _} when is_atom(item) ->
        item

      item when is_atom(item) ->
        {:atom, item}
    end
  end

  def ground(type) do
    case type do
      _ when is_base(type) ->
        type

      :elist ->
        :elist

      {:list, _} ->
        {:list, :any}

      {:tuple, type_list} ->
        {:tuple, 0..(length(type_list) - 1)//1 |> Enum.map(fn _ -> :any end)}

      {:map, type_map} ->
        {:map, Enum.into(Enum.map(type_map, fn {k, _} -> {k, :any} end), %{})}

      {:fun, type_list, _} ->
        {:fun, 0..(length(type_list) - 1)//1 |> Enum.map(fn _ -> :any end), :any}
    end
  end

  def is_base_type_valid_for_base_value(value, type) do
    case {value, type} do
      {atom, {:atom, a}} -> is_atom(value) and atom === a
      {_, :atom} -> is_atom(value)
      {_, false} -> is_boolean(value) and value
      {_, true} -> is_boolean(value) and value
      {_, :boolean} -> is_boolean(value)
      {_, :integer} -> is_integer(value)
      {_, :float} -> is_float(value)
      {_, :number} -> is_integer(value) or is_float(value)
    end
  end

  def cast(value, left_type, right_type) do
    #    IO.inspect({value, left_type, right_type})
    result =
      case {value, left_type, right_type} do
        {_, :any, :any} ->
          value

        {_, type, :any} ->
          cast(value, type, ground(type))

        {_, :any, type} ->
          cast(value, ground(type), type)

        _ when is_base(left_type) and is_base(right_type) ->
          if not is_base_type_valid_for_base_value(value, left_type) do
            :bad_argument_error
          else
            if not is_base_type_valid_for_base_value(value, right_type) do
              :cast_error
            else
              value
            end
          end

        {[], :elist, :elist} ->
          {:list, []}

        {value, {:list, left_type}, {:list, right_type}} ->
          if not is_list(value) do
            :bad_argument_error
          else
            {:list, Enum.map(value, fn val -> cast(val, left_type, right_type) end)}
          end

        {value, {:tuple, left_type_list}, {:tuple, right_type_list}} ->
          is_left_type_ok = is_tuple(value) and tuple_size(value) == length(left_type_list)
          left_right_ground_types_consistent = length(left_type_list) == length(right_type_list)

          case {is_left_type_ok, left_right_ground_types_consistent} do
            {true, true} ->
              Enum.zip([Tuple.to_list(value), left_type_list, right_type_list])
              |> Enum.map(fn {val, left_type, right_type} -> cast(val, left_type, right_type) end)
              |> List.to_tuple()

            {false, _} ->
              :bad_argument_error

            {true, false} ->
              :cast_error
          end

        {value, {:map, left_type_map}, {:map, right_type_map}} ->
          is_left_type_ok =
            is_map(value) and Enum.all?(Map.keys(left_type_map), &Enum.member?(Map.keys(value), &1))

          left_right_ground_types_consistent =
            Enum.sort(Map.keys(left_type_map)) === Enum.sort(Map.keys(right_type_map))

          case {is_left_type_ok, left_right_ground_types_consistent} do
            {true, true} ->
              Enum.map(value, fn {k, v} -> {k, v, left_type_map[k], right_type_map[k]} end)
              |> Enum.map(fn {k, v, type1, type2} -> {k, cast(v, type1, type2)} end)
              |> Enum.into(%{})

            {false, _} ->
              :bad_argument_error

            {true, false} ->
              :cast_error
          end

        {f, {:fun, [left_arg_type], left_ret_type}, {:fun, [right_arg_type], right_ret_type}} ->
          if not is_function(f, 1) do
            :bad_argument_error
          else
            fn val ->
              cast(f.(cast(val, left_arg_type, right_arg_type)), left_ret_type, right_ret_type)
            end
          end

        {f, {:fun, [], [left_arg_type1, left_arg_type2], left_ret_type},
         {:fun, [right_arg_type1, right_arg_type2], right_ret_type}} ->
          if not is_function(f, 2) do
            :bad_argument_error
          else
            fn val1, val2 ->
              cast(
                f.(
                  cast(val1, left_arg_type1, right_arg_type1),
                  cast(val2, left_arg_type2, right_arg_type2)
                ),
                left_ret_type,
                right_ret_type
              )
            end
          end

        {
          f,
          {:fun, [], [[left_arg_type1, left_arg_type2, left_arg_type3], left_ret_type]},
          {:fun, [], [[right_arg_type1, right_arg_type2, right_arg_type3], right_ret_type]}
        } ->
          if not is_function(f, 3) do
            :bad_argument_error
          else
            fn val1, val2, val3 ->
              cast(
                f.(
                  cast(val1, left_arg_type1, right_arg_type1),
                  cast(val2, left_arg_type2, right_arg_type2),
                  cast(val3, left_arg_type3, right_arg_type3)
                ),
                left_ret_type,
                right_ret_type
              )
            end
          end

        _ ->
          :cast_error
      end

    case result do
      :bad_argument_error ->
        raise BadArgumentError.new(%{
                reason: "type_error",
                value: value,
                left_type: left_type,
                right_type: right_type
              })

      :cast_error ->
        raise CastError.new(%{
                value: value,
                left_type: left_type,
                right_type: right_type
              })

      value ->
        value
    end
  end
end

defmodule UseCast do
  require Inspects

  defmacro __using__(_opts) do
    quote do
      alias Cast

      defmacro value_ast | {:~>, _, [left_type_ast, right_type_ast]} do
        context = [
          left_type: Code.string_to_quoted(inspect(left_type_ast)),
          right_type: Code.string_to_quoted(inspect(right_type_ast)),
          value_ast: value_ast
        ]

        quote bind_quoted: [context: context] do
          {:ok, left_type} = Keyword.get(context, :left_type)
          {:ok, right_type} = Keyword.get(context, :right_type)
          value_ast = Keyword.get(context, :value_ast)

          left_type = Cast.build_type_from_ast(left_type)
          right_type = Cast.build_type_from_ast(right_type)

          Cast.cast(value_ast, left_type, right_type)
        end
      end

      defmacro value_ast | type_ast do
        quote do
          unquote(value_ast)
        end
      end
    end
  end
end
