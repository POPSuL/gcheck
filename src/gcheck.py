#!/usr/bin/python
#-*- coding:utf-8 -*-

import appindicator
import gtk
import urllib2
import base64
import time
from threading import Thread
import thread
from xml.etree import ElementTree
import webbrowser
import sys, os
from config import GCHECK_CONFIG

__GPATH__ = os.path.dirname(os.path.abspath(__file__))

class GChecker(Thread):
    def __init__(self, status):
        Thread.__init__(self)
        gtk.gdk.threads_init()
        self.status_inst = status
        self.menu = status.get_menu()
        self.indicator = status.get_indicator()
        #self.animation_queue = [
        #                        0, -5, -10, -15, -20, -25, -30,
        #                        -25, -20, -15, -10, -5, 0,
        #                        5, 10, 15, 20, 25, 30,
        #                        25, 20, 15, 10, 5, 0]
        self.animation_queue = [
                                0, -10, -20, -30,
                                -20, -10, 0,
                                10, 20, 30,
                                20, 10, 0]
    
    def get_page(self):
        theurl = 'https://mail.google.com/mail/feed/atom'
        req = urllib2.Request(theurl)
        base64string = base64.encodestring(
                                           '%s:%s' % (GCHECK_CONFIG['email'], GCHECK_CONFIG['password']))[:-1]
        authheader =  "Basic %s" % base64string
        req.add_header("Authorization", authheader)
        handle = urllib2.urlopen(req)
        thepage = handle.read()
        return thepage

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
    
    def animate_new(self):
        for i in self.animation_queue:
            print i
            self.indicator.set_icon(__GPATH__ + '/img/ani/%d.png' % i)
            time.sleep(0.1)
    
    def run(self):
        while True:
            try:
                page = self.get_page()
                messages = self.get_messages(page)
                for item in self.menu.children():
                    self.menu.remove(item)
                    del item
                for message in messages:
                    buf = '%s — %s' % (message['sender'] or message['email'], message['title']) 
                    item = gtk.MenuItem(buf)
                    item.set_data('href', message['link'])
                    item.connect('activate', self.on_select)
                    self.menu.append(item)
                    item.show()
                self.indicator.set_label('%d' % len(messages))
                if len(messages) == 0:
                    self.indicator.set_icon("indicator-messages")
                    self.status_inst.set_items_if_empty_mail()
                else:
                    self.animate_new()
                self.status_inst.set_default_items()
            except AttributeError as (ec, es):
                print es
            except:
                print sys.exc_info()
            time.sleep(15)
    def on_select(self, item):
        href = item.get_data('href')
        self.menu.remove(item)
        webbrowser.open(href)

class GStatus:
    def __init__(self):
        self.indicator = appindicator.Indicator( "gcheck-client",
                                                 "indicator-messages",
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
        
    def set_default_items(self):
        if self._inited != True:
            self.separator = gtk.SeparatorMenuItem()
            self.options = gtk.MenuItem(u'Настройки')
            self.options.connect('activate', self.on_settings)
            self.exit = gtk.MenuItem(u'Выход')
            self.exit.connect('activate', self.on_exit)
            self.separator.show()
            self.options.show()
            self.exit.show()
            self._inited = True
        self.menu.append(self.separator)
        self.menu.append(self.options)
        self.menu.append(self.exit)
        
    def set_items_if_empty_mail(self):
        self.menu.append(self.mail_empty)
    
    def get_menu(self):
        return self.menu
    
    def get_indicator(self):
        return self.indicator

    def on_empty_mail(self, item):
        webbrowser.open('https://mail.google.com/mail/#inbox')
        
    def on_settings(self, item):
        #options = gtk.glade.XML('options.glade')
        pass
        
        
    
    def on_exit(self, item):
        self.on_quit_handler()
        sys.exit(0)
    
    def set_on_quit_handler(self, hndl):
        self.on_quit_handler = hndl
    
    def main(self):
        gtk.main()
        

try:
    gstat = GStatus()
    checker = GChecker(gstat)
    checker.start()
    def on_quit_handler():
        checker._Thread__stop()
    gstat.set_on_quit_handler(on_quit_handler)
    gstat.main()
except:
    checker._Thread__stop()
