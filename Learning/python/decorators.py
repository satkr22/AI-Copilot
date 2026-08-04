def greet():
    print("Hii :)")
    
    
    
def my_decorator(func):
    def wrapper():
        print("Some task before the function")
        func()
        print("Some task after the function")
    
    return wrapper

say_hi = my_decorator(greet)
say_hi()

@my_decorator
def greet():
    print("Hii :)")
    
greet()