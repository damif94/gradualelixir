defmodule Runner do
  def main(args) do
    [module] = args
    module = module |> String.replace("\\n", "\n")
    m = Code.eval_string(module)
    {{_, module_name, _, _}, _} = m
    out = apply(String.to_existing_atom("#{module_name}"), :main, [])
    out
  end
end

args = System.argv
IO.puts inspect(Runner.main(args))