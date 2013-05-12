#!/usr/bin/env python
import re
import os
import sys
from getpass import *
from mechanize import Browser
from bs4 import BeautifulSoup

"""

This program downloads scpd videos for a given class in the order
that they happened as a wmv, then converts them to a mp4. Each time 
the script is run, it will update to download all of the undownloaded
videos. 

This script is modified from the one by Ben Newhouse (https://github.com/newhouseb).

Unfortunately, there are lots of dependencies to get it up and running
1. Handbrake CLI, for converting to mp4: http://handbrake.fr/downloads2.php
2. BeautifulSoup for parsing: http://www.crummy.com/software/BeautifulSoup/
3. Mechanize for emulating a browser, http://wwwsearch.sourceforge.net/mechanize/

Usage: python scrape.py [Stanford ID] "Interactive Computer Graphics"

The way I use it is to keep a folder of videos, and once I have watched them, move them
into a subfolder called watched. So it also wont redowload files that are in a subfolder
called watched.


"""

def convertToMp4(wmv, mp4):
    print "Converting ", mp4
    os.system('HandBrakeCLI -i %s -o %s' % (wmv, mp4))
    os.system('rm -f %s' % wmv)

def download(work, courseName):
    # work[0] is url, work[1] is wmv, work[2] is mp4
    if os.path.exists(work[1]) or os.path.exists(courseName + "/" + work[1]) or os.path.exists(courseName + "/" + work[2]) or os.path.exists("watched/"+work[1]) or os.path.exists(work[2]) or os.path.exists("watched/"+work[2]):
        print "Already downloaded", work[1]
        return

    print "Starting", work[1]
    os.system("mimms -c %s %s" % (work[0], work[1]))
    # convertToMp4(work[1], work[2])
    print "Finished", work[1]
    
def assertLoginSuccessful(forms):
    for form in forms:
        if (form.name == "login"):
            print "Login Error: username or password likely incorrect"
            sys.exit(0)


def downloadAllLectures(username, courseName, password):
    br = Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6; en-us) AppleWebKit/531.9 (KHTML, like Gecko) Version/4.0.3 Safari/531.9')]
    br.set_handle_robots(False)
    br.open("https://myvideosu.stanford.edu/oce/currentquarter.aspx")
    assert br.viewing_html()
    br.select_form(name="login")
    br["username"] = username
    br["password"] = password

    # Open the course page for the title you're looking for 
    print "Logging in to myvideosu.stanford.edu..."
    response = br.submit()

    # Assert that the login was successful
    assertLoginSuccessful(br.forms())
        
    # Assert Course Exists
    try:
        response = br.follow_link(text=courseName)
    except:
        print 'Course Read Error: "'+ courseName + '"" not found'
        return


    # Print response.read()    
    print "Logged in, going to course link."

    # Build up a list of lectures
    print '\n=== Starting "' + courseName + '" ==='
    print "Loading video links."
    links = []
    for link in br.links(text="WMP"):
        links.append(re.search(r"'(.*)'",link.url).group(1))
    link_file = open('links.txt', 'w')
    # So we download the oldest ones first.
    links.reverse()

    print "Found %d links, getting video streams."%(len(links))
    videos = []
    for link in links:
        response = br.open(link)
        soup = BeautifulSoup(response.read())
        video = soup.find('object', id='WMPlayer')['data']
        video = re.sub("http","mms",video)        
        video = video.replace(' ', '%20') # remove spaces, they break urls
        output_name = re.search(r"[a-z]+[0-9]+[a-z]?/[0-9]+",video).group(0).replace("/","_") #+ ".wmv"
        output_wmv = output_name + ".wmv"
        link_file.write(video + '\n')
        print video
        output_mp4 = output_name + ".mp4"
        videos.append((video, output_wmv, output_mp4))
    link_file.close()

    print "Downloading %d video streams."%(len(videos))
    for video in videos:
        download(video, courseName)

    print "Done!"

def downloadAllCourses(username, courseNames):
    password = getpass()
    for courseName in courseNames:
        downloadAllLectures(username, courseName, password)


def printHelpDocumentation():
    print "\n       "
    print "=== SCPD Scrape Help==="
    print "Usage:"
    print "  python scrape.py 'username' '--flag1' ... '--flagN' 'courseName1' 'courseName2' ... 'courseNameN'"
    print "Flags:"
    print "  --all: downloads all new videos based on names of subdirectories in addition to courses listed"
    print "  --org: auto-organize downloads into subdirectories titled with the course name"


if __name__ == '__main__': 
    if (len(sys.argv) < 2):
        print "Usage: ./scrape.py [Stanford ID] 'Interactive Computer Graphics' 'Programming Abstractions' ..."
    elif (sys.argv[1] == "help"):
        printHelpDocumentation()
    else:
        username = sys.argv[1]
        flags = [param for param in sys.argv[2:len(sys.argv)] if param.startswith('--')]
        courseNames = [param for param in sys.argv[2:len(sys.argv)] if not param.startswith('--')]
        shouldOrganize = False

        if (len(flags) != 0):
            if "--all" in flags:
                # Append names of subdirectories (excluding hidden folders and 'watched') to courseNames list
                courseNames += [name for name in os.listdir(".") if os.path.isdir(name) and not (name[0] is '.' or name is "watched")]
                flags.remove("--all")
            if "--org" in flags:
                print "org in!!"
                shouldOrganize = True
                flags.remove("--org")
            if not len(flags) is 0:
                print "following flags undefined and will be ignored: "
                print flags
        downloadAllCourses(username, courseNames)

