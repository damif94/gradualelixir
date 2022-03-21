 defmodule Case do
  defmacro cast_case_aux(test, do: branches) do
    IO.inspect(branches)
    indexed_branches = Enum.zip(1..length(branches), branches)
    modified_branches = for {index, branch} <- indexed_branches do
      {:->, meta, [[cond_pat], do_expr]} = branch
      {:->, meta, [[{cond_pat, indexes}], do_expr]}
    end
    IO.inspect(modified_branches)
    {:case, [], [{test, true}, [do: modified_branches]]}
    branches = [{:->, [], [[1], 2]}, 1]
    context = [test: test, branches: branches]
    quote bind_quoted: [branches: branches_left] do
      IO.inspect(context)
      test = Keyword.get(context, :test)
      branches = Keyword.get(context, :branches)
      IO.inspect(branches)
      IO.inspect(unquote(branches))
      case unquote(test) do
        unquote(branches)
      end
    end
  end
  defmacro cast_case(test, do: branches) do
    indexed_branches = Enum.zip(1..length(branches), branches)
    modified_branches = for {index, branch} <- indexed_branches do
      {:->, meta, [[cond_pat], do_expr]} = branch
      modified_cond_pat = {:%{}, [], [{index, {cond_pat, false}}]}
      modified_cond_pat = {:%{}, [], [{index, cond_pat}]}
      {:->, meta, [[modified_cond_pat], do_expr]}
    end
    IO.inspect(modified_branches)
    modified_test_items = for {index, branch} <- indexed_branches do
      {:->, meta, [[cond_pat], do_expr]} = branch
      {index, {cond_pat, {:cast, [], [{:=, [], [cond_pat, do_expr]}]}}}
    end
    modified_test = {:%{}, [], modified_test_items}
    IO.inspect(modified_test)
    {:case, [], [modified_test, [do: modified_branches]]}
  end
 end

defmodule Inspects do
  defmacro macro_inspect(value) do
    quote bind_quoted: [value: value] do
      IO.inspect(value)
      value
    end
  end

  def fun_inspect(value) do
    IO.inspect(value)
    value
  end
end

#
# defmodule Demos do
#  use UseCast
#  require Case
#  require Example
#
#  @spec foo(integer) :: number
#  def foo(x) do
#    case x do
#      0 -> 0
#      n -> n + 1
#    end
#    | any ~> integer
#    x | ({integer, number, (() -> float), []}, float, [integer] -> integer)
#  end
#
#  def baz(f, x) do
#    f | (integer -> integer) ~> (integer -> integer)
#  end
#
#  def gaz(x) do
#    x | any ~> (integer -> integer)
#  end
#
#  def gaz(x, y, z) do
#    x | any ~> integer
#    y | {any, any} ~> {integer, integer}
#    z | any ~> {integer, integer}
#  end
#
##  defmacro my_case(value_ast, do: asts) do
##    IO.inspect(value_ast)
##    quote do
##      case value_ast do
##        1 -> 2
##      end
##    end
##  end
#
#  def cast(x) do
#    true
#  end
#
#  def main(test) do
#    Case.cast_case test do
#      :a -> :a
#    end
#  end
# end
