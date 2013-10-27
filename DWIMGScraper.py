# -*- coding: utf8 -*-

# DWIMGScraper.py - Downloads all your DayViews.com images to a local directory.
# Version 1.01
# Contact: micke.lind@gmail.com
#
# Required: Python 2.7 with extra libraries BeautifulSoup(http://www.crummy.com/software/BeautifulSoup/)
# and requests (http://www.python-requests.org/en/latest/)installed.
#
# Version history:
# 1.0 - First acceptable version.
# 1.01 - Changed some strings to make it work better on nonwindows platforms
#
# Usage: 'python DWGIMGScraper.py username password' Run the script from the directory you want to download to. 
#
# To Do:
# * Better error handling in function getImageFromPageAndGotoNext
# * Add option to save to a given directory


from bs4 import BeautifulSoup
import requests
import os
import shutil
import argparse

#Login function
def DWLogin(user, pw):
    payLoad = {'action':'login',
               'name':'login',
               'crosslogin':'0',
               'diaryname':'',
               'id':'',
               'directlink':'',
               'bdbhdCampaign':'0',
               'topLoginNoJScript':'1',
               'ajaxlogin':'0',
               'doIframeLogin':'0',
               'user':user,
               'pass':pw }

    post_headers = {'content-type': 'application/x-www-form-urlencoded'}
    
    #Try to login
    s = requests.Session()
    r = s.post('http://dayviews.com/',data=payLoad,headers=post_headers)

    #Return response and session
    return (r,s)


# Go to user homepage function
def getDWHomeP(s,user):
    HomePString = 'http://dayviews.com/'+ user +'/home/'
    r = s.get(HomePString)
    return r

# Check login
def checkLogin(r):
    cookies = r.cookies.get_dict()
    #If the correct cookies were not set, exit the program.
    if 'lastlogin_userid' and 'dv_sessionid' in cookies:
        return True
    else:
        return False

# Homepage scraper
def getImageLinkFromHomeP(r):
    soup = BeautifulSoup(r.text)
    start = soup.find(text='Mina bilder')
    link = start.find_next('a')
    return link.get('href')

#Image find scraper
def getImageFromPageAndGotoNext(s,link,user):
    r = s.get(link)
    soup = BeautifulSoup(r.text)
    dateAndNr = soup.find('p',id='showContentTitle')
    date = dirNameParse(dateAndNr.text)
    imgUrl = soup.find('img', id='picture')
    try:
        saveImageToDisk(s,imgUrl.get('src'),date,user)
    except AttributeError:
        pass
    
    try:
        nextPageLink = soup.find('a', title='Föregående dag').get('href')
    except AttributeError:
        try:
           nextPageLink = soup.find('a', title='Föregående bild').get('href')
        except AttributeError:
            nextPageLink = None
            pass
        
    if (nextPageLink != None):
        getImageFromPageAndGotoNext(s,nextPageLink,user)

#Parses correct name for directory
def dirNameParse(dirName):
    strArray = dirName.split(' ')
    day = strArray[1] #day
    if len(day) == 1:
        day = '0'+day
    year = strArray[3] #year
    lookUpMonth = {'januari': '01', 'februari': '02', 'mars': '03', 'april': '04',
                   'maj' : '05', 'juni' : '06', 'juli' : '07', 'augusti': '08',
                   'september' : '09', 'oktober': '10', 'november' : '11', 'december' : '12'}
    month = lookUpMonth.get(strArray[2],'None')
    return(year +'-'+ month +'-'+ day)

#Parses correct filename from url
def fileNameParse(fileName):
    strArray = fileName.split('/')
    lastOfArray = len(strArray)
    return strArray[lastOfArray-1]

#Image saver
def saveImageToDisk(s,link,date,user):
    r = s.get(link, stream=True)

    dirName = os.getcwd() + '/' + user + '/' + date
    print 'Downloading file ' + fileNameParse(link) +' to '+ dirName+'..'
    
    try:
        os.makedirs(dirName)
    except:
        if os.path.exists(dirName):
            pass

    fileName = fileNameParse(link)

    fullName = dirName+'/'+fileName

    outFile = open(fullName,'wb')
    shutil.copyfileobj(r.raw, outFile)
    del r

    print 'Saved as '+fileName+'!\n'
        
#Logout function
def DWLogOut(s):
    r = s.get('http://dayviews.com/?action=logout')
    return r
    

#Main - runs at start
def main():

    #Parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('user', action='store', help='Dayviews username')
    parser.add_argument('pw', action='store', help='Dayviews password')
    args = parser.parse_args()
    
    #Login to Daywievs
    print("\n\nLogging in to Dayviews.com with the supplied username and password...\n\n")
    r,s = DWLogin(args.user,args.pw)

    #Check that login went well
    if(checkLogin(r)):
        print('Login successful!\n')
    else:
        print ('Login failed!\nPlease check that the username and password given are correct!\n\n')
        exit()        
    
    #Go to user homepage
    DWHomeP = getDWHomeP(s,args.user)

    #Extract first (latest) image link from user homepage
    firstLink = getImageLinkFromHomeP(DWHomeP)

    print('Starting download...\n\n')
    #Iterate through pages and extract images
    getImageFromPageAndGotoNext(s,firstLink,args.user)

    #Logout in a nice way
    print("Done!\n Logging out from Dayviews.com..")
    foo = DWLogOut(s)

if  __name__ =='__main__':main()
