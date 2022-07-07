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
          :type_error ->
            "#{inspect(value)} is not of type #{inspect(left_type)}"

          :inconsistent_types ->
            "#{inspect(left_type)} is not consistent with #{inspect(right_type)}"
        end

      message =
        "Cast is forbidden: #{message}"

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


  defguard is_literal(value)
           when is_atom(value) or is_integer(value) or is_float(value)

  defguard is_base(type)
           when (is_atom(type) and type in [:integer, :float, :number, :atom, :boolean]) or
                  (is_tuple(type) and tuple_size(type) == 2 and elem(type, 0) == :atom and
                     is_atom(elem(type, 1)))

  def build_type_from_ast(type_ast) do
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
        {:map, Enum.map(key_type_list, fn {key, type} -> {key, build_type_from_ast(type)} end)}

      {item, _, _} when is_atom(item) ->
        item

      item when is_atom(item) ->
        {:atom, item}
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

  def is_subtype(left_type, right_type) do
    case {left_type, right_type} do
      _ when is_base(left_type) and is_base(right_type) ->
        is_base_subtype(left_type, right_type)

      {:any, :any} ->
        true

      {:elist, :elist} ->
        true

      {:elist, {:list, _}} ->
        true

      {{:list, left_type}, {:list, right_type}} ->
        is_subtype(left_type, right_type)

      {{:tuple, left_type_list}, {:tuple, right_type_list}}
      when length(left_type_list) == length(right_type_list) ->
        Enum.zip(left_type_list, right_type_list)
        |> Enum.all?(fn {type1, type2} -> is_subtype(type1, type2) end)

      {{:map, left_type_pair_list}, {:map, right_type_pair_list}} ->
        left_type_map = Enum.into(left_type_pair_list, %{})
        right_type_map = Enum.into(right_type_pair_list, %{})
        if Enum.all?(Map.keys(right_type_map), &Enum.member?(Map.keys(left_type_map), &1)) do
          Enum.all?(right_type_map, fn {k, type} ->
            is_subtype(left_type_map[k], type)
          end)
        else
          false
        end

      {{:fun, left_type_list, left_type}, {:fun, right_type_list, right_type}}
      when length(left_type_list) == length(right_type_list) ->
        if is_subtype(left_type, right_type) do
          Enum.zip(left_type_list, right_type_list)
          |> Enum.all?(fn {type1, type2} -> is_subtype(type2, type1) end)
        else
          false
        end

      _ ->
        false
    end
  end


  def ground_type_for_value(value) do
    case value do
      _ when is_literal(value) ->
        cond do
          is_atom(value) -> {:atom, value}
          is_integer(value) -> :integer
          is_float(value) -> :float
        end

      [] ->
        :elist

      _ when is_list(value) ->
        {:list, :any}

      _ when is_tuple(value) ->
        {:tuple, Tuple.to_list(value) |> Enum.map(fn _ -> :any end)}

      _ when is_map(value) ->
        {:map, value |> Enum.map(fn {k, _} -> {k, :any} end)}

      _ when is_function(value) ->
        args_list = case :erlang.fun_info(value)[:arity]-1 do
          -1 -> []
          n -> Enum.to_list(0..n) |> Enum.map(fn _ -> :any end)
        end
        {:fun, args_list, :any}
    end
  end

  def ground_type_for_type(type) do
    case type do
      _ when is_base(type) ->
        type

      :elist ->
        :elist

      {:list, _} ->
        {:list, :any}

      {:tuple, type_list} ->
        {:tuple, type_list |> Enum.map(fn _ -> :any end)}

      {:map, type_map} ->
        {:map, Enum.map(type_map, fn {k, _} -> {k, :any} end)}

      {:fun, type_list, _} ->
        {:fun, type_list |> Enum.map(fn _ -> :any end), :any}
    end
  end


  def cast(value, left_type, right_type) do
    result = case {value, left_type, right_type} do
      {value, :any, :any} ->
        value

      {value, type, :any} ->
        cast(value, type, ground_type_for_type(type))

      {value, :any, type} ->
        if is_subtype(ground_type_for_value(value), ground_type_for_type(type)) do
          cast(value, ground_type_for_type(type), type)
        else
          :cast_error
        end

      {value, left_type, right_type} when is_literal(value) ->
        cond do
          not is_subtype(ground_type_for_value(value), left_type) ->
            {:bad_argument_error, :type_error}
          left_type != right_type ->
            {:bad_argument_error, :inconsistent_types}
          true ->
            value
        end

      {[], left_type, right_type} ->
        cond do
          ground_type_for_type(left_type) not in [:elist, {:list, :any}] ->
            {:bad_argument_error, :type_error}
          ground_type_for_type(right_type) not in [:elist, {:list, :any}] ->
            {:bad_argument_error, :inconsistent_types}
          true ->
            []
        end

      {[head_value | tail_value], left_type, right_type} ->
        cond do
          not Kernel.match?({:list, _}, left_type) ->
            {:bad_argument_error, :type_error}
          not Kernel.match?({:list, _}, right_type) ->
            {:bad_argument_error, :inconsistent_types}
          true ->
            {:list, left_type} = left_type
            {:list, right_type} = right_type
            [cast(head_value, left_type, right_type) | cast(tail_value, {:list, left_type}, {:list, right_type})]
        end

      {value, left_type, right_type} when is_tuple(value) ->
        cond do
          not Kernel.match?({:tuple, _}, left_type) ->
            {:bad_argument_error, :type_error}
          tuple_size(value) != length(Kernel.elem(left_type, 1)) ->
            {:bad_argument_error, :type_error}
          not Kernel.match?({:tuple, _}, right_type) ->
            {:bad_argument_error, :inconsistent_types}
          length(Kernel.elem(left_type, 1)) != length(Kernel.elem(right_type, 1)) ->
            {:bad_argument_error, :inconsistent_types}
          true ->
            {:tuple, left_type_list} = left_type
            {:tuple, right_type_list} = right_type
            Enum.zip([Tuple.to_list(value), left_type_list, right_type_list])
            |> Enum.map(fn {val, left_type, right_type} -> cast(val, left_type, right_type) end)
            |> List.to_tuple()
        end

      {value, left_type, right_type} when is_map(value) ->
        cond do
          not Kernel.match?({:map, _}, left_type) ->
            {:bad_argument_error, :type_error}
          Enum.any?(Kernel.elem(left_type, 1), fn {k, _} -> k not in Map.keys(value) end) ->
            {:bad_argument_error, :type_error}
          not Kernel.match?({:map, _}, right_type) ->
            {:bad_argument_error, :inconsistent_types}
          Enum.map(Kernel.elem(left_type, 1), fn {k, _} -> k end) != Enum.map(Kernel.elem(right_type, 1), fn {k, _} -> k end) ->
            {:bad_argument_error, :inconsistent_types}
          true ->
            left_type_map = Enum.into(Kernel.elem(left_type, 1), %{})
            right_type_map = Enum.into(Kernel.elem(right_type, 1), %{})
            Enum.map(value, fn {k, v} ->
              if Map.has_key?(left_type_map, k) do
                {k, cast(v, left_type_map[k], right_type_map[k])}
              else
                {k, v}
              end
            end)
            |> Enum.into(%{})
        end

        {value, left_type, right_type} when is_function(value) ->
          cond do
            not Kernel.match?({:fun, _, _}, left_type) ->
              {:bad_argument_error, :type_error}
            not is_function(value, length(Kernel.elem(left_type, 1))) ->
              {:bad_argument_error, :type_error}
            not Kernel.match?({:fun, _, _}, right_type) ->
              {:bad_argument_error, :inconsistent_types}
            not is_function(value, length(Kernel.elem(right_type, 1))) ->
              {:bad_argument_error, :inconsistent_types}
            true ->
              left_type_tuple = Kernel.elem(left_type, 1) |> List.to_tuple()
              right_type_tuple = Kernel.elem(right_type, 1) |> List.to_tuple()
              left_type = Kernel.elem(left_type, 2)
              right_type = Kernel.elem(right_type, 2)
              case tuple_size(left_type_tuple) do
                0 ->
                  fn ->
                    cast(value.(), left_type, right_type)
                  end

                1 ->
                  fn val1 ->
                    casted_val1 = cast(val1, elem(right_type_tuple, 0), elem(left_type_tuple, 0))
                    cast(value.(casted_val1), left_type, right_type)
                  end

                2 ->
                  fn val1, val2 ->
                    casted_val1 = cast(val1, elem(right_type_tuple, 0), elem(left_type_tuple, 0))
                    casted_val2 = cast(val2, elem(right_type_tuple, 1), elem(left_type_tuple, 1))
                    cast(value.(casted_val1, casted_val2), left_type, right_type)
                  end

                3 ->
                  fn val1, val2, val3 ->
                    casted_val1 = cast(val1, elem(right_type_tuple, 0), elem(left_type_tuple, 0))
                    casted_val2 = cast(val2, elem(right_type_tuple, 1), elem(left_type_tuple, 1))
                    casted_val3 = cast(val3, elem(right_type_tuple, 2), elem(left_type_tuple, 2))
                    cast(value.(casted_val1, casted_val2, casted_val3), left_type, right_type)
                  end

                  # TODO make this general to support arbitrary function arity
                  #  probably this is macro-doable by converting function args into tuple first
              end
          end
    end

    case result do
      {:bad_argument_error, error_type} ->
        raise BadArgumentError.new(%{
          reason: error_type,
          value: value,
          left_type: left_type,
          right_type: right_type
        })
      :cast_error ->
        raise CastError.new(%{
            value: value,
            left_type: ground_type_for_value(value),
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
