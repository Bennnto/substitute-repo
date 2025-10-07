#!/usr/bin/env python3

def grading():
    print('Please Enter Score to Calculate Grade')
    Score = input('>')
    Score = float(Score)
    if Score > 0.00 and Score < 50.00 :
        print("Grade 'F' Not Pass required")
    elif Score >= 50.00 and Score < 60.00 :
        print("Grade 'D' Pass Minimum")
    elif Score >= 60.00 and Score < 70.00 :
        print("Grade 'C' Pass")
    elif Score >= 70.00 and Score < 80.00 :
        print("Grade 'B' Pass")
    elif Score >= 80.00 and Score < 90.00 :
        print("Grade 'A' Pass")
    elif Score >= 90.00 and Score <= 100 : 
        print ("Grade 'A+' Pass")

def aCcess():
    print('Would you like to calculate Grade ? Answer Y or N')
    ansWer = input('>')
    ansWer = str(ansWer)
    if ( ansWer == 'Y' or ansWer == 'y' ):
        grading()
        aCcess()
    else :
        print('Exiting Program... Thank you!')
        exit()

aCcess()

