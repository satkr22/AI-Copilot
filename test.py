

class Demo:
    @classmethod
    def hello(cls):
        print("-----------------Prints from inside hello------------------")
        print(cls.hello)
        print(cls.greet)
        print(type(cls.hello))
        print(type(cls.greet))
        print(cls)
        print(type(Demo))
        print(type(cls))
        print("-----------------------------------------------------------")
        print(end="\n\n")
        
        

    def greet(self):
        print("-----------------Prints from inside greet------------------")

        print(self)
        print(self.greet)
        print(self.hello)
        print(type(self.greet))
        print(type(self.hello))
        print("-----------------------------------------------------------")
        print(end="\n\n")
        
        
h0 = Demo
print("-------------------------Prints of h0------------------------------")
print(h0)
print(type(h0))
print("-------------------------------------------------------------------")
print(end="\n\n")


h1 = Demo.hello()
print("-------------------------Prints of h1------------------------------")
print(h1)
print("-------------------------------------------------------------------")
print(end="\n\n")


h2 = Demo().greet()
print("-------------------------Prints of h2------------------------------")
print(h2)
print("-------------------------------------------------------------------")
print(end="\n\n")


h3 = Demo().hello()
print("-------------------------Prints of h3------------------------------")
print(h3)
print("-------------------------------------------------------------------")
print(end="\n\n")


h4 = Demo()
print("-------------------------Prints of h4------------------------------")
print(h4)
print("-------------------------------------------------------------------")
print(end="\n\n")


'''
while executing do these simply:

1. all execution starts after the class bluprint is stored

2. so when someone calls Demo.hello()
    -- simply execute the hello function 
3. so when someone calls Demo().hello()
    -- simply execute the hello function 
4. why even the need the to do all those things just like C or C++

'''