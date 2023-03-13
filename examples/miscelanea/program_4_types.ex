defmodule Program do
  use UseCast

  @spec join(string, [string]) :: string
  def join(_, []) do
    "" | string
  end

  def join(_, [str | []]) do
    str | string
  end

  def join(sep, [str | strs]) do
    str <> (sep <> (join(sep | string, strs | [string]) | string) | string) | string
  end

  def main() do
    x = (["b" | ["cd" | []] | [string]] | [string]) | [string]
    %{:result => join(",", ["a" | x | [string]] | [string]) | string} | %{:result => string}
  end
end