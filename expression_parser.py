#!/usr/bin/env python3 

from modgrammar import *
from modgrammar import Terminal, error_result, util, GrammarClass, ParseError
from modgrammar.extras import *
import re
import random
from sys import *
import signal

#grammar_whitespace = re.compile("\s+")

#
# formatting helper functions
#

def StripWhitespace( string ):
    ret = re.sub( "\s+", " ", string, flags = re.MULTILINE )
    return ret.strip()

def GotoNextTabstop( x ):
    tab_width = 4
    return ( ( x + tab_width - 1 ) // tab_width ) * tab_width

#
# Grammar classes
#

def BALANCED_TOKENS( opening_char, closing_char, **kwargs ):
    cdict = util.make_classdict( BalancedGrammar, (), kwargs, opening_char = opening_char, closing_char = closing_char )
    return GrammarClass( "<BalancedGrammar>", ( BalancedGrammar, ), cdict )

class BalancedGrammar (Terminal):
    grammar_desc = "Balanced Braces"
    opening_char = None
    closing_char = None

    @classmethod
    def grammar_parse(cls, text, index, sessiondata):
        i = index
        depth = 0
        string = text.string
        while i < len( string ):
            c = string[i]
            if c == cls.opening_char:
                depth += 1
            elif c == cls.closing_char:
                depth -= 1

            elif c == "\"":
                i += 1
                while i < len( string ):
                    if string[i] == "\"" and string[i-1] != "\\":
                        break
                    i += 1
            elif c == "'":
                i += 1
                while i < len( string ):
                    if string[i] == "'" and string[i-1] != "\\":
                        break
                    i += 1
            if depth < 0:
                yield( i - index, cls( string[index:i] ) )
                break
            i += 1
        yield error_result( index, cls )
                           
    @classmethod
    def grammar_ebnf_lhs(cls, opts):
      return (util.ebnf_specialseq(cls, opts), ())

    @classmethod
    def grammar_ebnf_rhs(cls, opts):
      return None

def BALANCED_UNTIL_TOKENS( ending_chars, use_templates = False, **kwargs ):
    bracket_pairs = [ ( "{", "}" ),
                      ( "(", ")" ),
                      ( "[", "]" ) ]

    independent_bracket_pair = ( "<", ">" ) if use_templates else ()
    
    cdict = util.make_classdict( BalancedUntilGrammar, (), kwargs, ending_chars = ending_chars, bracket_pairs = bracket_pairs, independent_bracket_pair = independent_bracket_pair )
    return GrammarClass( "<BalancedUntilGrammar>", ( BalancedUntilGrammar, ), cdict )

class BalancedUntilGrammar (Terminal):
    grammar_desc = "Balanced Until"
    ending_chars = None
    bracket_pairs = None
    independent_bracket_pair = None

    @classmethod
    def read_until(cls, string, index, stop_chars ):
        i = index
        while i < len( string ):
            c = string[i]
            if c in stop_chars:
                return i
            if c == "\"":
                i += 1
                while i < len( string ):
                    if string[i] == "\"" and string[i-1] != "\\":
                        break
                    i += 1
            elif c == "'":
                i += 1
                while i < len( string ):
                    if string[i] == "'" and string[i-1] != "\\":
                        break
                    i += 1
            i += 1
        return None

    @classmethod
    def grammar_parse(cls, text, index, sessiondata):
        i = index
        ind_depth = 0
        string = text.string
        while i < len( string ):
            c = string[i]
            if c in cls.ending_chars and ind_depth <= 0:
                yield( i - index, cls( string[index:i] ) )
                break
            if len( cls.independent_bracket_pair ) > 0:
                if c == cls.independent_bracket_pair[0]:
                    ind_depth += 1
                elif c == cls.independent_bracket_pair[1]:
                    ind_depth = max( 0, ind_depth - 1 )
            for bracket_pair in cls.bracket_pairs:
                if c == bracket_pair[0]:
                    depth = 1
                    while depth > 0:
                        i += 1
                        i = cls.read_until( string, i, ( bracket_pair[0], bracket_pair[1] ) )
                        if not i:
                            yield error_result( index, cls )
                        if string[i] == bracket_pair[0]:
                            depth += 1
                        else:
                            depth -= 1
                    break
            i += 1
        yield error_result( index, cls )
                           
    @classmethod
    def grammar_ebnf_lhs(cls, opts):
      return (util.ebnf_specialseq(cls, opts), ())

    @classmethod
    def grammar_ebnf_rhs(cls, opts):
      return None
 
#
# Functions
#

def PrintIndented( string, indentation ):
    for i in range( 0, indentation ):
        stdout.write( " " )
    for c in string:
        stdout.write( c )
        if c == "\n":
            for i in range( 0, indentation ):
                stdout.write( " " )
    stdout.write( "\n" )

def PrintElements( element, indentation = 0 ):
    PrintIndented( element.__repr__(), indentation )
    if not element:
        return
    #PrintIndented( "POSITION: " + str( element.start ) , indentation )
    for e in element.elements:
        PrintElements( e, indentation + 4 )

#
#
#

class DigitSequence( Grammar ):
    grammar = RE( "[0-9]+", grammar_desc = "Any digit" )

class FractionalConstant( Grammar ):
    grammar = OR( ( OPTIONAL( DigitSequence ), ".", DigitSequence ),
                  ( DigitSequence, "." ) )

class Sign( Grammar ):
    grammar = OR( "+",
                  "-" )

class ExponentPart( Grammar ):
    grammar = OR( "e",
                  "E" ), OPTIONAL( Sign ), DigitSequence

class FloatingSuffix( Grammar ):
    grammar = OR( "f",
                  "l",
                  "F",
                  "L" )

class FloatingLiteral( Grammar ):
    grammar = OR( G( FractionalConstant, OPTIONAL( ExponentPart ), OPTIONAL( FloatingSuffix ), collapse = True ),
                  G( DigitSequence, ExponentPart, OPTIONAL( FloatingSuffix ), collapse = True ) )

    def elem_init( self, k ):
        string = self[0].string
        if self[1]:
            string += self[1].string
        self.value = float( string )

class DecimalLiteral( Grammar ):
    grammar = RE( "[1-9][0-9]*", grammar_desc = "Decimal digit" )

    def elem_init( self, sessiondata ):
        self.value = int( self.string )

class OctalLiteral( Grammar ):
    grammar = RE( "0[0-7]*", grammar_desc = "Octal digit" )

    def elem_init( self, sessiondata ):
        self.value = int( self.string, base = 8 )

class HexadecimalLiteral( Grammar ):
    grammar = RE ( "0[xX][0-9a-fA-F]+", grammar_desc = "Hexadecimal number" )

    def elem_init( self, sessiondata ):
        self.value = int( self.string[2:], base = 16 )

class UnsignedSuffix( Grammar ):
    grammar = OR( "u",
                  "U" )

class LongSuffix( Grammar ):
    grammar = OR( "l",
                  "L" )

class LongLongSuffix( Grammar ):
    grammar = OR( "ll", #c++0x
                  "LL" ) #c++0x

class IntegerSuffix( Grammar ):
    grammar = OR( ( UnsignedSuffix, OPTIONAL( LongSuffix ) ),
                  ( UnsignedSuffix, OPTIONAL( LongLongSuffix ) ), #c++0x
                  ( LongSuffix, OPTIONAL( UnsignedSuffix ) ),
                  ( LongLongSuffix, OPTIONAL( UnsignedSuffix ) ) ) #c++0x

class IntegerLiteral( Grammar ):
    grammar = OR( ( DecimalLiteral, OPTIONAL( IntegerSuffix ) ),
                  ( OctalLiteral, OPTIONAL( IntegerSuffix ) ),
                  ( HexadecimalLiteral, OPTIONAL( IntegerSuffix ) ) )

    def elem_init( self, k ):
        self.value = self[0][0].value

class Number( Grammar ):
    grammar = OR( FloatingLiteral, IntegerLiteral )

    def elem_init( self, k ):
        self.value = self[0].value

class ParenthesesExpression( Grammar ):
    grammar = OR( Number,
                  G( L( "(", grammar_collapse_skip = False ), REF( "AdditionExpression" ), L( ")", grammar_collapse_skip = False ), collapse = True ) )

    def elem_init( self, k ):
        if len( self.elements ) == 1:
            self.value = self[0].value
        else:
            self.value = self[1].value

class FactorialError( BaseException ):
    def __init__( self, node ):
        self.node = node

def factorial( n ):
    acc = 1
    for i in range( 1, n+1 ):
        acc *= i
    return acc

class FactorialExpression( Grammar ):
    grammar = ParenthesesExpression, OPTIONAL( "!" )
                   
    def elem_init( self, k ):
        if self.elements[1]:
            n = self[0].value
            if n != int( n ):
                raise FactorialError( self )
            if n < 0:
                raise FactorialError( self )
            self.value = factorial( n )
        else:
            self.value = self[0].value

class DieError( BaseException ):
    def __init__( self, node ):
        self.node = node

class DieExpression( Grammar ):
    grammar = OR( FactorialExpression,
                  G( OPTIONAL( FactorialExpression ), OR( L( "d", grammar_collapse_skip = False ),
                                                            L( "D", grammar_collapse_skip = False ) ), FactorialExpression, collapse = True ) )

    def elem_init( self, k ):
        if len( self.elements ) == 1:
            self.value = self[0].value
        else:
            num_dice = 1
            if self[0]:
                num_dice = self[0].value
              
            num_sides = self[2].value

            if num_sides <= 0 or num_dice < 0 or num_sides != int( num_sides ) or num_dice != int( num_dice ):
                raise DieError( self )

            acc = 0
            for i in range( num_dice ):
                acc += random.randint( 1, num_sides )

            self.value = acc

class UnaryExpression( Grammar ):
    grammar = OR( G( Sign, REF( "UnaryExpression" ), collapse = True ),
                  DieExpression )

    def elem_init( self, k ):
        if len( self.elements ) == 1:
            self.value = self[0].value
        else:
            if self[0].string == "-":
                self.value = -self[1].value
            else:
                self.value = self[1].value

class ExponentiationExpression( Grammar ):
    grammar = OR( UnaryExpression,
                  G( UnaryExpression, OR( L( "**", grammar_collapse_skip = False ), 
                                          L( "^", grammar_collapse_skip = False ) ), REF( "ExponentiationExpression" ), collapse = True ) )
    
    def elem_init( self, k ):
        if len( self.elements ) == 1:
            self.value = self[0].value
        else:
            self.value = pow( self[0].value, self[2].value )

class MultiplicationExpression( Grammar ):
    grammar = OR( ExponentiationExpression,
                  G( ExponentiationExpression, OR( L( "*", grammar_collapse_skip = False ),
                                                   L( "/", grammar_collapse_skip = False ) ), REF( "MultiplicationExpression" ), collapse = True ) )

    def elem_init( self, k ):
        if len( self.elements ) == 1:
            self.value = self[0].value
        else:
            if self[1].string == "*":
                self.value = self[0].value * self[2].value
            else:
                self.value = self[0].value / self[2].value

class AdditionExpression( Grammar ):
    grammar = OR( MultiplicationExpression,
                  G( MultiplicationExpression, OR( L( "+", grammar_collapse_skip = False ),
                                                   L( "-", grammar_collapse_skip = False ) ), REF( "AdditionExpression" ), collapse = True ) )

    def elem_init( self, k ):
        if len( self.elements ) == 1:
            self.value = self[0].value
        else:
            if self[1].string == "+":
                self.value = self[0].value + self[2].value
            else:
                self.value = self[0].value - self[2].value

class Expression( Grammar ):
    grammar = AdditionExpression, EOF

    def elem_init( self, k ):
        self.value = self[0].value

class TimeError( BaseException ):
    def __init__( self ):
        pass

def handler( signum, frame ):
    print( "Timeout" )
    raise TimeError()

#signal.signal( signal.SIGALRM, handler )

def ParseExpression( string ):
    parser = Expression.parser()
    try:
        result = parser.parse_string( string, reset = True, eof = True )
    except ParseError as e:
        error_string = "*** Parse error at column "
        error_string += str( e.col ) 
        error_string += " *** "
        error_string += e.message
        return error_string
    except DieError as e:
        error_string = "*** You have tried to construct an impossible die *** "
        error_string += e.node.string
        return error_string
    except FactorialError as e:
        error_string = "*** You have tried to evaluate an impossible factorial *** "
        error_string += e.node.string
        return error_string
    return str( result.value )

def main():
    parser = Expression.parser()
    string = "1.5!"
    try:
        result = parser.parse_string( string, reset = True, eof = True )
    except ParseError as e:
        error_string = "*** Parse error at column "
        error_string += str( e.col ) 
        error_string += " *** "
        error_string += e.message
        print( error_string )
        exit()
    except DieError as e:
        error_string = "*** You have tried to construct an impossible die *** "
        error_string += e.node.string
        print( error_string )
        exit()
    except FactorialError as e:
        error_string = "*** You have tried to evaluate an impossible factorial *** "
        error_string += e.node.string
        print( error_string )
        exit()
    PrintElements( result )
    print( result.value )
    exit()

if __name__ == "__main__":
    main()

