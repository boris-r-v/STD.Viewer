import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango, GLib

import gtk
import threading
import socket
import struct
import sys


class Reciever( ):
    def __init__(self, textview):
        self.text = textview
        self.socket_create()

    def listen( self ):
        threading.Thread( target = self.threading_func ).start()

    def socket_create ( self ):
        mcast_grp = '224.1.1.1'
        mcast_port = 20050

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((mcast_grp, mcast_port))
        mreq = struct.pack("4sl", socket.inet_aton(mcast_grp), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


    def threading_func( self ):
        self.text.append_text( self.sock.recv(1024).decode("utf-8") )



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
    def __init__(self, parent):
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
        self.group.set_text( "224.1.1.1" )
        box.add( self.group )


        label = Gtk.Label(label="Set UDP port:")
        box.add(label)

        self.port = Gtk.Entry( )
        self.port.set_text( "20050" )
        box.add( self.port )

        self.show_all()


class TextViewWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="TextView Example")

        self.set_default_size(900, 350)

        self.grid = Gtk.Grid()
        self.add(self.grid)

        self.create_textview()
        self.create_toolbar()

    def create_toolbar(self):
        toolbar = Gtk.Toolbar()
        self.grid.attach(toolbar, 0, 0, 3, 1)

        button_search = Gtk.ToolButton()
        button_search.set_icon_name("system-search-symbolic")
        button_search.connect("clicked", self.on_search_clicked)
        toolbar.insert(button_search, 0)

        toolbar.insert(Gtk.SeparatorToolItem(), 1)

        button_clear = Gtk.ToolButton()
        button_clear.set_icon_name("edit-clear-symbolic")
        button_clear.connect("clicked", self.on_clear_clicked)
        toolbar.insert(button_clear, 2)

        toolbar.insert(Gtk.SeparatorToolItem(), 3 )

        button_clear = Gtk.ToolButton()
        button_clear.set_icon_name("network-wired-symbolic")
        button_clear.connect("clicked", self.on_network_clicked)
        toolbar.insert(button_clear, 4)

        toolbar.insert(Gtk.SeparatorToolItem(), 5 )

    def append_text(self, text ):
        self.textbuffer.insert_at_cursor( text )

    def create_textview(self):
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        self.grid.attach(scrolledwindow, 0, 1, 3, 1)
        self.textview = Gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        scrolledwindow.add(self.textview)

        self.tag_found = self.textbuffer.create_tag("found", background="yellow")

    def on_network_clicked( self, widget ):
        dialog = NetworkDialog( self )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            group = dialog.group.get_text()
            port = dialog.group.get_text()

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

if __name__ == '__main__':
    win = TextViewWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Reciever( win ).listen()
    Gtk.main()
