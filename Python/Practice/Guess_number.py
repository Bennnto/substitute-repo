import random

seCret_num = random.randint(1, 50)

#Ask for Guess Number
print('Guess your number')


for guess_No in range(1, 6):
    print('Take a guess.')
    guess_Num = input('>')
    guess_Num = int(guess_Num)
    if guess_Num < seCret_num:
        print('Your number is a bit less than what i think')
        continue
    elif guess_Num > seCret_num:
        print('Your number is a bit higher than what i think')
        continue
    elif guess_Num == seCret_num:
        print('Gotcha you guess a correct number',guess_Num,'Secret Number is',seCret_num)
        break
print('Thank you')
