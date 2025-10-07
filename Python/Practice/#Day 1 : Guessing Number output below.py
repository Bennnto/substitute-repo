#Day 1 : Guessing Number output below 
"""
    I'm thinking of a number between 1 and 100.

Guess the number:
50

Too high! Try again.
Guess the number:
25

Too low! Try again.
Guess the number:
37

Congratulations! You guessed it in 3 attempts.
    """
    
import random

def guess_numb():
    print('Guess Number is :')
    while True :
        guess_n = input('>')
        guess_n = int(guess_n)
        if guess_n > 100 or guess_n <= 0 :
            print('Only input 1 to 100')
            continue
        else:
            break
    return guess_n

print('I am thinking of a number between 1 and 100')
#Random Number using random
random_number = random.randint(1, 100)
print('You have only 3 attempts to guess')
for i in range(3):
    guess_number = guess_numb()
    if random_number > guess_number :
        print('Too low! Try again.')
        continue
    elif random_number < guess_number :
        print('Too high! Try again.')
        continue
    elif random_number == guess_number :
        print('Congratulations! You guessed it in 3 attempts')
        break
    else :
        print('Unfortunately Let Try agiain Next time.')
        
