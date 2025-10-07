import random
print('Hey ! Welcome to Number Guessing Game')

print('Instruction!\n' + 'you have 5 chance to guessing the random number by input Range of number you would like to guess')

def chk_range():
    print('Please Enter Number in positive(+) integer value of range of number to random')
    try:
        print('Enter Lower bound')
        low = input('>')
        low = int(low)
        print('Enter Higher bound')
        high = input('>')
    except ValueError :
        print('Incorrect number format')
        return None

# check if high - low bound is in correct format of number of not 
    if low < 0 or high < 0 :
    print ('low and high number should be positive value')
        return None

    if low > high :
    print('lower bound should less than higher bound')
        return Non

# Start Main Program
chk_range()
print('Your range of guess number is in' + str(low) + 'to' + str(high))
return(low, high)

#Ask user inout Guessing number
print('Please Enter Number in Positive(+) integer to guess')
guess = input('>')

#random number from range 
random_num = random.randint(low, high)
ch = 5 
count = 0

while count < ch :
    if guess < low or guess > high :
        print('Your guess number not in range')
        count +=1
    elif guess > random_num :
        print('Too high! Try again')
        count +=1
    elif guess < random_num : 
        print('Too Low! Try again')
        count +=1
    elif guess = random_num :
        break


print(f'Congratulation your guess number {guess} matched with random number {random_num}')


