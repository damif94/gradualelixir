defmodule Cast do
  require IEx
  defmodule Foo do
    def head([h | _ ]) do
      h
    end
  end

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
      message = "Couldn't cast #{inspect(value)} from type #{inspect(left_type)} into #{inspect(right_type)}"

      struct(CastError, Map.put(params, :message, message))
    end
  end

  defguard is_base(type)
           when (is_atom(type) and type != :any) or
                  (is_tuple(type) and tuple_size(type) == 2 and elem(type, 0) == :atom and
                     is_atom(elem(type, 1)))

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
        {:elist, []}

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

  def type_for_value(value) do
    case value do
      _ when is_boolean(value) -> {:atom, value}
      _ when is_atom(value) -> {:atom, value}
      _ when is_integer(value) -> :integer
      _ when is_float(value) -> :float
    end
  end

  def is_base_subtype(left_type, right_type) do
    case {left_type, right_type} do
      {type, type} -> true
      {{:atom, _}, :atom} -> true
      {{:atom, false}, :boolean} -> true
      {{:atom, true}, :boolean} -> true
      {:boolean, :atom} -> true
      {:integer, :number} -> true
      {:float, :number} -> true
      _ -> false
    end
  end

  def is_consistent_subtype(left_type, right_type) do
    case {left_type, right_type} do
      _ when is_base(left_type) and is_base(right_type) ->
        is_base_subtype(left_type, right_type)

      {:any, _} ->
        true

      {_, :any} ->
        true

      {{:elist, []}, {:elist, []}} ->
        true

      {{:elist, []}, {:list, _}} ->
        true

      {{:list, left_type}, {:list, right_type}} ->
        is_consistent_subtype(left_type, right_type)

      {{:tuple, left_type_list}, {:tuple, right_type_list}}
      when length(left_type_list) == length(right_type_list) ->
        Enum.zip(left_type_list, right_type_list)
        |> Enum.all?(fn {type1, type2} -> is_consistent_subtype(type1, type2) end)

      {{:map, left_type_map}, {:map, right_type_map}} ->
        if Enum.all?(Map.keys(right_type_map), &Enum.member?(Map.keys(left_type_map), &1)) do
          Enum.all?(right_type_map, fn {k, type} ->
            is_consistent_subtype(left_type_map[k], type)
          end)
        else
          false
        end

      {{:fun, left_type_list, left_type}, {:map, right_type_list, right_type}}
      when length(left_type_list) == length(right_type_list) ->
        if is_consistent_subtype(left_type, right_type) do
          Enum.zip(left_type_list, right_type_list)
          |> Enum.all?(fn {type1, type2} -> is_consistent_subtype(type1, type2) end)
        else
          false
        end

      _ ->
        false
    end
  end

  def ground(type) do
    case type do
      _ when is_base(type) ->
        type

      {:elist, []} ->
        {:elist, []}

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

  def cast(value, left_type, right_type) do
#    IO.inspect({value, left_type, right_type})
    result =
      case {value, left_type, right_type} do
        {value, :any, :any} ->
          value

        {value, type, :any} ->
          if is_base(type) do
            if is_consistent_subtype(type_for_value(value), type), do: value, else: :cast_error
          else
            cast(value, type, ground(type))
          end

        {value, :any, type} ->
          if is_base(type) do
            if is_consistent_subtype(type_for_value(value), type), do: value, else: :cast_error
          else
            cast(value, ground(type), type)
          end

        _ when is_base(left_type) ->
          is_left_type_ok = is_consistent_subtype(type_for_value(value), left_type)

          left_right_ground_types_consistent = is_base(right_type) and is_base_subtype(left_type, right_type)

          case {is_left_type_ok, left_right_ground_types_consistent} do
            {true, true} -> value
            {false, _} -> :bad_argument_error
            {_, false} -> :cast_error
          end

        {value, {:elist, []}, right_type} ->
          is_left_type_ok = value == []

          left_right_ground_types_consistent =
            case right_type do
              {:elist, []} -> true
              {:list, _} -> true
              _ -> false
            end

          case {is_left_type_ok, left_right_ground_types_consistent} do
            {true, true} ->
              []

            {false, _} ->
              :bad_argument_error

            {true, false} ->
              :cast_error
          end

        {value, {:list, left_type}, right_type} ->
          is_left_type_ok = is_list(value)

          left_right_ground_types_consistent =
            case right_type do
              {:list, _} -> true
              _ -> false
            end

          case {is_left_type_ok, left_right_ground_types_consistent} do
            {true, true} ->
              right_type = elem(right_type, 1)

              if value == [] and not is_consistent_subtype(left_type, right_type) do
                # since this will not be checked downwards
                :cast_error
              else
                Enum.map(value, fn val -> cast(val, left_type, right_type) end)
              end

            {false, _} ->
              :bad_argument_error

            {true, false} ->
              :cast_error
          end

        {value, {:tuple, left_type_list}, right_type} ->
          is_left_type_ok = is_tuple(value) and tuple_size(value) == length(left_type_list)

          left_right_ground_types_consistent =
            case right_type do
              {:tuple, right_type_list} -> length(left_type_list) == length(right_type_list)
              _ -> false
            end

          case {is_left_type_ok, left_right_ground_types_consistent} do
            {true, true} ->
              right_type_list = elem(right_type, 1)

              Enum.zip([Tuple.to_list(value), left_type_list, right_type_list])
              |> Enum.map(fn {val, left_type, right_type} -> cast(val, left_type, right_type) end)
              |> List.to_tuple()

            {false, _} ->
              :bad_argument_error

            {true, false} ->
              :cast_error
          end

        {value, {:map, left_type_map}, right_type} ->
          is_left_type_ok = is_map(value) and Enum.all?(Map.keys(left_type_map), &Enum.member?(Map.keys(value), &1))

          left_right_ground_types_consistent =
            case right_type do
              {:map, right_type_map} ->
                Enum.sort(Map.keys(left_type_map)) === Enum.sort(Map.keys(right_type_map))

              _ ->
                false
            end

          case {is_left_type_ok, left_right_ground_types_consistent} do
            {true, true} ->
              right_type_map = elem(right_type, 1)

              Enum.map(value, fn {k, v} -> {k, v, left_type_map[k], right_type_map[k]} end)
              |> Enum.map(fn {k, v, type1, type2} -> {k, cast(v, type1, type2)} end)
              |> Enum.into(%{})

            {false, _} ->
              :bad_argument_error

            {true, false} ->
              :cast_error
          end

        {value, {:fun, left_type_list, left_type}, right_type} ->
          f = value
          is_left_type_ok = is_function(f, length(left_type_list))

          left_right_ground_types_consistent =
            case right_type do
              {:fun, _, _} -> true
              _ -> false
            end

          case {is_left_type_ok, left_right_ground_types_consistent} do
            {true, true} ->
              {:fun, right_type_list, right_type} = right_type
              left_type_tuple = left_type_list |> List.to_tuple()
              right_type_tuple = right_type_list |> List.to_tuple()

              case length(left_type_list) do
                0 ->
                  fn ->
                    cast(f.(), left_type, right_type)
                  end

                1 ->
                  fn val1 ->
                    casted_val1 = cast(val1, elem(right_type_tuple, 0), elem(left_type_tuple, 0))
                    cast(f.(casted_val1), left_type, right_type)
                  end

                2 ->
                  fn val1, val2 ->
                    casted_val1 = cast(val1, elem(right_type_tuple, 0), elem(left_type_tuple, 0))
                    casted_val2 = cast(val2, elem(right_type_tuple, 1), elem(left_type_tuple, 1))
                    cast(f.(casted_val1, casted_val2), left_type, right_type)
                  end

                3 ->
                  fn val1, val2, val3 ->
                    casted_val1 = cast(val1, elem(right_type_tuple, 0), elem(left_type_tuple, 0))
                    casted_val2 = cast(val2, elem(right_type_tuple, 1), elem(left_type_tuple, 1))
                    casted_val3 = cast(val3, elem(right_type_tuple, 2), elem(left_type_tuple, 2))
                    cast(f.(casted_val1, casted_val2, casted_val3), left_type, right_type)
                  end

                  # TODO make this general to support arbitrary function arity
                  #  probably this is macro-doable by converting function args into tuple first
              end

            {false, _} ->
              :bad_argument_error

            {true, false} ->
              :cast_error
          end
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
