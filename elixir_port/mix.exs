defmodule ElixirPort.MixProject do
  use Mix.Project

  def project do
    [
      app: :elixir_port,
      version: "0.1.0",
      elixir: "~> 1.12",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      escript: escript()
    ]
  end

  defp escript do
    [main_module: ElixirPort]
  end

  # Run "mix help compile.app" to learn about applications.
  def application do
    [
      extra_applications: [:logger]
    ]
  end

  # Run "mix help deps" to learn about dependencies.
  defp deps do
    [
      {:type_check, "~> 0.10.0"},
      {:json, "~> 1.4"}
    ]
  end
end
