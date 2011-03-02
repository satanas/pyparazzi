# -*- coding: utf-8 -*-
#
# Author: Wil Alvarez (aka Satanas)
# Feb 28, 2011

import re
import time
import urllib2
import datetime
from urllib import urlencode

HASHTAG = 'oscars'
SERVICES = ['plixi.com', 'twitpic.com', 'mobypicture.com']

TWITTER_URL = 'http://search.twitter.com/search.json'
STR_REQ = '%s?q=&ors=twitpic+moby+plixi&tag=%s'
URL_PATTERN = re.compile('((http://|ftp://|https://|www\.)[-\w._~:/?#\[\]@!$&\'()*+,;=]*)')
PLIXI_PATTERN = re.compile('<img (src=\".*?\") (alt=\".*?\") (id=\"photo\")>')
PLIXI2_PATTERN = re.compile('<img (src=\".*?\") (alt=\".*?\") (style=\".*?\") />')
TWITPIC_PATTERN = re.compile('<img (class=\"photo\") (id=\"photo-display\") (src=\".*?\") (alt=\".*?\") />')
MOBY_PATTERN = re.compile('<img (class=\"imageLinkBorder\") (src=\".*?\") (id=\"main_picture\") (alt=\".*?\")>')

# TODO picplz e instagram
def _py26_or_greater():
    import sys
    return sys.hexversion > 0x20600f0
    
if _py26_or_greater():
    import json
else:
    import simplejson as json

def detect_urls(text):
    '''Returns an array with all URLs in a tweet'''
    urls = []
    match_urls = URL_PATTERN.findall(text)
    for item in match_urls:
        url = item[0]
        # Elimina el último paréntesis en las expresiones regulares
        if url[-1] == ')':
            url = url[:-1]
        urls.append(url)
    return urls
    
def convert_time(str_datetime):
    ''' Take the date/time and convert it into Unix time'''
    # Tue Mar 13 00:12:41 +0000 2007 -> Tweets normales
    # Wed, 08 Apr 2009 19:22:10 +0000 -> Busquedas
    month_names = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
        'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    date_info = str_datetime.split()
    
    if date_info[1] in month_names:
        month = month_names.index(date_info[1])
        day = int(date_info[2])
        year = int(date_info[5])
        time_info = date_info[3].split(':')
    else:
        month = month_names.index(date_info[2])
        day = int(date_info[1])
        year = int(date_info[3])
        time_info = date_info[4].split(':')
        
    hour = int(time_info[0])
    minute = int(time_info[1])
    second = int(time_info[2])
    
    d = datetime.datetime(year, month, day, hour, minute, second)
    
    i_hate_timezones = time.timezone
    if (time.daylight):
        i_hate_timezones = time.altzone
    
    dt = datetime.datetime(*d.timetuple()[:-3]) - \
         datetime.timedelta(seconds=i_hate_timezones)
    return time.strftime('%b %d, %I:%M %p', dt.timetuple())
    
def get_image_url(url, service):
    image_url = ''
    comment = ''
    handle = urllib2.urlopen(url)
    response = handle.read()
    fd = open('/tmp/response', 'w')
    fd.write(response)
    fd.close()
    if service == SERVICES[0]:
        #<img src="http://c0013659.cdn1.cloudfiles.rackspacecloud.com/x2_4c3c8a3" alt="" id="photo">
        #class="photo"><img src="http://c0013670.cdn1.cloudfiles.rackspacecloud.com/x2_4d4d8c0" alt="" style="max-width:295px" />
        code = PLIXI_PATTERN.findall(response)
        if len(code) <= 0:
            start = response.find('class="photo"><img src')
            end = response.find('>', start + 15) + 1
            piece = response[start:end]
            print piece
            code = PLIXI2_PATTERN.findall(piece)
        
        if len(code) > 0:
            image_url = code[0][0][5:-1]
        print len(code), image_url, comment
    elif service == SERVICES[1]:
        #<img class="photo" id="photo-display" src="http://s3.amazonaws.com/twitpic/photos/full/250705493.jpg?AWSAccessKeyId=0ZRYP5X5F6FSMBCCSE82&amp;Expires=1299078040&amp;Signature=pJAW8i8UkxYMOe%2FvET3kt6oQ8sk%3D" alt="This dude @djspinking just sent me this picture... lmaoooo! this has me rollin right now. shoutout to whoever made this! loll">
        code = TWITPIC_PATTERN.findall(response)
        if len(code) > 0:
            image_url = code[0][2][5:-1]
            comment = code[0][3][5:-1]
        print len(code), image_url, comment
    elif service == SERVICES[2]:
        #<img class="imageLinkBorder" src="http://img.mobypicture.com/723dd328b352fb48e1d10e364c59fb7f_view.jpg" id="main_picture" alt="ビックリカメラで目的以外のものを買ってしまった☻写真が横だ。">
        code = MOBY_PATTERN.findall(response)
        if len(code) > 0:
            image_url = code[0][1][5:-1]
            comment = code[0][3][5:-1]
        print len(code), image_url, comment
    return image_url, comment
    
def get_first_photo(text):
    for url in detect_urls(text):
        print 'Analyzing %s' % url
        for srv in SERVICES:
            if url.find(srv) > 0:
                try:
                    return get_image_url(url, srv)
                except Exception, e:
                    print e
                    return None, None
    
results = []
urlreq = STR_REQ % (TWITTER_URL, HASHTAG)
handle = urllib2.urlopen(urlreq)
rtn = handle.read()
response = json.loads(rtn)
for tweet in response['results']:
    user = tweet['from_user']
    timestamp = convert_time(tweet['created_at'])
    image_url, comment = get_first_photo(tweet['text'])
    print image_url
    if image_url:
        results.append({
            'user': user,
            'timestamp': timestamp,
            'image_url': image_url,
            'comment': comment
        })
    
print results

