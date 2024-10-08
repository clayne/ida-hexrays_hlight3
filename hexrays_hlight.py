# highlighting plugin for Hex-Rays Decompiler
# Copyright (c) 2016
# Milan Bohacek <milan.bohacek+hexlight@gmail.com>
# All rights reserved.
# 
# ==============================================================================
# 
# This file is part of Hexlight.
# 
# Hexlight is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
# ==============================================================================
 
 
import idautils
import idaapi
import idc
 
 
import traceback
 
hexlight_cb_info = None
hexlight_cb = None
 
posledni = 0
 
def jump(custom_viewer, line):
    (pl, x, y) = idaapi.get_custom_viewer_place(custom_viewer, False)
    pl2 = idaapi.place_t_as_simpleline_place_t(pl.clone())
    oldline = pl2.n
    pl2.n = line
    idaapi.jumpto(custom_viewer, pl2, x, y)
    return oldline
 
class hexrays_callback_info(object):
     
    def __init__(self):
        self.vu = None
        self.highlights = {}
        self.highl_brack = {}
        self.hicolor = 0x646464       #0xF2E8BF #0x00ffff00
        self.theotherline = None
        self.safe = False
        return
     
    def clearall(self, ps, refresh=True):
        ctr = 0
        for i in self.highlights:
            try:            
                ps[i].bgcolor = self.highlights[i]
                ctr += 1
            except:
                pass
#               place_t_as_simpleline_place_t
#              ps[i].line.replace("\x04{\x04", "{")
#              ps[i].line.replace("\x04}\x04", "}")
                 
        self.highlights = {}
        self.theotherline = None
        if((ctr > 0) and refresh):
            idaapi.refresh_idaview_anyway()
 
    def clearbracket(self, ps, refresh=True):
        ctr = 0
        for i in self.highl_brack:
            try:            
                ps[i].line = self.highl_brack[i]
                ctr += 1
                #print('clear' + ps[i].line)
            except:
                pass
             
        self.highl_brack = {}
        if((ctr > 0) and refresh):
            idaapi.refresh_idaview_anyway()     
             
    def highlight_bracket2(self, ps, pos_brach, xpos, ypos):
        ln = ps[ypos].line[:]
        # print("ypos",ypos)
        # print("highl_brack",self.highl_brack)
        if (ypos not in self.highl_brack):
            self.clearbracket(ps, True)
            self.highl_brack[ypos] = ln
        else:
            ln = self.highl_brack[ypos]
 
        s1pos = idaapi.tag_advance(ln, pos_brach)
        s2pos = idaapi.tag_advance(ln, xpos)
        line = list(ln)
        while (line[s1pos] != idaapi.SCOLOR_ON or line[s1pos+1] != idaapi.SCOLOR_SYMBOL):
            s1pos += 1
            if (s1pos > len(line)):
                return
        while (line[s2pos] != idaapi.SCOLOR_ON or line[s2pos+1] != idaapi.SCOLOR_SYMBOL):
            s2pos += 1
            if (s2pos > len(line)):
                return
 
        line[s1pos+1] = idaapi.SCOLOR_ERROR
        line[s1pos+4] = idaapi.SCOLOR_ERROR
        line[s2pos+1] = idaapi.SCOLOR_ERROR
        line[s2pos+4] = idaapi.SCOLOR_ERROR
        ps[ypos].line = ''.join(line)        
        idaapi.refresh_idaview_anyway()  
     
    def rfind_match_brack(self, start, strline, brack1, brack2):
        i = 0
        while (start >= 0) :
            if (strline[start] == brack1):
                i = i + 1
            elif (strline[start] == brack2):
                i = i - 1
            if (i == 0) :
                #find match
                return start 
            start = start - 1
             
        return -1    
         
    def find_match_brack(self, start, strline, brack1, brack2):
        i = 0
        while (start < len(strline)) :
            if (strline[start] == brack1):
                i = i + 1
            elif (strline[start] == brack2):
                i = i - 1
            if (i == 0) :
                #find match
                return start 
            start = start + 1
             
        return -1                   
 
    def event_callback(self, event, *args):
        try:
            # print("event: %d"%event)
            if event == idaapi.hxe_keyboard:
                vu, keycode, shift = args
 
                if idaapi.lookup_key_code(keycode, shift, True) == idaapi.get_key_code("B") and shift == 0:
                    if self.theotherline:
                        self.theotherline = jump(vu.ct, self.theotherline)
                    return 0
 
            # print("查看event")
            if event <= idaapi.hxe_print_func:
                self.safe = False
 
            if event == idaapi.hxe_switch_pseudocode:
                self.safe = False
 
            if event == idaapi.hxe_func_printed:
                self.safe = True
 
            if event == idaapi.hxe_text_ready:
                self.safe = True
 
            if event == idaapi.hxe_curpos:
                if not self.safe:
                    return 0
                #print "1"
                self.vu = args[0]
 
                if not self.vu:
                    return 0
                #print "2"
 
                if self.vu.cfunc.maturity != idaapi.CMAT_FINAL:
                    return 0
                #print "3"
 
                if not self.vu.visible():
                    return 0
                #print "4"
                if not self.vu.refresh_cpos(idaapi.USE_KEYBOARD):
                 #   print "refresh_cpos failed"
                    return 0
                pos = self.vu.cpos
                ypos = pos.lnnum
                xpos = pos.x
                # print("ypos,xpos",ypos,xpos)
                #print "cursor click %d %d %d" % (pos.x, pos.y, pos.lnnum)
 
                
                if ypos in self.highlights:
                    return  0
                #print "5"
 
                ps = self.vu.cfunc.get_pseudocode()
                #print "6"
                #print "ypos:%d"%ypos
                #print "ps[ypos].line: %s"%(ps[ypos].line)
 
                #line = [idaapi.COLSTR("[%02d]"%i, chr(i)) for i in
                #range(1,0x40) ]
                #ps[0].line = ''.join(line);
                #ps[1].line = '\x04'.join(line);
                #line = [idaapi.COLSTR( idaapi.COLSTR("[ \x04%02d\x04 ]"%i,
                #chr(i)), chr(i+1)) for i in range(1,0x40) ]
                #ps[2].line = ''.join(line);
                #ps[3].line = '\x04'.join(line);
                ln = ps[ypos].line[:]
                curline = idaapi.tag_remove(ln)
                #print "7"
 
                #print curline
                 
                if (xpos > 1 and xpos <= len(curline)):
                    chPrev = curline[xpos - 1]
                    # print("chPrev",chPrev)
                     
                    if (chPrev == ')'):
                        pos_brach = self.rfind_match_brack(xpos - 1, curline, ')', '(')
                        if (pos_brach != -1) :
                            self.highlight_bracket2(ps, pos_brach, xpos-1, ypos)
                    elif (chPrev == '('):
                        pos_brach = self.find_match_brack(xpos - 1, curline, '(', ')')
                        if (pos_brach != -1) :
                            self.highlight_bracket2(ps, pos_brach, xpos-1, ypos)
                    elif (chPrev == ']'):
                        pos_brach = self.rfind_match_brack(xpos - 1, curline, ']', '[')
                        if (pos_brach != -1) :
                            self.highlight_bracket2(ps, pos_brach, xpos-1, ypos)
                    elif (chPrev == '['):
                        pos_brach = self.find_match_brack(xpos - 1, curline, '[', ']')
                        if (pos_brach != -1) :
                            self.highlight_bracket2(ps, pos_brach, xpos-1, ypos)
                    else:
                        self.clearbracket(ps, True)
                else:
                    self.clearbracket(ps, True)
                        
                idxO = curline.find('{')
                idxC = curline.find('}')
                #print "O:", idxO, " C: ",idxC
                #there is no need to highlight first and last {
                #print "8"
 
                if (idxO >= 0) or (idxC >= 0):
                #   print "9"
                    self.clearall(ps, False)
 
                    self.highlights[ypos] = ps[ypos].bgcolor
 
                    ps[ypos].bgcolor = self.hicolor
                     
                    dir = 1
                    bracechar = '}'
                    idx = idxO
 
                    if (idxC >= 0):
                        dir = -1
                        bracechar = '{'
                        idx = idxC
 
                    j = ypos + dir
 
                    max = len(ps)
                 #   print "max: ",max
 
                    while (j >= 0) and (j < max):
                #       print "10"
                        #print "j:", j
                        ln = idaapi.tag_remove(ps[j].line)
                        if ln.find(bracechar) == idx:
                            if not(j in self.highlights):
                                self.highlights[j] = ps[j].bgcolor
                            #ps[j].line = ps[j].line.replace(bracechar,
                            #idaapi.COLSTR("\x04"+bracechar+"\x04", "\x27"))
                            #ps[j].line = ps[j].line.replace(bracechar,
                            #idaapi.COLSTR(bracechar, chr(52)))
                            ps[j].bgcolor = self.hicolor
                            self.theotherline = j
                            break
                        j+=dir
                     
                    idaapi.refresh_idaview_anyway()
                else:
                    self.clearall(ps)
                #print "11"
                return 0
        except:
            traceback.print_exc()
         
        return 0
 
def remove():
    if hexlight_cb:
        idaapi.remove_hexrays_callback(hexlight_cb)
 
class HexHLightPlugin_t(idaapi.plugin_t):
    flags = idaapi.PLUGIN_HIDE
    comment = "highlights the matching brace in Pseudocode-View"
    help = "press B to jump to the matching brace"
    wanted_name = "HexLight"
    wanted_hotkey = ""
 
    def init(self):
        # Some initialization
        global hexlight_cb_info, hexlight_cb
 
        if idaapi.init_hexrays_plugin():
            hexlight_cb_info = hexrays_callback_info()
            hexlight_cb = hexlight_cb_info.event_callback
            if not idaapi.install_hexrays_callback(hexlight_cb):
            #    print "could not install hexrays_callback"
                return idaapi.PLUGIN_SKIP
            print("Hexlight plugin installed Mod by Snow;modify by p1ay8y3ar")
            addon = idaapi.addon_info_t()
            addon.id = "milan.bohacek.hexlight"
            addon.name = "Hexlight"
            addon.producer = "p1ay8y3ar"
            addon.url = "https://github.com/p1ay8y3ar"
            addon.version = "7.6"
            idaapi.register_addon(addon)
            return idaapi.PLUGIN_KEEP
        #print "init_hexrays_plugin failed"
        return idaapi.PLUGIN_SKIP
 
    def run(self, arg=0):
        return
 
    def term(self):
        remove()
 
def PLUGIN_ENTRY():
    return HexHLightPlugin_t()
