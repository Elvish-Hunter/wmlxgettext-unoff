import re
import pywmlx.state.machine
from pywmlx.state.state import State
import pywmlx.nodemanip
from pywmlx.wmlerr import wmlerr



class WmlIdleState:
    def __init__(self):
        self.regex = None
        self.iffail = None
    
    def run(self, xline, lineno, match):
        _nextstate = 'wml_checkdom'
        if pywmlx.state.machine._pending_wmlstring is not None:
            pywmlx.state.machine._pending_wmlstring.store()
            pywmlx.state.machine._pending_wmlstring = None
        m = re.match(r'\s*$', xline)
        if m:
            xline = None
            _nextstate = 'wml_idle'
        return (xline, _nextstate) # 'wml_define'



'''
class WmlDefineState:
    def __init__(self):
        self.regex = re.compile('\s*#(define|enddef|\s+wmlxgettext:\s+)', re.I)
        self.iffail = 'wml_checkdom'
    
    def run(self, xline, lineno, match):
        if match.group(1).lower() == 'define':
            # define
            xline = None
            if pywmlx.nodemanip.onDefineMacro is False:
                pywmlx.nodemanip.onDefineMacro = True
            else:
                err_message = ("expected an #enddef before opening ANOTHER " + 
                               "macro definition with #define")
                finfo = pywmlx.nodemanip.fileref + ":" + str(lineno)
                wmlerr(finfo, err_message)
        elif match.group(1).lower() == 'enddef':
            # enddef
            xline = None
            if pywmlx.nodemanip.onDefineMacro is True:
                pywmlx.nodemanip.onDefineMacro = False
            else:
                err_message = ("found an #enddef, but no macro definition " +
                               "is pending. Perhaps you forgot to put a " +
                               "#define somewhere?")
                finfo = pywmlx.nodemanip.fileref + ":" + str(lineno)
                wmlerr(finfo, err_message)
        else:
            # wmlxgettext: {WML CODE}
            xline = xline [ match.end(): ]
        return (xline, 'wml_idle')
'''



class WmlCheckdomState:
    def __init__(self):
        self.regex = re.compile(r'\s*#textdomain\s+(\S+)', re.I)
        self.iffail = 'wml_checkpo'
    
    def run(self, xline, lineno, match):
        pywmlx.state.machine._currentdomain = match.group(1)
        xline = None
        return (xline, 'wml_idle')



class WmlCheckpoState:
    def __init__(self):
        rx = r'\s*#\s+(wmlxgettext|po-override|po):\s+(.+)'
        self.regex = re.compile(rx, re.I)
        self.iffail = 'wml_comment'
    
    def run(self, xline, lineno, match):
        if match.group(1) == 'wmlxgettext':
            xline = match.group(2)
        # on  #po: addedinfo
        elif match.group(1) == "po":
            xline = None
            if pywmlx.state.machine._pending_addedinfo is None:
                pywmlx.state.machine._pending_addedinfo = [ match.group(2) ]
            else:
                pywmlx.state.machine._pending_addedinfo.append(match.group(2))
        # on -- #po-override: overrideinfo
        elif pywmlx.state.machine._pending_overrideinfo is None:
            pywmlx.state.machine._pending_overrideinfo = [ match.group(2) ]
            xline = None
        else:
            pywmlx.state.machine._pending_overrideinfo.append(match.group(2))
            xline = None
        return (xline, 'wml_idle')



class WmlCommentState:
    def __init__(self):
        self.regex = re.compile(r'\s*#.+')
        self.iffail = 'wml_tag'
    
    def run(self, xline, lineno, match):
        xline = None
        return (xline, 'wml_idle')



class WmlTagState:
    def __init__(self):
        self.regex = re.compile(r'\s*\[\s*([\/+-]?)\s*([^\]]*?)\s*\]')
        self.iffail = 'wml_getinf'
    
    def run(self, xline, lineno, match):
        # xdebug = open('./debug.txt', 'a')
        # xdebug_str = None
        if match.group(1) == '/':
            closetag = '[/' + match.group(2) + ']'
            pywmlx.nodemanip.closenode(closetag, 
                                       pywmlx.state.machine._dictionary,
                                       lineno)
            if closetag == '[/lua]':
                pywmlx.state.machine._pending_luafuncname = None
            # xdebug_str = closetag + ': ' + str(lineno)
        else:
            opentag = '[' + match.group(2) + ']'
            pywmlx.nodemanip.newnode(opentag)
            # xdebug_str = opentag + ': ' + str(lineno)
        # print(xdebug_str, file=xdebug)
        # xdebug.close()
        pywmlx.state.machine._pending_addedinfo = None
        pywmlx.state.machine._pending_overrideinfo = None
        xline = xline [ match.end(): ]
        return (xline, 'wml_idle')



class WmlGetinfState:
    def __init__(self):
        rx = ( r'\s*(speaker|id|role|description|condition|type|race)' +
               r'\s*=\s*(.*)' )
        self.regex = re.compile(rx, re.I)
        self.iffail = 'wml_str01'
    def run(self, xline, lineno, match):
        _nextstate = 'wml_idle'
        if '"' in match.group(2):
            _nextstate = 'wml_str01'
            pywmlx.state.machine._pending_winfotype = match.group(1)
        else:
            loc_wmlinfo = match.group(1) + '=' + match.group(2)
            xline = None
            pywmlx.nodemanip.addWmlInfo(loc_wmlinfo)
        return (xline, _nextstate)



class WmlStr01:
    def __init__(self):
        rx = r'(?:[^"]*?)\s*(_?)\s*"((?:""|[^"])*)("?)'
        self.regex = re.compile(rx)
        self.iffail = 'wml_golua'
    
    def run(self, xline, lineno, match):
        _nextstate = 'wml_idle'
        loc_translatable = True
        if match.group(1) == "":
            loc_translatable = False
        loc_multiline = False
        if match.group(3) == "":
            xline = None
            loc_multiline = True
            _nextstate = 'wml_str10'
        else:
            xline = xline [ match.end(): ]    
        pywmlx.state.machine._pending_wmlstring = (
            pywmlx.state.machine.PendingWmlString( 
                lineno, match.group(2), loc_multiline, loc_translatable
            )
        ) 
        return (xline, _nextstate)



# well... the regex will always be true on this state, so iffail will never
# be executed
class WmlStr10:
    def __init__(self):
        self.regex = re.compile(r'((?:""|[^"])*)("?)')
        self.iffail = 'wml_str10'
        
    def run(self, xline, lineno, match):
        _nextstate = None
        pywmlx.state.machine._pending_wmlstring.addline( match.group(1) )
        if match.group(2) == "":
            _nextstate = 'wml_str10'
            xline = None
        else:
            _nextstate = 'wml_idle'
            xline = xline [ match.end(): ]
        return (xline, _nextstate)



class WmlGoluaState:
    def __init__(self):
        self.regex = re.compile(r'.*?<<\s*')
        self.iffail = 'wml_final'
    
    def run(self, xline, lineno, match):
        xline = xline [ match.end(): ]
        return (xline, 'lua_idle')



class WmlFinalState:
    def __init__(self):
        self.regex = None
        self.iffail = None
    
    def run(self, xline, lineno, match):
        xline = None
        if pywmlx.state.machine._pending_wmlstring is not None:
            pywmlx.state.machine._pending_wmlstring.store()
            pywmlx.state.machine._pending_wmlstring = None
        return (xline, 'wml_idle')



def setup_wmlstates():
    for statename, stateclass in [ ('wml_idle', WmlIdleState),
                                   # ('wml_define', WmlDefineState),
                                   ('wml_checkdom', WmlCheckdomState),
                                   ('wml_checkpo', WmlCheckpoState),
                                   ('wml_comment', WmlCommentState),
                                   ('wml_tag', WmlTagState),                    
                                   ('wml_getinf', WmlGetinfState),
                                   ('wml_str01', WmlStr01),
                                   ('wml_str10', WmlStr10),
                                   ('wml_golua', WmlGoluaState),
                                   ('wml_final', WmlFinalState)]:
        st = stateclass()
        pywmlx.state.machine.addstate(statename, 
            State(st.regex, st.run, st.iffail) )

