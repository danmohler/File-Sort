# Author:                   Dan Mohler
# FileSort.py               A program to sort files using account numbers
# Last modified             10/14/2021
# Python Version            Python 3.7.4


# Application Notes
# Parameters are specified in the following order:
# fileDir, folderDir, optional parameters
# fileDir is the location of directory that contains files to be copied
# folderDir is the location of directory that contains subfolders to copy files
# -d is a flag that specifies debug mode

# file format
# "YYYY-MM-DD Name ACCOUNT_NUMBER"


import sys, argparse, sqlite3, shutil, os

class FileSort:
    def __init__(self, year, folderDir, fileDir):
        self.year = year
        self.folderDir = folderDir
        self.fileDir = fileDir

        # set length of account numbers
        self.ACCOUNT_LENGTH = 3
        self.FILE_END_LENGTH = self.ACCOUNT_LENGTH + 1

        # Minimum file length requires character, space, and account
        self.MIN_FILE_LENGTH = self.ACCOUNT_LENGTH + 2

        # Number of digits used to specify year
        self.YEAR_LENGTH = 4

        # Create dictionary to store file structure of disk
        self.fileDB = {}

        self.totalFiles = 0
        self.ignoredFiles = 0
        self.totalFolders = 0
        self.accountFolders = 0

        if not (self.InputValidation()):
            sys.exit("Input validation failed")

    def InputValidation(self):
        # verify that directory exists to be parsed
        if not (os.path.isdir(self.folderDir)):
            print(f"{self.folderDir} is not a valid file directory.")
            return False

        # Verify that year is a number
        if not self.year.isnumeric():
            print(f"{self.year} is not a valid year.")
            return False

        return True

    def ValidateAccountDir(self, basename):
        # Function validates that output directory basename has proper
        # formatting to match a year and an account
        # Returns True if a valid output directory basename
        # Returns False if not a a valid output directory basename

        # verify that directory is sufficiently long
        # and has proper "...Name ACCOUNT_NUMBER" end formatting
        if (len(basename) < self.MIN_FILE_LENGTH):
            return False
        elif (basename[-self.FILE_END_LENGTH] != ' '):
            return False
        elif not (basename[-self.ACCOUNT_LENGTH:].isnumeric()):
            return False

        # Add folder if the year matches
        if (basename[:self.YEAR_LENGTH] == self.year):
            return True
        # Add folder if it has no year
        elif not (basename[:self.YEAR_LENGTH].isnumeric()):
            return True
        else:
            return False


    def ParseDir(self, directory=None):
        # This function performs directory parsing
        if directory is None:
            directory = self.folderDir

        endDir = os.path.basename(directory)
        self.totalFolders += 1

        if self.ValidateAccountDir(endDir):
            numbers = endDir[-self.ACCOUNT_LENGTH:]
            self.fileDB[numbers] = {
                'full_directory': directory,
                'basename': endDir
            }
            self.accountFolders += 1

        # For every subdirectory (next sublevel), call function with new path
        for item in os.listdir(directory):
            nextDir = os.path.join(directory, item)
            if os.path.isdir(nextDir):
                self.ParseDir(nextDir)

        return;

    def FileValidate(self, directory, filename):
        # Check if the file exists
        if not os.path.isfile(os.path.join(directory, filename)):
            return False

        filenameNoExt = os.path.splitext(filename)[0]

        if (len(filenameNoExt) < self.MIN_FILE_LENGTH):
            return False
        elif filenameNoExt[-self.FILE_END_LENGTH:-self.ACCOUNT_LENGTH] != ' ':
            return False

        accountNumber = filenameNoExt[-self.ACCOUNT_LENGTH:]
        if not (accountNumber.isnumeric()):
            return False
        elif not (accountNumber in self.fileDB):
            return False

        # if file has year, require match, if not place in current year
        if (filenameNoExt[:self.YEAR_LENGTH] == self.year):
            return True
        elif not (filenameNoExt[:self.YEAR_LENGTH].isnumeric()):
            return True
        else:
            return False

    def Deduplicate(self, filepath, filename):
        i = 2

        newFn = filename
        fnNoExt = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]
        fnNoAccount = fnNoExt[:-self.FILE_END_LENGTH]
        fileEnd = fnNoExt[-self.FILE_END_LENGTH:]

        # Check for existing file
        while os.path.isfile(os.path.join(filepath, newFn)):
            newFn = fnNoAccount + '-' + str(i) + fileEnd + ext
            i += 1
        return newFn

    def FileMove(self):
        # perform file move for each file in the filing directory
        for filename in os.listdir(self.fileDir):
            self.totalFiles += 1
            if self.FileValidate(self.fileDir, filename):
                fnNoExt = os.path.splitext(filename)[0]
                fnAccount = fnNoExt[-self.ACCOUNT_LENGTH:]

                # Get directory for file
                destPath = self.fileDB[fnAccount]['full_directory']
                destFilename = self.Deduplicate(destPath, filename)

                shutil.move(os.path.join(self.fileDir, filename), os.path.join(destPath, destFilename))
            else:
                self.ignoredFiles += 1


if __name__ == '__main__':
    # parser initialization
    parser = argparse.ArgumentParser(
        description = "Sorts files into folders based on account numbers."
    )
    # parameter specification
    parser.add_argument('fileDir', help = "Directory of files to copy")
    parser.add_argument('folderDir', help = "Directory to copy files to subfolders")
    parser.add_argument('year', help = "Year to copy files")
    # argument parsing
    args = parser.parse_args()
    print(f'Year:{args.year} Folder:{args.folderDir} File:{args.fileDir}')
    filer = FileSort(args.year, args.folderDir, args.fileDir)
    filer.ParseDir()
    filer.FileMove()
    print(f'{filer.accountFolders} account folders were found out of {filer.totalFolders} folders in directory.')
    print(f'{filer.totalFiles-filer.ignoredFiles} of {filer.totalFiles} files were moved.')
    print(f'{filer.ignoredFiles} files were ignored.')
