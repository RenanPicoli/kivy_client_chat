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

# for using shared storage
from shutil import rmtree
from os.path import exists, join
from android import mActivity, autoclass, api_version
from androidstorage4kivy import SharedStorage, Chooser
from android_permissions import AndroidPermissions

from kivy.logger import Logger

'''
if platform == "android":
    from android.permissions import request_permissions, Permission, check_permission  # pylint: disable=import-error # type: ignore
    request_permissions([Permission.READ_EXTERNAL_STORAGE,
                        Permission.WRITE_EXTERNAL_STORAGE])
'''

remote_cond = False
listen_cond = False
listen_msg = ''
remote_msg = ''
send_file=False
files_to_send=[]
HOST = '192.168.15.4' # cellphone's own IP
PORT = 65432

def sender():
    global remote_msg, send_file,files_to_send
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
                    # checks if there is a file to send
                    elif send_file==True:
                        send_file=False
                        for file in files_to_send:
                            with open(file,"rb") as f:
                                msg = f.read()
                                remote_socket.sendall(msg)# sendall sends bytes
                                files_to_send.remove(file)
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
        selected_path = ''
        # create chooser listener
        self.chooser = Chooser(self.chooser_callback)
        
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
        #self.show_load_list()
  
        # cleanup from last time if Android didn't
        temp = SharedStorage().get_cache_dir()
        if temp and exists(temp):
            rmtree(temp)
            
        self.chooser.choose_content("image/*")

    # Chooser interface
    #def chooser_start(self,bt):
    #    self.chooser.choose_content("image/*")

    def chooser_callback(self,uri_list):
        try:
            ss = SharedStorage()
            for uri in uri_list:
                # copy to private
                self.selected_path = ss.copy_from_shared(uri)
                #self.append(f"path = {self.selected_path}")
                print(f"path = {self.selected_path}")
                if self.selected_path:
                    # then to app shared
                    shared = ss.copy_to_shared(self.selected_path)
                    #self.append(f"shared = {shared}")
                    #self.append("Result copied to app shared "+\
                    #            str(exists(self.selected_path) and shared != None))
            #self.display()
            self.show_load_list(self.selected_path)
        except Exception as e:
            Logger.warning('MyChat: SharedStorageExample.chooser_callback():')
            Logger.warning(str(e))
        
    def show_load_list(self,selected_path):
        '''
        content = LoadDialog(load=self.load_list, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load a file list", content=content, size_hint=(1, 1))
        self._popup.open()
        '''
        global send_file,files_to_send
        print(f'Selected {selected_path}')
        send_file=True
        files_to_send=[selected_path] # filename is a list of selected files

    def load_list(self, path, filename):
        global send_file,files_to_send
        print(f'Selected {filename} at path: {path}')
        send_file=True
        files_to_send=filename # filename is a list of selected files
        self._popup.dismiss()

    def dismiss_popup(self):
        self._popup.dismiss()
    
class BoxApp(App):
    def build(self):
        Logger.info('MyChat: started build')
        Window.softinput_mode = 'below_target'
        
        self.screenm = ScreenManager(transition=FadeTransition())
        
        self.initscreen = InitScreen(name="initscreen")
        #screen = Screen(name="initscreen")
        self.screenm.add_widget(self.initscreen)
        
        self.mainscreen = MainScreen(name="mainscreen")
        #screen = Screen(name="mainscreen")
        self.screenm.add_widget(self.mainscreen)
        
        Logger.info('MyChat: succesful build')
        return self.screenm

    def on_start(self):
        self.dont_gc = AndroidPermissions(self.start_app)    

    def start_app(self):
        self.dont_gc = None
        #ss = SharedStorage()
        #app_title = str(ss.get_app_title())
        #self.label_lines = []
        #self.display()
        #self.append("Cache Dir Exists:  " + str(exists(ss.get_cache_dir())))

if __name__ == '__main__':
    try:
        Logger.info('MyChat: entry point at main:')
        boxapp = BoxApp()
        listen_cond = False
        thread_1.start()
        thread_2.start()
        remote_cond = False
        #threading.Thread(target = boxapp.run()).start()
        boxapp.run()
    except Exception as e:
        Logger.info('MyChat: exception at main:'+str(e))
