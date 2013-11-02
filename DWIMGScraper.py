# -*- coding: utf8 -*-

# DWIMGScraper.py - Downloads all your DayViews.com images to a local directory.
# Version 1.5
# Contact: micke.lind@gmail.com
#
# Required: Python 2.7 with extra libraries BeautifulSoup(http://www.crummy.com/software/BeautifulSoup/)
# and requests (http://www.python-requests.org/en/latest/)installed.
#
# Version history:
# 1.0 - First acceptable version.
# 1.01 - Changed some strings to make it work better on nonwindows platforms
# 1.2 - Merged some layout changes submitted by https://github.com/lndbrg
# 1.5 - Rewrote Page fetching function to avoid unexpected filename errors. Script should exit in a nice way now.
#
# Usage: 'python DWGIMGScraper.py username password' Run the script from the directory you want to download to.
#
# To Do:
# * Add option to save to a given directory

from __future__ import print_function
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
    return s.get('http://dayviews.com/{0}/home'.format(user))

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
def getImageFromPageAndGiveNext(s,link,user):
    r = s.get(link)
    soup = BeautifulSoup(r.text)
    dateAndNr = soup.find('p',id='showContentTitle')
    try:
        date = dirNameParse(dateAndNr.text)
    except AttributeError:
        date = 'unknown'
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
    return nextPageLink

#Parses correct name for directory
def dirNameParse(dirName):
    _, day, month, year, _ = dirName.split(' ', 4)
    if len(day) == 1:
        day = '0{0}'.format(day)
    lookUpMonth = {'januari': '01', 'februari': '02', 'mars': '03', 'april': '04',
                   'maj' : '05', 'juni' : '06', 'juli' : '07', 'augusti': '08',
                   'september' : '09', 'oktober': '10', 'november' : '11', 'december' : '12'}
    month = lookUpMonth.get(month,'None')
    return('{0}-{1}-{2}'.format(year, month, day))

#Parses correct filename from url
def fileNameParse(fileName):
    _, _, fileName = fileName.rpartition('/')
    return fileName

#Image saver
def saveImageToDisk(s,link,date,user):
    r = s.get(link, stream=True)

    dirName = '{0}/{1}/{2}'.format(os.getcwd(), user, date)
    fileName = fileNameParse(link)

    print('Downloading file {0} to {1} ..'.format(fileName, dirName))

    try:
        os.makedirs(dirName)
    except:
        if os.path.exists(dirName):
            pass

    fullName = '{0}/{1}'.format(dirName, fileName)

    outFile = open(fullName,'wb')
    shutil.copyfileobj(r.raw, outFile)
    del r

    print('Saved as {0}\n'.format(fileName))

#Logout function
def DWLogOut(s):
    _ = s.get('http://dayviews.com/?action=logout')

#Main - runs at start
def main():

    #Parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('user', action='store', help='Dayviews username')
    parser.add_argument('pw', action='store', help='Dayviews password')
    args = parser.parse_args()

    #Login to Daywievs
    print('\n\nLogging in to Dayviews.com with the supplied username and password...\n\n')
    r,s = DWLogin(args.user,args.pw)

    #Check that login went well
    if(checkLogin(r)):
        print('Login successful!\n')
    else:
        print('Login failed!\nPlease check that the username and password given are correct!\n\n')
        exit(1)

    #Go to user homepage
    DWHomeP = getDWHomeP(s,args.user)

    #Extract first (latest) image link from user homepage
    nextPageLink = getImageLinkFromHomeP(DWHomeP)

    print('Starting download...\n\n')
    #Iterate through pages and extract images
    while 1:
        nextPageLink = getImageFromPageAndGiveNext(s,nextPageLink,args.user)
        if (nextPageLink == None):
            break

    #Logout in a nice way
    print('Done!\n Logging out from Dayviews.com..')
    DWLogOut(s)

if  __name__ =='__main__':
    main()
