# Author:                   Dan Mohler
# FileCopyRename.py         A program to sort files using account numbers
# Last modified             3/9/2019
# Python Version            Python 3.7.2

# Application Notes
# Parameters are specified in the following order:
# fileDir, folderDir, optional parameters
# fileDir is the location of directory that contains files to be copied
# folderDir is the location of directory that contains subfolders to copy files
# -d is a flag that specifies debug mode

import sys, argparse, sqlite3, shutil, os



def parseDir(directory, database, year):
    # This function performs directory parsing
    # print("Input Source: %s\tdirectory" % (directory))

    # verify that directory exists to be parsed
    if not (os.path.isdir(directory)):
        print("% is not a valid file directory." % (directory))
        sys.exit()

    endDir = os.path.basename(directory)
    # print("file %s" % (endFile))

    # verify that file is sufficiently long
    if (len(endDir) >= 4):
        shortDir = endDir[-4:]
        if (shortDir[0] == ' ' and shortDir[1:].isnumeric() ):
            numbers = shortDir[1:]
            # do not add folders from other years
            if not (endDir[:4].isnumeric() and endDir[:4] != year):
                # code to update SQL database
                try:
                    cursor = database.cursor()
                    cursor.execute('''INSERT INTO accounts(num, year, fullDir, endDir)
                        VALUES(?,?,?,?)''', (numbers, year, directory, endDir))
                    cursor.close()
                except Exception as e:
                    print(e)
                    print(" Record to be inserted has the following values:")
                    print("num: ", numbers)
                    print("year: ", year)
                    print("fullDir: ", directory)
                    print("endDir: ", endDir)

    # print(os.listdir(directory))
    for item in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, item)):
            parseDir(os.path.join(directory, item), database, year)
    # for every subdirectory (next sublevel), call function with new path
    return;

if __name__ == '__main__':
    # parser initialization
    parser = argparse.ArgumentParser(
        description = "File sort by account numbers."
    )
    # parameter specification
    parser.add_argument('fileDir', help = "Directory of files to copy")
    parser.add_argument('folderDir', help = "Directory to copy files to subfolders")
    parser.add_argument('year', help = "Year to copy files")
    # argument parsing
    args = parser.parse_args()

    # current directory
    if not args.year.isnumeric():
        print("% is not a valid year." % (args.year))
        sys.exit()

    numDB = sqlite3.connect(':memory:')
    d = numDB.cursor()
    d.execute('''CREATE TABLE accounts(num TEXT, year TEXT, fullDir TEXT, endDir TEXT UNIQUE)''')
    numDB.commit()
    # build database
    parseDir(args.folderDir, numDB, args.year)

    # print table
    #d.execute('''SELECT num, endDir FROM accounts''')
    #for row in d:
        #print('{0} : {1}'.format(row[0], row[1]))

    # perform file move
    for item in os.listdir(args.fileDir):
        if os.path.isfile(os.path.join(args.fileDir, item)):
            itemName = os.path.splitext(item)[0]
            if (len(itemName) > 5 and itemName[-4:-3] == ' ' and itemName[-3:].isnumeric()):
                itemNumber = itemName[-3:]
                # if file has year, require match, if not place in current year
                if (itemName[:4] == args.year or not itemName[:4].isnumeric()):
                    try:
                        d.execute('''SELECT fullDir FROM accounts WHERE year=? AND num=?''', (args.year, itemNumber))
                        result = d.fetchone()
                        if result is not None:
                            if (os.path.isfile(os.path.join(result[0], item))):
                                i = 2
                                while True:
                                    fileName = itemName[:-4]+'-'+str(i)+itemName[-4:]+os.path.splitext(item)[1]
                                    if not (os.path.isfile(os.path.join(result[0],fileName))):
                                        break
                                    i+=1
                                shutil.move(os.path.join(args.fileDir, item), os.path.join(result[0], fileName))
                            else:
                                shutil.move(os.path.join(args.fileDir, item), os.path.join(result[0], item))
                    except Exception as e:
                        print(e)

    # cleanup
    d.execute('''DROP TABLE accounts''')
    numDB.commit()
    d.close()
    numDB.close()
