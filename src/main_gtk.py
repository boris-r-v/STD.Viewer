import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango, GLib

import gtk
import threading
import socket
import struct
import sys
import time

class SearchDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(
            self, title="Search", transient_for=parent, modal=True,
        )
        self.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_FIND,
            Gtk.ResponseType.OK,
        )

        box = self.get_content_area()

        label = Gtk.Label(label="Insert text you want to search for:")
        box.add(label)

        self.entry = Gtk.Entry()
        box.add(self.entry)

        self.show_all()

class NetworkDialog(Gtk.Dialog):
    def __init__(self, parent, group, port ):
        Gtk.Dialog.__init__(
            self, title="Search", transient_for=parent, modal=True,
        )
        self.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )

        box = self.get_content_area()

        label = Gtk.Label(label="Set Multicast group:")
        box.add(label)

        self.group = Gtk.Entry( )
        self.group.set_text( group )
        box.add( self.group )

        label = Gtk.Label(label="Set UDP port:")
        box.add(label)
        
        self.port = Gtk.SpinButton(adjustment = Gtk.Adjustment(1024, 1024, 99999, 1, 0, 0), climb_rate=1, digits=0 )
        self.port.set_value ( port )
        box.add( self.port )

        self.show_all()

class Reciever( ):
    def __init__(self, textview):
        self.text = textview
        self.mcast_grp = '224.1.1.1'
        self.mcast_port = 20050

    def socket_create ( self ):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.mcast_grp, self.mcast_port))
        mreq = struct.pack("=4sl", socket.inet_aton(self.mcast_grp), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.settimeout(0.5)
        self.listen = True

        self.text.append_text( "\nListen: " + self.mcast_grp + ":" + str(self.mcast_port)+"\n" )
        threading.Thread( target = self.threading_func ).start()

    def socket_close( self ):
        self.listen = False

    def threading_func( self ):
        while ( self.listen ):
            try:
                s = self.sock.recv( 1000 ).decode("utf-8")
                self.text.append_text( s )
                print (s)
            except socket.timeout:
                continue

            except:
                self.text.append_text( "\nInternal error: " + str(sys.exc_info()[0]) +"\n" )
                break
        self.sock.close()
        self.text.append_text( "\nStop listen: " + self.mcast_grp + ":" + str(self.mcast_port)+"\n" )


class TextViewWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=u"Приемник логов STD/KSA")
        self.set_default_size(900, 350)
        self.grid = Gtk.Grid()
        self.add(self.grid)
        self.create_textview()
        self.create_toolbar()
        self.receiver = Reciever( self )

    def create_toolbar(self):
        toolbar = Gtk.Toolbar()
        self.grid.attach(toolbar, 0, 0, 3, 1)

        button_search = Gtk.ToolButton()
        button_search.set_icon_name("system-search-symbolic")
        button_search.connect("clicked", self.on_search_clicked)
        button_search.set_tooltip_text("Поиск в логе")
        toolbar.insert(button_search, 0)

        toolbar.insert(Gtk.SeparatorToolItem(), 1)

        button_clear = Gtk.ToolButton()
        button_clear.set_icon_name("edit-clear-symbolic")
        button_clear.connect("clicked", self.on_clear_clicked)
        button_clear.set_tooltip_text("Очистить")
        toolbar.insert(button_clear, 2)

        toolbar.insert(Gtk.SeparatorToolItem(), 3 )

        self.button_nc = Gtk.ToolButton()
        self.button_nc.set_icon_name("network-wired-symbolic")
        self.button_nc.connect("clicked", self.on_network_clicked)
        self.button_nc.set_tooltip_text("Настроить сеть")
        toolbar.insert(self.button_nc, 4)

        toolbar.insert(Gtk.SeparatorToolItem(), 5 )

        button_rec = Gtk.ToggleToolButton()
        button_rec.set_icon_name("media-record-symbolic")
        button_rec.connect("clicked", self.on_recieve_clicked)
        button_rec.set_tooltip_text("Вкл/Откл сбор логов")
        toolbar.insert(button_rec, 6)

        toolbar.insert(Gtk.SeparatorToolItem(), 7 )

        button_save = Gtk.ToggleToolButton()
        button_save.set_icon_name("document-save-symbolic")
        button_save.connect("clicked", self.on_save_clicked)
        button_save.set_tooltip_text("Сохранить логи в файл")
        toolbar.insert(button_save, 8)

    def append_text(self, text ):
        self.textbuffer.insert_at_cursor( text )

    def create_textview(self):
        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_hexpand(True)
        self.scrolledwindow.set_vexpand(True)
        self.grid.attach(self.scrolledwindow, 0, 1, 3, 1)
        self.textview = Gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        self.scrolledwindow.add(self.textview)
        self.textview.connect("size-allocate", self.autoscroll)
        self.textview.set_property("editable", False)
        self.textview.set_property("cursor-visible", False)

        self.tag_found = self.textbuffer.create_tag("found", background="yellow")

    def autoscroll(self, *args):
        adj = self.scrolledwindow.get_vadjustment()
        adj.set_value( adj.get_upper() - adj.get_page_size() )

    def on_save_clicked( self, widget ):
        dialog = Gtk.FileChooserDialog( title="Сохранить", parent=self, action=Gtk.FileChooserAction.SAVE )
        dialog.add_buttons(Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT)
        flter = Gtk.FileFilter()
        flter.set_name("txt files")
        flter.add_pattern("*.txt")
        dialog.add_filter(flter)

        response = dialog.run()
        filepath = dialog.get_filename()
        dialog.destroy()
        if ( -1 == filepath.find(".txt") ):
            filepath += ".txt"
        tbuf = self.textbuffer
        text = tbuf.get_text( tbuf.get_start_iter(), tbuf.get_end_iter(), False )
        try:
            open(filepath, 'w').write(text)
        except SomeError as err:
            self.append_text( 'Ошибка сохранения в %s: %s' % (filepath, err) )


    def on_network_clicked( self, widget ):
        dialog = NetworkDialog( self, self.receiver.mcast_grp, self.receiver.mcast_port  )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.receiver.mcast_grp = dialog.group.get_text()
            self.receiver.mcast_port = int ( dialog.port.get_value() )
        dialog.destroy()

    def on_clear_clicked(self, widget):
        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        self.textbuffer.remove_all_tags(start, end)

    def on_search_clicked(self, widget):
        dialog = SearchDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            cursor_mark = self.textbuffer.get_insert()
            start = self.textbuffer.get_iter_at_mark(cursor_mark)
            if start.get_offset() == self.textbuffer.get_char_count():
                start = self.textbuffer.get_start_iter()

            self.search_and_mark(dialog.entry.get_text(), start)

        dialog.destroy()

    def search_and_mark(self, text, start):
        end = self.textbuffer.get_end_iter()
        match = start.forward_search(text, 0, end)

        if match is not None:
            match_start, match_end = match
            self.textbuffer.apply_tag(self.tag_found, match_start, match_end)
            self.search_and_mark(text, match_end)

#    def set_reciever( self, rec ):
#        self.receiver = rec

    def on_recieve_clicked ( self, widget ):
        print ( widget.get_active() )
        self.button_nc.set_sensitive( not widget.get_active() )
        if ( widget.get_active() ):
            self.receiver.socket_create()
        else:
            self.receiver.socket_close()


if __name__ == '__main__':
    win = TextViewWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    Gtk.main()
