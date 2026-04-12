# sample_bug.py — intentionally broken code for testing the debugger

def greet(name)
    print("Hello, " + name

def divide(a, b):
    return a / b   # no guard for b == 0

class Calculator
    def __init__(self):
        self.result = 0

    def add(self, x y):
        self.result = x + y
        return self.result

result = divide(10, 0)
print(result)
greet("World")
calc = Calculator()
print(calc.add(3, 4))
