#!/usr/bin/python
#-*- coding:utf-8 -*-

import urllib2
import base64
import time
from threading import Thread
from xml.etree import ElementTree
import webbrowser
import sys, os
import appindicator
import gtk
import requests

try:
    import pynotify
    USE_NOTIFY = True
    pynotify.init('Gchecker')
except ImportError:
    USE_NOTIFY = False
try:
    from config import GCHECK_CONFIG
except ImportError:
    print '''
    Не удалось подключить конфигурацию!
    Скопируйте example_config.py в config.py, отредактируйте,
    и попробуйте снова
    '''
    sys.exit(1)

__GPATH__ = os.path.dirname(os.path.abspath(__file__))

ICONS = {
         'about.me': 'aboutdotme-48x48.png',
         'aim.com': 'aim-48x48.png',
         'amazon.com': 'amazon-48x48.png',
         'bebo.com': 'bebo-48x48.png',
         'creativecommons.org': 'creativecommons-48x48.png',
         'delicious.com': 'delicious-48x48.png',
         'digg.com': 'digg-48x48.png',
         'diggthis.net': 'digg-this-48x48.png',
         'dopplr.com': 'dopplr-48x48.png',
         'dribbble.com': 'dribbble-48x48.png',
         'ebay.com': 'ebay-48x48.png',
         'facebook.com': 'facebook-48x48.png',
         'facebookmail.com': 'facebook-48x48.png',
         'ffffound.com': 'ffffound-48x48.png',
         'flickr.com': 'flickr-48x48.png',
         'formspring.me': 'formspring-48x48.png',
         'forrst.com': 'forrst-48x48.png',
         'foursquare.com': 'foursquare-48x48.png',
         'geotag.com': 'geotag-48x48.png',
         'getstatisfaction.com': 'getstatisfaction-48x48.png',
         'github.org': 'github-48x48.png',
         'goodreads.com': 'goodreads-48x48.png',
         'plus.google.com': 'google+-48x48.png',
         'google.com': 'google-48x48.png',
         'googlegroups.com': 'googlegroups-42x42.png',
         'gowalla.com': 'gowalla-48x48.png',
         'huffduffer.com': 'huffduffer-48x48.png',
         'identi.ca': 'identica-48x48.png',
         'ilike.com': 'ilike-48x48.png',
         'imdb.com': 'imdb-48x48.png',
         'lanyrd.com': 'lanyrd-48x48.png',
         'last.fm': 'lastfm-48x48.png',
         'linkedin.com': 'linkedin-48x48.png',
         'meetup.com': 'meetup-48x48.png',
         'mixx.com': 'mixx-48x48.png',
         'myspace.com': 'myspace-48x48.png',
         'netvibes.com': 'netvibes-48x48.png',
         'newsvine.com': 'newsvine-48x48.png',
         'orkut.com': 'orkut-48x48.png',
         'paypal.com': 'paypal-48x48.png',
         'picasa.com': 'picasa-48x48.png',
         'pinboard.in': 'pinboard-48x48.png',
         'plancast.com': 'plancast-48x48.png',
         'posterous.com': 'posterous-48x48.png',
         'rdio.com': 'rdio-48x48.png',
         'redernaut.com': 'redernaut-48x48.png',
         'reddit.com': 'reddit-48x48.png',
         'sharethis.com': 'share-48x48.png',
         'skype.com': 'skype-48x48.png',
         'slideshare.net': 'slideshare-48x48.png',
         'speakerdeck.com': 'speakerdeck-48x48.png',
         'spotify.com': 'spotify-48x48.png',
         'stumbleupon.com': 'stumbleupon-48x48.png',
         'tumblr.com': 'tumblr-48x48.png',
         'twitter.com': 'twitter-48x48.png',
         'viddler.com': 'viddler-48x48.png',
         'vimeo.com': 'vimeo-48x48.png',
         'wikipedia.org': 'wikipedia-48x48.png',
         'xbox.com': 'xbox-48x48.png',
         'xing.com': 'xing-48x48.png',
         'yahoo.com': 'yahoo-48x48.png',
         'yelp.com': 'yelp-48x48.png',
         'youtube.com': 'youtube-48x48.png',
         'zootool.com': 'zootool-48x48.png'}

class GChecker(Thread):
    def __init__(self):
        Thread.__init__(self)
        gtk.gdk.threads_init()
        
        self.indicator = appindicator.Indicator( "gcheck-client",
                __GPATH__ + "/img/indicator-messages.png",
                appindicator.CATEGORY_APPLICATION_STATUS)
        self.indicator.set_status(appindicator.STATUS_ACTIVE)
        self.menu = gtk.Menu()
        self.indicator.set_menu(self.menu)
        self.indicator.set_label('0')
        self._inited = False
        
        self.mail_empty = gtk.MenuItem(u'Почта пуста')
        self.mail_empty.show()
        self.mail_empty.connect('activate', self.on_empty_mail)
        self.set_items_if_empty_mail()
        
        self.set_default_items()
        
        
        #self.animation_queue = [
        #                        0, -5, -10, -15, -20, -25, -30,
        #                        -25, -20, -15, -10, -5, 0,
        #                        5, 10, 15, 20, 25, 30,
        #                        25, 20, 15, 10, 5, 0]
        self.animation_queue = [
                                0, -5, -10,
                                -5, 0,
                                5, 10,
                                5, 0]
        self.old_messages = []
    
    def get_page(self):
        url = 'https://mail.google.com/mail/feed/atom'
        
        req = requests.get(url, auth=(GCHECK_CONFIG['email'],
                                     GCHECK_CONFIG['password']))
        return req.content
        #req = urllib2.Request(theurl)
        #base64string = base64.encodestring(
        #                    '%s:%s' % (GCHECK_CONFIG['email'],
        #                               GCHECK_CONFIG['password']))[:-1]
        #authheader =  "Basic %s" % base64string
        #req.add_header("Authorization", authheader)
        #handle = urllib2.urlopen(req)
        #thepage = handle.read()
        #return thepage

    def get_messages(self, page):
        page = page.replace('http://purl.org/atom/ns#', '')
        o = ElementTree.fromstring(page)
        messages = []
        for e in o.findall('entry'):
            title = e.find('title').text
            email = e.find('author/email').text
            sender = e.find('author/name').text
            link = e.find('link').attrib['href']
            messages.append({
                             'title': title,
                             'email': email,
                             'link': link,
                             'sender': sender})
        return messages
    
    def get_email_icon(self, email):
        for site in ICONS:
            if email.endswith(site):
                return '/socialmediaicons/' + ICONS[site]
        return 'indicator-messages-new.png'
    
    def animate_new(self):
        for i in self.animation_queue + self.animation_queue[1:]:
            self.indicator.set_icon(__GPATH__ + '/img/ani/%d.png' % i)
            time.sleep(0.1)
    
    def get_list_difference(self, a, b):
        diff = []
        for item in b:
            try:
                idx = a.index(item)
            except ValueError:
                diff.append(item)
        return diff
    
    def notify_messages_diff(self, messages):
        if USE_NOTIFY:
            difference = self.get_list_difference(self.old_messages,
                                                  messages)
            for i in difference:
                icon = self.get_email_icon(i['email'])
                notify = pynotify.Notification(i['sender'] or i['email'],
                                    i['title'],
                                    __GPATH__ + '/img/' + icon)
                notify.show()
            self.old_messages = messages
            
    def run(self):
        while True:
            try:
                page = self.get_page()
                messages = self.get_messages(page)
                for item in self.menu.children():
                    self.menu.remove(item)
                    del item
                for message in messages:
                    buf = '%s — %s' % (message['sender'] or message['email'],
                                       message['title']) 
                    item = gtk.MenuItem(buf)
                    item.set_data('href', message['link'])
                    item.connect('activate', self.on_select)
                    self.menu.append(item)
                    item.show()
                self.indicator.set_label('%d' % len(messages))
                if len(messages) == 0:
                    self.indicator.set_icon(
                                    __GPATH__ + "/img/indicator-messages.png")
                    self.set_items_if_empty_mail()
                else:
                    self.notify_messages_diff(messages)
                    self.animate_new()
                self.set_default_items()
            #except AttributeError as (ec, es):
            #    print es
            except:
                print sys.exc_info()
            time.sleep(15)
            
    def set_default_items(self):
        if self._inited != True:
            self.separator = gtk.SeparatorMenuItem()
        #    self.options = gtk.MenuItem(u'Настройки')
        #    self.options.connect('activate', self.on_settings)
            self.exit = gtk.MenuItem(u'Выход')
            self.exit.connect('activate', self.on_exit)
            self.separator.show()
        #    self.options.show()
            self.exit.show()
            self._inited = True
        self.menu.append(self.separator)
        #self.menu.append(self.options)
        self.menu.append(self.exit)
        
    def on_select(self, item):
        href = item.get_data('href')
        webbrowser.open(href)
        
    def set_items_if_empty_mail(self):
        self.menu.append(self.mail_empty)

    def on_empty_mail(self, item):
        webbrowser.open('https://mail.google.com/mail/#inbox')
        
    def on_settings(self, item):
        #options = gtk.glade.XML('options.glade')
        pass
        
    def on_exit(self, item):
        self._Thread__stop()
        sys.exit(0)

        
if __name__ == '__main__':
    try:
        checker = GChecker()
        checker.start()
        gtk.main()
    except:
        checker._Thread__stop()
