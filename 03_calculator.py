def add(a,b):
    return a+b
def subtract(a,b):
    return a-b
def multiply(a,b):
    return a*b
def division(a, b):
    if b == 0:
        return "Error: Division by zero is impossible"
    
    
    return a / b

print("\n=====Python calculator=====")

print("\n1.Addition")
print("2.Subtraction")
print("3.Multiplication")
print("4.Division")
choice = input("Enter your choice (1-4): ")

if not choice.isdigit() or choice not in ["1", "2", "3", "4"]:
    print("Invalid choice! Please restart the program.")
    exit()

x=float(input("Enter the first number:"))
y=float(input("Enter the second number:"))


  
if choice=="1":
    print("Addition of these two numbers:",add(x,y))
elif choice=="2":
    print("Subtraction of these two numbers:",subtract(x,y))
elif choice=="3":
    print("Multiplication of these two numbers:",multiply(x,y))
elif choice=="4":
    print("Division of these two numbers:",division(x,y))