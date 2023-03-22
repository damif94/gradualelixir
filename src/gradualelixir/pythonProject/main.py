# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


def mult(nums):
    r = 1
    for num in nums:
        r = r*num
    return r


def rec(i, n):
    if i == 0:
        return 1 / n
    else:
        return 1 / (n*mult([(1 - rec(j, n)) for j in range(0, i)]))

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print(list(range(0, 1)))
    [print(rec(i,22)) for i in range(1, 22)]

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
