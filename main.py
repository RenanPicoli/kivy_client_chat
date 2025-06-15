import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from threading import Thread
from kivy.graphics import *

import socket
import threading
import time
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.properties import ObjectProperty

from kivy import platform

if platform == "android":
    from android.permissions import request_permissions, Permission, check_permission  # pylint: disable=import-error # type: ignore
    request_permissions([Permission.READ_EXTERNAL_STORAGE,
                        Permission.WRITE_EXTERNAL_STORAGE])

remote_cond = False
listen_cond = False
listen_msg = ''
remote_msg = ''
HOST = '192.168.15.4' # cellphone's own IP
PORT = 65432

def sender():
    global remote_msg
    remote_ip = '192.168.15.99'
    remote_port = 65432
    while True:
        try:
            while remote_cond == True:
                # connects to destination
                remote_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                remote_socket.connect((remote_ip,remote_port))
                while True:
                    if remote_msg != '':
                        remote_socket.sendall(remote_msg.encode())# sendall sends bytes
                        remote_msg=''
        except:
            time.sleep(0.5)
            
thread_1 = threading.Thread(target = sender)         

def listen():
    global listen_msg, listen_cond
    listen_cond = True
    while listen_cond == True:
        try:
            listen_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            listen_socket.bind((HOST,PORT))
            # starts to listen
            listen_socket.listen()
            while True:
                # wait until connected
                conn, addr = listen_socket.accept()
                with conn: # is a socket object for communicating with other side after connection is accepted
                    #print(f"Connected by {addr}") # addr is a tuple (host, port) of the other side
                    while True:
                        # reads up to 1024 bytes, blocking method
                        data  = conn.recv(1024) # data is of bytes type
                        if not data:
                            break
                        #print(data.decode('utf-8')+"\n") # converts data to string and prints
                        listen_msg  = data.decode('utf-8')
        except:
            time.sleep(0.5)
            print("binding...")
            
thread_2 = threading.Thread(target = listen)
        
class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class InitScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def initiate(self):
        global remote_cond
        remote_cond = True
        boxapp.screenm.current = 'mainscreen'
        Clock.schedule_interval(boxapp.mainscreen.update_received, 0.5)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def send_msg(self):
        global remote_msg
        self.ids.chat_text_id.text = self.ids.chat_text_id.text + "\n"
        remote_msg = self.ids.msg_id.text
        self.ids.chat_text_id.text = self.ids.chat_text_id.text + "You:" + self.ids.msg_id.text
        # this is done to prevent from sending previous text again
        self.ids.msg_id.text = ''
        
    def update_received(self, widget):
        global listen_msg
        if listen_msg != '':
            self.ids.chat_text_id.text = self.ids.chat_text_id.text + "\n" + "Other side:" + listen_msg
            listen_msg = ''
            
    def send_file(self):
        self.show_load_list()
        
    def show_load_list(self):
        content = LoadDialog(load=self.load_list, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load a file list", content=content, size_hint=(1, 1))
        self._popup.open()

    def load_list(self, path, filename):
        print(f'Selected {filename} at pah: {path}')

    def dismiss_popup(self):
        self._popup.dismiss()
    
class BoxApp(App):
    def build(self):
        Window.softinput_mode = 'below_target'
        
        self.screenm = ScreenManager(transition=FadeTransition())
        
        self.initscreen = InitScreen(name="initscreen")
        #screen = Screen(name="initscreen")
        self.screenm.add_widget(self.initscreen)
        
        self.mainscreen = MainScreen(name="mainscreen")
        #screen = Screen(name="mainscreen")
        self.screenm.add_widget(self.mainscreen)
        
        return self.screenm

if __name__ == '__main__':
    boxapp = BoxApp()
    listen_cond = False
    thread_1.start()
    thread_2.start()
    remote_cond = False
    threading.Thread(target = boxapp.run()).start()
