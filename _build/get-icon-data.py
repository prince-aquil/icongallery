# Imports
# ------------------------------
import os
import json
import time
import urllib
import urllib2
import re
import collections
from BeautifulSoup import BeautifulSoup #for apple watch retrieval

# Function Definitions
# ------------------------------
def printData(data):
    print '\033[92m'
    print(json.dumps(data, indent=4))
    print '\033[0m'

def printError(text):
    print '\033[91m' + text + '\033[0m'

def createPost(app):
    global post

    # Required
    # All of the required values should be returned
    # by the iTunes API on a proper request
    # And they should be written in this order

    # [required] title, slug, date, category, itunes-url, app-developer
    post['title'] = app['trackName']
    slug = re.search('/app/(.*)/', app['trackViewUrl'])
    slug = slug.group(1)
    post['slug'] = slug
    post['date'] = time.strftime("%Y-%m-%d")
    post['category'] = app['primaryGenreId']
    post['itunes-url'] = re.sub(r'\?.*$', '', app['trackViewUrl']) # remove ? query string
    post['app-developer'] = app['artistName']

    # [optional] app-developer-url, icon-designer, icon-designer-url, tags
    if 'sellerUrl' in app:
        post['app-developer-url'] = app['sellerUrl']

    designer = raw_input('designer: ')
    if(designer != ''):
        designerUrl = raw_input('designer-url: ')
        post['icon-designer'] = designer
        post['icon-designer-url'] = designerUrl

    tags = raw_input('tags (space separated): ')
    if(tags != ''):
        post['tags'] = tags

def modifyPost():
    printData(post)
    key = raw_input('Changes? Enter the key (otherwise write files): ')
    if(key != ''):
        post[key] = raw_input('New value: ')
        # If it was the title changed, do so with the slug
        if(key == 'title'):
            post['slug'] = post[key].replace(' ', '-').lower()
        modifyPost()

def getItunesId():
    # Run this until we get what we want, then return and break out
    while True:
        url = raw_input('iTunes URL: ')
        url = url.strip()
        urlBeginsCorrectly = re.match('^(http|https):\/\/itunes.apple.com', url)
        urlHasId = re.search('\/id([\d]+)', url)
        if(urlBeginsCorrectly != None and urlHasId != None):
            return urlHasId.group(1)
            break
        else:
            printError('Invalid URL. Follow this pattern: https://itunes.apple.com/us/app/angry-birds/id343200656?mt=8')


def makeItunesRequest(appId):
    response = urllib2.urlopen('https://itunes.apple.com/lookup?id=' + appId)
    data = json.load(response)
    #validate response data
    if(data['results'][0]['artworkUrl512']):
        return data['results'][0]
    else:
        printError('The iTunes API response appears to be incorrect')

def writePost():
    # write .md file
    f = open(post['date'] + '-' + post['slug'] + '.md','w')
    f.write('---\n')
    for key in post:
        f.write(key + ': ' + str(post[key]) + '\n')
    f.write('---\n')
    f.close()
    # write image
    writeImage()

def writeImage():
    if(domain == 'ios'):
        # if it's a 1024 icon, the store provides it in the 512 prop
        urllib.urlretrieve(itunesResponse['artworkUrl512'], post['slug'] + '-' + time.strftime("%Y") + '.png')
    elif(domain == 'mac'):
        # for mac, try explicitly getting the 1024, if it fails, get the regular 512
        try:
            url1024 = re.sub('512x512', '1024x1024',itunesResponse['artworkUrl512'])
            urllib.urlretrieve(url1024, post['slug'] + '-' + time.strftime("%Y") + '.png')
        except URLError, e:
            urllib.urlretrieve(itunesResponse['artworkUrl512'], post['slug'] + '-' + time.strftime("%Y") + '.png')

    elif(domain == 'applewatch'):
        # Read from the object, storing the page's contents in 's'.
        f = urllib.urlopen(post['itunes-url'])
        html = f.read()
        f.close()
        # Parse the page's source for the things we want
        html = BeautifulSoup(html)
        #find the thumbnail by searching by icon size...there should only be one
        img = html.findAll(width="20")
        #get the first list item
        img = img[0]
        #get the image's src attribute and change the size to 300px
        src = img['src']
        src = src.replace('40x40', '300x300')
        ext = src.split('/')[-1]
        ext = ext.split('.')[-1]
        # get it (is likely a jpg, so you'll have to convert it)
        urllib.urlretrieve(src, post['slug'] + '-' + time.strftime("%Y") + "." + ext)
    else:
        printError('Looks like your domains are wrong for writing an image')

# Run
# ------------------------------

# Set the current domain (set by bash)
domain = os.environ['DOMAIN']

# Make an ordered dic
# http://pymotw.com/2/collections/ordereddict.html
post = collections.OrderedDict()

# Make iTunes Request, get data, and write it
itunesId = getItunesId()
itunesResponse = makeItunesRequest(itunesId)
createPost(itunesResponse)
modifyPost()
writePost()
