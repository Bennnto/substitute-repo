!/urs/bin/python3 
import os 
import sys
import seedir as sd


def back_to_main():

    print('Back to Main Menu Y or N')
    ans = input('>')
    ans = str(ans)
    if ans == 'Y' or ans == 'y' :
        Main()
    elif ans == 'N' or ans == 'n' :
        exit
    else : 
        print('Invalid input try again')
        return

 
def list_file_tree ():  
    print('Please Enter your directory path')
    path = input('>')
    #check if path exists or not
    path_exists = os.path.exists(path)
    if path_exists :
        sd.seedir(path = path, style = 'emoji', depthlimit = 2,
                  exclude_folders=['.git', '.JSON', '.config', '.DS_Store', '.gitignore', '.nvm', '.tmux'])
    else : 
        print("Path doesn't exists")
        back_to_main()


def list_all_dir ():
    """
    list all dir use to list all of files and directories in specified Path that 
    input by user 
    
    """

    print('Please enter your files or directories path')
    path = input('>')
    path_exists = os.path.exists(path)

    if path_exists :
        list_file = os.listdir(path)
        print(list_file)
    else :
        os.mkdir(path)
        print("Path doesn't exists create new directory")
        back_to_main()


def remove_dir ():
    """
    This function use to remove both files and directories
    Logic of function :
    - Ask Users to input path to work with
    - Ask Users Select Remove files or directories
    - Check if files or directories exists
    - Remove files or directories and Show confirmation

    """
    print('Please enter your files or directories path')
    path = input('>')
    path_exists = os.path.exists(path)

    if path_exists :
        print('Would you like to delete files or directory/n Y or N')
        ans = input('>')
        if ans == 'y' or ans == 'Y' :
            os.rmdir(path)
            print('Removed files/Directories completed')
        else :
            print('Invalid Input...')
            remove_dir()
    else:
        print("Files/Directories doesn't exists")
    
        



def Main():

    print('File / Directories Management System')
    print('------------ Main Menu -------------')
    print('1. List files/directories')
    print('2. Remove files/directories')





