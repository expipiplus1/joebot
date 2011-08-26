#!/usr/bin/env python3

import time
#import ircutils
import ircutils.bot
import ircutils.events
import lxml.html
import urllib
import urllib.parse
import urllib.request
import json
import re

import expression_parser

#regex mainly sourced from here: https://gist.github.com/729294
url_regex = """
                \\b
                (
                    (?:https?://)?
                    (?:\\S+(?::\\S*)?@)?

                    (?:
                        (?!10(?:\\.\\d{1,3}){3})
                        (?!127(?:\\.\\d{1,3}){3})
                        (?!169\\.254(?:\\.\\d{1,3}){2})
                        (?!192\\.168(?:\\.\\d{1,3}){2})
                        (?!172\\.(?:1[6-9]|2\\d|3[0-1])(?:\\.\\d{1,3}){2})
                    
                        (?:[1-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])
                        (?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}
                        (?:\\.(?:[1-9]\\d?|1\\d\\d|2[0-4]\\d|25[0-4]))
                        |
                        (?:(?:[a-z\\u00a1-\\uffff0-9]+-?)*[a-z\\u00a1-\\uffff0-9]+)
                        (?:\\.(?:[a-z\\u00a1-\\uffff0-9]+-?)*[a-z\\u00a1-\\uffff0-9]+)*
                        (?:\\.(?:[a-z\\u00a1-\\uffff]{2,}))
                    )
                    (?::\\d{2,5})?
                    (?:/[^\\s]*)?
                )
            """
url_pattern = re.compile( url_regex, re.VERBOSE )

server = "irc.ox.ac.uk"

class JoeBot( ircutils.bot.SimpleBot ):
    def PrintUrlNames( self, event ):
        try:
            string = event.message
            urls = url_pattern.findall( string )
            for url in urls:
                if url[0:4] != "http":
                    url = "http://" + url
                h = None
                try:
                    h = lxml.html.parse( url )
                except:
                    print( "Can't load url: \"" + url + "\"" )
                    continue
                title = h.find( ".//title" ).text
                title = re.sub( "\n\\s*", " ", title, re.MULTILINE )
                title = title.strip()
                if "\n" in title:
                    print( "I ;m aftr" )
                self.send_message( event.target, title )
        except:
            self.send_message( event.target, "Something is broken in JoeBot.PrintUrlNames()" )

    def Ggl( self, event ):
        try:
            if event.message[:4] != "!ggl":
                return
            if len( event.message ) < 5:
                self.send_message( event.target, "I pity the fool who tries to crash me." )
            n = 0
            if event.message[4] in "0123456789":
                n = int( event.message[4] )
            query = urllib.parse.urlencode( {"q" : event.message[5:].strip() } )
            url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s" % query
            search_results = urllib.request.urlopen( url )
            j = json.loads( search_results.read().decode() )
            results = j["responseData"]["results"]
            if len( results ) == 0:
                self.send_message( event.target, "There were no results." )
                return
            if n >= len( results ):
                self.send_message( event.target, "Maximum of " + str( len( results ) ) + " results." )
                return
            result_url = results[n]["unescapedUrl"]
            self.send_message( event.target, result_url )
        except:
            self.send_message( event.target, "Something is broken in JoeBot.Ggl()!" )

    def DiceRoll( self, event ):
        pass
        #try:
            #dice_regex = "!
        #except:
            #self.send_message( event.target, "Something is broken in JoeBot.DiceRoll()!" )

    def ParseExpression( self, event ):
        try:
            expression_string = None
            if event.message[:2] != "!=":
                expression_string = event.message
            else:
                expression_string = event.message[2:]
            result_string = expression_parser.ParseExpression( expression_string ) 
            if result_string[0] == "*":
                if event.message[:2] == "!=":
                    self.send_message( event.target, result_string )
                return
            else:
                string = result_string + " = " + expression_string
                self.send_message( event.target, string )
        except:
            self.send_message( event.target, "Something is broken in JoeBot.ParseExpression()!" )

    def Log( self, event ):
        try:
            if not event.target:
                return

            log_string = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            log_string += " "

            log_string += event.command
            log_string += " "

            for param in event.params:
                log_string += "\""
                log_string += param
                log_string += "\" "
    
            log_string += "<"
            if event.source:
                log_string += event.source
            log_string += "> "

            if isinstance( event, ircutils.events.MessageEvent ):
                log_string += event.message

            log_string += "\n"
            log_filename = server + "-" + event.target + ".log"
            log_file = open( log_filename, "a" )
            log_file.write( log_string )
        except:
            self.send_message( event.target, "Something is broken in JoeBot.Log()!" )

    def on_channel_message( self, event ):
        try:
            self.PrintUrlNames( event )

            self.Ggl( event )

            self.ParseExpression( event )
        except:
            self.send_message( event.target, "Something is broken in JoeBot.on_channel_message()" )

    def on_any( self, event ):
        try:
            self.Log( event )
        except:
            self.send_message( event.target, "Something is broken in JoeBot.on_any()" )

def main():
    joe_bot = JoeBot( "joebot" )
    joe_bot.connect( server, channel = ["#bots","#freshers", "#wn"] )
    joe_bot.start()

if __name__ == "__main__":
    main()


