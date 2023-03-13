defmodule Program do
  use UseCast

  @spec join(string, [string]) :: string
  def join(_, []) do
    ""
  end

  def join(_, [str | []]) do
    str
  end

  def join(sep, [str | strs]) do
    str <> sep <> join(sep, strs)
  end

  def main() do
    x = ["b" | ["cd" | []]]
    %{:result => join(",", ["a" | x])} | %{:result => string} ~> any
  end
end