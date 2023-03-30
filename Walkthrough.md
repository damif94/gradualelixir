# Walkthrough

Set the following module in a file called `program.ex` in your working directory:
```elixir
defmodule Program do
  @spec sum(number, number) :: number
  def sum(x, y) do
    x + y
  end

  def untyped(x) do
    x
  end

  @spec main() :: number
  def main do
    sum(1, 2)
  end
end
```

And execute the static type checker:
```bash
 ./gradualelixir type_check program.ex
```

Boring issues with the unspecified function `untyped`...  Let's go gradual!:

```bash
 ./gradualelixir type_check program.ex --gradual
```

It should be fine, so now run it with:
```bash
 ./gradualelixir run program.ex --gradual
```

That goes well, too!

Try making the type checker complain a little. Some ideas to run the checker again:
- Replace the `+` symbol by `<>`
- Add an extra argument at the sum invocation
- Change the main return type to `integer`
- Change the second parameter for `sum` `y` with a literal `"y"`
- Change all occurrences of `y` in `sum` (parameter and body) with a literal `"y"`
- Do the following changes all across the file, iteratively
  - `1` into `"1"`
  - `@spec sum(number, number) :: number` into `@spec sum(string, number) :: number` 
  - `x` into `1`,   
- Replace the first argument of sum (`1`) with the string `"1"` 

Do the errors make sense?

Let's stick with the last example. Try running it!
```bash
> Failed to run with gradual semantics because Program has type errors
```

You should be getting the error above. Let's cheat the type checker by making the `"1"` parameter _untyped_: replace `sum("1", 2)` with `sum(untyped("x"), 2)`.

You will probably be getting a cast error at `Program.main/0` when attempting the invocation:
```bash
> (Cast.CastError) Couldn't cast "1" from type string into number
```
You see, even if the type checker was _cheated_ at compile time, it certainly can't be _cheated_ in runtime. 

Now run without the aid of type checker
```bash
 ./gradualelixir run program.ex
```
You should get a plain old runtime error inside `Program.sum/2`:

```bash
> (ArithmeticError) bad argument in arithmetic expression: "1" + 2
```