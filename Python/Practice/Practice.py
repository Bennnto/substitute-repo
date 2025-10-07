# To Show Basic Output USE print (lower case)
# Write a programe that print :
# Your Name
# Your age
# Your favourite hobby

# Solution
#print("My name is Vissarut Promkaew Ben")
#print("I'm 27 years old")
#print("My favourite hobby is cycling")
#-----------------------------------------------
# Variable store data values, Python have dynamic typing
# Example of Variable
#name = "Ben"      #Type : String
#age = 27 	      #Type : Integer
#height = 5.6      #Type : Float
#is_student = True # Type : Boolean

#-------------------------------------------------
# Number
#Int_num = 5
#float_num = 5.2
#complex_num = 3-2j

#-------------------------------------------------
#String
#Single_quote = 'string'
#Double_quote = "Hello"
#multiline = """this is a
#multiline string"""
#print(multiline)
#-------------------------------------------------
#Boolean
#is_true = True
#is_false = False

#-------------------------------------------------
#Type Conversion & Variable Practice
#age = int("25")
#str_age = str(25)
#price = float("19.99")

#print(age)
#print(str_age)
#print(price)
#print(age + str_age) Error different type operation

#practice
#create variable for
#1. your favourite move (string)
#fav_mov = "Sex and The City"
#2. Year it was released (integer)
#year = 2004
#3. Movie Rating
#rating = 7.5
#4 Recommend
#rec = True
#print (fav_mov)
#print (year)
#print ("This is ", fav_mov, "and it released on", year)
#------------------------------------------------------
#Conversion Challenge Convert 3 variable to proper type and find
# sum of all 3 , Product of first two and Division of first by third
#num1_str = "15"
#num2_str = "7.5"
#num3_str = "3"
#num1 = int("15")
#num2 = float("7.5")
#num3 = int("3")
#print(num1 + num2 + num3)
#print(num1 * num2)
#print(num1 / num3)
#-------------------------------------------------------
#Exercise Calculator Practice
#Create a simple Calculator that :
#1. Take 2 number from user
#2. Perform all arithmatic operations
#3. Displays results
#num1 = float(input("Please enter 1st number:  "))
#num2 = float(input("Please enter 2nd number:  "))
#print("Result from Calculator")
#print(f"{num1} + {num2} = {num1 + num2}")
#print(f"{num1} - {num2} = {num1 - num2}")
#print(f"{num1} * {num2} = {num1 * num2}")
#if num2 !=0:
#    print(f"{num1} / {num2} = {num1 / num2}")
#else :
#    print("cannot divde by zero")
#    print(f"{num1} ** {num2} = {num1 ** num2}")

#------------------------------------------------------
#Exercise String Manipulation
#Given a sentence write a program to:
# Count total characters
# Count Words
# Reverse the sentence
# Check if it's a palindrome (ignoring spaces and case)
#sentence = "A man a plan a canal Panama"
#print(f"{sentence}")
#print(f"Character Count: {len(sentence)}")
#print(f"Word Count: {len(sentence.split())}")
#print(f"Reversed: {sentence[::-1]}")
#Palindrome check
#------------------------------------------------------
#name = input("What is your name ?")
#age = input("How old are you ?")
#city = input("Where is your locate?")
#job = input("What is your dream job?")
#print("Personal Information")
#print(f"Personal Name: {name}")
#print(f"Age : {age}")
#print(f"Address : {city}")
#print(f"Dream job : {job}")

#------------------------------------------------------
"""
#Exercise Temperature Conversion
def temperature_conversion(): 
    print("Temperature Conversion")
    print("1 Conversion Temperature to Degree Celcious")
    print("2 Convert Temperature to Farenheit")
    choice = input("please Select 1 or 2 ?")

    if choice == "1":
        temp_input = input("Enter temperature in Farenhiet:")
        farenheit_f = float(temp_input)
        celcious_t = (farenheit_f - 32) * 5 / 9
        print("temperature",farenheit_f,"F equal to",celcious_t,"C")
    elif choice == "2":
        temp_input = input("Enter temperature in Celcious:")
        celcious_f = float(temp_input)
        farenheit_t = (celcious_f * 9/5) + 32
        print("temperature",Celcious_f,"C equal to",farenheit_t,"F")
    else :
        print("Invalid input")
#------------------------------------------------------------
# Exercise Classified People By Age group

def Age_Classified():
    print("Classified People By Age Group")
    age_str = input("How old are you? :")
    age_int = int(age_str)
    
    if age_int > 0 and age_int < 10 :
        print("Group1: Baby")
    elif age_int >= 10 and age_int < 20 :
        print("Group2: Teenager")
    elif age_int >= 20 and age_int < 30 :
        print("Group3: Yound Adult")
    elif age_int >= 30 and age_int < 60 :
        print("Group4: Adult")
    elif age_int >= 60 :
        print("Group5: Senior")
    else:
        print("Invalid Output")
"""
#--------------------------------------------------------------
"""
Given 2 int return their product if product equal or less than 1,000
otherwise return sum of them

number1 = 30
number2 = 40
Product = number1 * number2
if Product <= 1000 :
    print(Product)
else :
    print(number1+number2)

"""
#----------------------------------------------------------------
        
"""
#number = 0
#for i in range (15) :
    pass
    if i != 0 :
        Accum = i + i-1
        print('Current Number', i, 'Previous', i-1, 'Sum:', Accum)
    else :
        Accum = i + number
        print('Current Number', i, 'Previous', number, 'Sum:', Accum)

Output 
Current Number 5 Previous 4 Sum: 9
Current Number 6 Previous 5 Sum: 11
Current Number 7 Previous 6 Sum: 13
Current Number 8 Previous 7 Sum: 15
Current Number 9 Previous 8 Sum: 17
Current Number 10 Previous 9 Sum: 19
Current Number 11 Previous 10 Sum: 21
Current Number 12 Previous 11 Sum: 23
Current Number 13 Previous 12 Sum: 25
Current Number 14 Previous 13 Sum: 27
"""    
#------------------------------------------------------------------
#print character at even index number
"""
Word = 'PyNative'
Slice = list(Word)
print(Slice)
i = 0
for i in range(8) :
    if i % 2 == 0 :
        print(Slice[i])

Output 
['P', 'y', 'N', 'a', 't', 'i', 'v', 'e']
P
N
t
v
"""     
#--------------------------------------------------------------------
#Write a python to remoce first n character from 0 to in strin
"""
def remove_char(word, n) :
    count_char = len(word)
    start_slice = count_char - n 
    slice = word[start_slice:]
    return slice

print(remove_char('Pynative', 4))
print(remove_char('Promkaew', 5))

Output
tive
mkaew
"""
#---------------------------------------------------------------
"""
# Check if the first and last numbers of a list are the same    
def check_first_last(list):
    #access list from first
    first = list[0]
    last = list[-1]
    if first == last :
        return True
    else : 
        return False
    
list1 = [10, 20, 30, 40, 10]  
list2 = [75, 65, 35, 75, 30]
print(check_first_last(list1))
print(check_first_last(list2))

Output 
True
False
"""
#-------------------------------------------------------------------
"""
#Display number divisible by 5
def divisible(A) :
    for i in range(len(A)):
        if A[i] % 5 == 0 :
          print(A[i])
             
AB = [10, 20, 33, 46, 55]
print(divisible(AB))

output
10
20
55
"""
#--------------------------------------------------------------------
"""
#Exercise 7: Find the number of occurrences of a substring in a string
def find_string(STR, Key):
    list_of_str = STR.split(" ")
    i = STR.count(Key)  
    print(f"{Key} appeared {i} times")


Word = ("Emma is good developer. Emma is a writer")
find_string(Word, "Emma")
"""
#----------------------------------------------------------------------
# Print the following Pattern
"""
1
2 2
3 3 3
4 4 4 4
5 5 5 5 5
    
def Pattern(Num) :
    i = 1
    for i in range(Num):
        i = str(i)
        count = int(i)
        
        pattern = ((f"{i} ") * count)
        print (pattern)
    
Pattern(6)
"""
#----------------------------------------------------------
"""
# Check Palindrome Number
def chk_palindrome (Num) : 
    Number1 = str(Num)
    Number2 = (str(Num)[::-1])
    if Number1 == Number2 : 
        print('Yes. given number is palindrome number')
    else :
        print('No. given number is not palindrome number')

chk_palindrome(454)
chk_palindrome(423)
Output
    454
Yes. given number is palindrome number
324
No. given number is not palindrome number
    """
#------------------------------------------------------------
"""
#Given two lists of numbers, write Python code to 
#create a new list containing odd numbers from the
#first list and even numbers from the second list.
def create_new_list(A, B) :
    A = list(A)
    B = list(B)
    c = list()
    d = list()
    for i in range(len(A)) :
        if A[i] % 2 != 0 :
           c.append(A[i]) #Don't Assign just Append
    for i in range(len(B)) :
        if B[i] % 2 == 0 :
           d.append(B[i])
    print(c + d)

L1 = [10, 20, 25, 30, 35]
L2 = [40, 45, 60, 75, 90]
create_new_list(L1, L2)
[25, 35, 40, 60, 90]
    """
#----------------------------------------------------------------
"""
# Get Each Digit from a number in reverse order
def Reverse_num (Num) :
    while Num > 0 :
        di
        
        git = Num % 10
        number = Num // 10
        print (digit, end=" ")
Number = 7536
Reverse_num(Number)     
"""
#---------------------------------------------------------------------------------------
#Calculate incomtax
"""
|  taxable inc  |  Rate in (%) |
--------------------------------
| first 10,000  |   0          |
| Next 10,000   |   10         |
| The reamining |   20         |
---------------------------------

def cal_inctax (inc) :
    inc = int(inc)
    #Check if income > 10,000 or no
    if inc <= 10000 :
        tax = 0
    elif inc >= 10000 and inc <= 20000 :
        first_over = inc - 10000
        tax = first_over * 0.1 
    elif inc > 20000 :
        tax1 = 10000 * 0.1 
        left_inc = inc - 20000
        tax2 = left_inc * 0.2
        tax = tax1 + tax2 
    print(tax)
"""
#--------------------------------------------------------------
#print multiplication table from 1 to 10
"""
def multiplication_table() :
    for i in range (1, 11):
        for j in range (1, 11):
            print(i * j, end=" ")
        print("\t\t")        
    
multiplication_table()

1 2 3 4 5 6 7 8 9 10 
2 4 6 8 10 12 14 16 18 20 
3 6 9 12 15 18 21 24 27 30 
4 8 12 16 20 24 28 32 36 40 
5 10 15 20 25 30 35 40 45 50 
6 12 18 24 30 36 42 48 54 60 
7 14 21 28 35 42 49 56 63 70 
8 16 24 32 40 48 56 64 72 80 
9 18 27 36 45 54 63 72 81 90 
10 20 30 40 50 60 70 80 90 100 

"""
#------------------------------------------------------
"""
#print downward half pyramid
def pyramid() :
    for i in range (5, 0, -1):
        print("* " *  i, end = " ")
        print("\n")
pyramid()
* * * * *  

* * * *  

* * *  

* *  

*  

"""
#-------------------------------------------------------
"""
# Get an int value of base raises to the power of exponent
def exponent(base, exp) :
    result = 1
    for i in range(exp):
        result = result * base
    print(result)
exponent (2, 5)
exponent (5, 4)
    """
#--------------------------------------------------------
"""
#Check palindrome number
def palindrome_num (number):
    number = str(number)
    number1 = number[::-1]
    if number == number1 :
        print('palindrome')
        return True
    else :
        print('Not palindrome')
        return False

palindrome_num(121)
    """
#--------------------------------------------------------
"""
#1. The stock_info( ) function is defined. Using the appropriate attribute of the stock_info( ) function, display
# the names of all arguments to this function to the console.
def stock_info(company, country, price, currency):
    company = str(company)
    country =  str(country)
    price = str(price)
    currency = str(currency)
    return f"Company :{company}\nCountry:{country}\nPrice:{currency}{price}"


print(stock_info('ABC', 'USA', 115, "$"))
"""
#-------------------------------------------------------
