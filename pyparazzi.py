#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Author: Wil Alvarez (aka Satanas)
# Feb 28, 2011

import os
import re
import time
import Image
import urllib2
import datetime
import ConfigParser

# Don't touch this :P
CONFIG = {}
SERVICES = ['plixi.com', 'twitpic.com', 'instagr.am', 'moby.to', 'picplz.com']
TWITTER_URL = 'http://search.twitter.com/search.json'
STR_REQ = '%s?q=&ors=twitpic+moby+plixi+instagr.am+picplz&tag=%s&rpp=30'
URL_PATTERN = re.compile('((http://|ftp://|https://|www\.)[-\w._~:/?#\[\]@!$&\'()*+,;=]*)')
PLIXI_PATTERN = re.compile('<img (src=\".*?\") (alt=\".*?\") (id=\"photo\") />')
PLIXI2_PATTERN = re.compile('<img (src=\".*?\") (alt=\".*?\") (style=\".*?\") />')
TWITPIC_PATTERN = re.compile('<img (class=\"photo\") (id=\"photo-display\") (src=\".*?\") (alt=\".*?\") />')
MOBY_PATTERN = re.compile('<img (class=\"imageLinkBorder\") (src=\".*?\") (id=\"main_picture\") (alt=\".*?\") />')
INSTAGR_PATTERN = re.compile('<img (src=\".*?\") (class=\"photo\") />')
PICPLZ_PATTERN = re.compile('<img (src=\".*?\") (width=\".*?\") (height=\".*?\") (id=\"mainImage\") (class=\"main-img\") (alt=\".*?\") />')

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
        if url[-1] == ')':
            url = url[:-1]
        urls.append(url)
    return urls
    
def convert_time(str_datetime):
    ''' Take the date/time and convert it into Unix time'''
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
    if service == SERVICES[0]:
        code = PLIXI_PATTERN.findall(response)
        if len(code) <= 0:
            start = response.find('class="photo"><img src')
            end = response.find('>', start + 15) + 1
            piece = response[start:end]
            code = PLIXI2_PATTERN.findall(piece)
        
        if len(code) > 0:
            image_url = code[0][0][5:-1]
    elif service == SERVICES[1]:
        code = TWITPIC_PATTERN.findall(response)
        if len(code) > 0:
            image_url = code[0][2][5:-1]
            comment = code[0][3][5:-1]
    elif service == SERVICES[2]:
        code = INSTAGR_PATTERN.findall(response)
        if len(code) > 0:
            image_url = code[0][0][5:-1]
    elif service == SERVICES[3]:
        code = MOBY_PATTERN.findall(response)
        if len(code) > 0:
            image_url = code[0][1][5:-1]
            comment = code[0][3][5:-1]
    elif service == SERVICES[4]:
        code = PICPLZ_PATTERN.findall(response)
        if len(code) > 0:
            image_url = code[0][0][5:-1]
            comment = code[0][5][5:-1]
    return image_url, comment
    
def get_first_photo(text):
    for url in detect_urls(text):
        for srv in SERVICES:
            if url.find(srv) > 0:
                try:
                    return get_image_url(url, srv)
                except Exception, e:
                    print "Error:", e
                    return None, None
    return None, None

# This function remains unused until science finds a way to call it without making Wil cry
def remove_previous_thumbnails():
    folder = os.path.join(CONFIG['html_root'], CONFIG['thumbnail_folder_path'])

    for thumbnail_file in os.listdir(folder):
        file_path = os.path.join(folder, thumbnail_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception, e:
            print e

def generate_thumbnail(image_url):
    # Removes everything after a '?' symbol in the url if there is one (for local file name purposes)
    simple_image_url = image_url.split('?')[0]
      
    # Checks if thumbnail already exists (in which case there is no need to generate it again)
    outfilename = '.'.join(os.path.basename(simple_image_url).split('.')[:-1]) + '.png'
    outfilepath = os.path.join(CONFIG['html_root'], CONFIG['thumbnail_folder_path'], outfilename)
    thumbpath = os.path.join(CONFIG['thumbnail_folder_path'], outfilename)
    
    if os.path.isfile(outfilepath):
        return thumbpath
    
    print 'Processing image from %s' % image_url
    
    # Gets image from url
    opener1 = urllib2.build_opener()
    page1 = opener1.open(image_url)
    outfile = page1.read()
      
    # Saves image locally 
    fout = open(outfilepath, "wb")
    fout.write(outfile)
    fout.close()
    
    # Opens image
    im = Image.open(outfilepath)
    
    # Gets image size
    original_width, original_height = im.size
    
    # Calculates aspect ratios
    original_ratio = original_width / float(original_height)
    thumbnail_ratio = CONFIG['thumbnail_width'] / float(CONFIG['thumbnail_height'])
    
    # Calculates crop size and offset according to aspect ratios
    crop_needed = True

    if thumbnail_ratio > original_ratio:
        crop_width = original_width
        crop_height = int(original_width / thumbnail_ratio)
        crop_offset_x = 0
        crop_offset_y = (original_height - crop_height) / 2
    elif thumbnail_ratio < original_ratio:
        crop_width = int(original_height * thumbnail_ratio)
        crop_height = original_height
        crop_offset_x = (original_width - crop_width) / 2
        crop_offset_y = 0
    else:
        crop_needed = False
    
    # Crop (if needed)
    if crop_needed:
        cropbox = (crop_offset_x, crop_offset_y, crop_offset_x+crop_width, crop_offset_y+crop_height)
        im = im.crop(cropbox)
    
    # Resize
    im = im.resize((CONFIG['thumbnail_width'], CONFIG['thumbnail_height']))
        
    # Save
    im.save(outfilepath, "PNG")
    
    # Returns thumbnail url
    return thumbpath
    
def generate_image(user, timestamp, image_url, thumbnail_url, comment, first=False):
    _class = ' first' if first else ''
    comment = comment.decode('utf-8')
    try:
        return u'''<div class="image%s">
            <a href="%s" rel="lytebox[pyparazzi]" title="%s">
                <img src="%s" width="%s" height="%s" />
            </a>
            <div class="author">Por: <a href="http://twitter.com/%s">@%s</a></div>
            <div class="timestamp">%s</div>
        </div>''' % (_class, image_url, comment, thumbnail_url, 
                     CONFIG['thumbnail_width'], CONFIG['thumbnail_height'], 
                     user, user, timestamp)
    except Exception, e:
        print "Error generando imagen:", e
        return '''<div class="image">
                <img src="" width="%s" height="%s" />
            <div class="author">No se pudo cargar la imagen</div>
        </div>''' % (CONFIG['thumbnail_width'], CONFIG['thumbnail_height'])
    
def load_config():
    cfg = ConfigParser.ConfigParser()
    cfgdir = os.path.join(os.path.expanduser('~'), '.config', 'pyparazzi')
    cfgfile = os.path.join(cfgdir, 'config')
    
    # Making default config
    if not os.path.isdir(cfgdir) or not os.path.isfile(cfgfile): 
        return False
    
    global CONFIG
    # Reading config
    cfg.read(cfgfile)
    CONFIG['columns'] =  int(cfg.get('General', 'columns'))
    CONFIG['hashtag'] =  cfg.get('General', 'hashtag')
    CONFIG['title'] =  cfg.get('General', 'title')
    CONFIG['message'] =  cfg.get('General', 'message')
    CONFIG['html_root'] =  cfg.get('General', 'html_root')
    CONFIG['html_template'] =  cfg.get('General', 'html_template')
    CONFIG['html_output'] =  cfg.get('General', 'html_output')
    CONFIG['thumbnail_width'] =  int(cfg.get('General', 'thumbnail_width'))
    CONFIG['thumbnail_height'] =  int(cfg.get('General', 'thumbnail_height'))
    CONFIG['thumbnail_folder_path'] =  cfg.get('General', 'thumbnail_folder_path')
    return True
    
def main():
    if not load_config():
        print "Can't find config file. Please create it and try again"
        return
    urlreq = STR_REQ % (TWITTER_URL, CONFIG['hashtag'])
    print "Searching on Twitter %s" % urlreq
    handle = urllib2.urlopen(urlreq)
    rtn = handle.read()
    response = json.loads(rtn)
    
    count = 0
    content = ''
    for tweet in response['results']:
        user = tweet['from_user']
        timestamp = convert_time(tweet['created_at'])
        image_url, comment = get_first_photo(tweet['text'])
        if image_url:
            first = True if (count % CONFIG['columns'] == 0) else False
            content += generate_image(user, timestamp, image_url, generate_thumbnail(image_url), comment, first)
            count += 1
    
    fd = open(CONFIG['html_template'], 'r')
    temp = fd.read()
    fd.close()
    
    page = temp.replace('$title$', CONFIG['title'])
    page = page.replace('$message$', CONFIG['message'])
    page = page.replace('$content$', content)
    page = page.encode('utf-8')
    
    outfilepath = os.path.join(CONFIG['html_root'], CONFIG['html_output'])
    fd = open(outfilepath, 'w')
    fd.write(page)
    fd.close()

if __name__ == '__main__':
    main()
