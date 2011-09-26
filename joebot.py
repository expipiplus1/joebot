#!/usr/bin/env python3.2

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
import sys

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
                    
                        (?:
                            [a-zA-Z0-9\\-]+
                            \\.
                        )+
                        [a-zA-Z]+
                    )
                    (?::\\d{2,5})?
                    (?:/[^\\s]*)?
                )
            """
url_pattern = re.compile( url_regex, re.VERBOSE )

server = "no.server"

class JoeBot( ircutils.bot.SimpleBot ):
    def Init( self ):
        self.last_seen = {}

    def LastSeen( self, event ):
        try:
            if event.message[:9].lower() != "!lastseen":
                return
            if len( event.message ) < 10:
                self.send_message( event.target, "Please give a name" )
                return

            name = event.message[9:].strip().lower()
            if name not in self.last_seen:
                self.send_message( event.target, "I've never seen that nick" )
                return

            self.send_message( event.target, self.last_seen[name] )
        except:
            self.send_message( event.target, "Something is broken in JoeBot.LastSeen()" )

    def Say( self, event ):
        try:
            regex = r"\!say\s+(?P<target>[^\s]+)\s+(?P<message>.*)"
            pattern = re.compile( regex )
            match = pattern.match( event.message )
            if not match:
                return
            self.send_message( match.group( "target" ), match.group( "message" ) )
        except:
            self.send_message( event.target, "bleh" )
            raise

    def GetUrlTitle( self, url ):
        if url[0:4] != "http":
            url = "http://" + url
        request = None
        try:
            request = urllib.request.urlopen( url )
            #h = lxml.html.parse( url )
        except:
            print( "Can't load url: \"" + url + "\"" )
            return None
        data = request.read()
        h = lxml.html.fromstring( str( data ) )
        title = h.find( ".//title" )
        if title is None:
            return None
        title_string = bytes( title.text, "utf8" ).decode( "unicode_escape" )
        title_string = re.sub( "\n\\s*", " ", title_string, re.MULTILINE )
        title_string = title_string.strip()
        return title_string
        
    def PrintUrlNames( self, event ):
        try:
            string = event.message
            print("BEGIN")
            print( string )
            urls = url_pattern.findall( string )
            print( string )
            print("END")
            titles = []
            for url in urls:
                title_string = self.GetUrlTitle( url )
                if title_string is None:
                    print( "no title: " + url )
                    continue
                if title_string not in titles:
                    titles.append( title_string )
            for title in titles:
                self.send_message( event.target, title )
        except:
            self.send_message( event.target, "Bleh" )
            raise

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
            title_string = self.GetUrlTitle( result_url )
            if title_string:
                self.send_message( event.target, result_url + " " + title_string )
            else:
                self.send_message( event.target, result_url )
        except:
            self.send_message( event.target, "bLeh" )
            raise

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
                    self.send_message( event.target, "BLEh" )
                return
            else:
                if len( result_string ) > 512:
                    self.send_message( event.target, "A very big number" )
                else: 
                    string = result_string + " = " + expression_string
                    self.send_message( event.target, string )
        except:
            self.send_message( event.target, "BLeh" )

    def Log( self, event ):
        try:
            if not event.target:
                return

            log_string = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            log_string += " "

            log_string += event.command
            log_string += " "

            if not isinstance( event, ircutils.events.MessageEvent ):
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

            #
            # Update last_seen
            #
            self.last_seen[event.source.lower()] = log_string
        except:
            self.send_message( event.target, "blEh" )
            raise

    def on_channel_message( self, event ):
        try:
            self.ParseExpression( event )

            self.Ggl( event )

            self.LastSeen( event )

            self.PrintUrlNames( event )

            self.Say( event )

        except:
            self.send_message( event.target, "BlEh" )
            raise

    def on_any( self, event ):
        try:
            self.Log( event )
        except:
            self.send_message( event.target, "bLEh" )
            raise

def main():
    if len( sys.argv ) < 3:
        print( "Need a server and channel" )
        exit()
    server = sys.argv[1]
    channels = sys.argv[2:]
    joe_bot = JoeBot( "ZZ_Bot" )
    joe_bot.Init()
    joe_bot.connect( server, channel = channels )
    joe_bot.start()

if __name__ == "__main__":
    main()


