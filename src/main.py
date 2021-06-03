import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
# to use buttons:
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
import socket_client
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
import sys


kivy.require("1.10.1")


class ConnectPage(GridLayout):
    # Runs on initialisation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #Used for the grid in the UI
        self.cols = 2 

        #Read from .txt file, interpret columns
        with open("prev_details.txt","r") as f:
            d = f.read().split(",")
            prev_ip = d[0]
            prev_port = d[1]
            prev_username = d[2]

        #Creating Widget 1, top left
        self.add_widget(Label(text='IP:')) 
        #Create a text input for self.ip
        self.ip = TextInput(text=prev_ip, multiline=False) 
        #Creating Widget 2, top right
        self.add_widget(self.ip)

        
        self.add_widget(Label(text='Port:'))
        self.port = TextInput(text=prev_port, multiline=False)
        self.add_widget(self.port)

        
        self.add_widget(Label(text='Username:'))
        self.username = TextInput(text=prev_username, multiline=False)
        self.add_widget(self.username)

        #Add button
        self.join = Button(text="Join")
        self.join.bind(on_press=self.join_button)
        self.add_widget(Label())  # just take up the spot.
        self.add_widget(self.join)


    def join_button(self, instance):
        #Set values to the text inputs
        port = self.port.text
        ip = self.ip.text
        username = self.username.text
        with open("prev_details.txt","w") as f:
            f.write(f"{ip},{port},{username}")
        #print(f"Joining {ip}:{port} as {username}")
        # Create info string, update InfoPage with a message and show it
        info = f"Joining {ip}:{port} as {username}"
        chat_app.info_page.update_info(info)
        chat_app.screen_manager.current = 'Info'
        Clock.schedule_once(self.connect, 1)

    # Connects to the server
    def connect(self, _):

        # Get information for sockets client
        port = int(self.port.text)
        ip = self.ip.text
        username = self.username.text

        if not socket_client.connect(ip, port, username, show_error):
            return

        # Create chat page and activate it
        chat_app.create_chat_page()
        chat_app.screen_manager.current = 'Chat'




class ScrollableLabel(ScrollView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = GridLayout(cols=1, size_hint_y=None)
        self.add_widget(self.layout)

        self.chat_history = Label(size_hint_y=None, markup=True)
        self.scroll_to_point = Label()

        self.layout.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll_to_point)

    # Method called externally to add new message to the chat history
    def update_chat_history(self, message):

        # First add new line and message itself
        self.chat_history.text += '\n' + message

        # Set layout height to whatever height of chat history text is + 15 pixels
        self.layout.height = self.chat_history.texture_size[1] + 15
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)

        self.scroll_to(self.scroll_to_point)



class ChatPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cols = 1
        self.rows = 2

        self.history = ScrollableLabel(height=Window.size[1]*0.9, size_hint_y=None)
        self.add_widget(self.history)

        
        self.new_message = TextInput(width=Window.size[0]*0.8, size_hint_x=None, multiline=False)
        self.send = Button(text="Send")
        self.send.bind(on_press=self.send_message)

        bottom_line = GridLayout(cols=2)
        bottom_line.add_widget(self.new_message)
        bottom_line.add_widget(self.send)
        self.add_widget(bottom_line)



        # Listen to key press.
        Window.bind(on_key_down=self.on_key_down)

        # We also want to focus on our text input field
        Clock.schedule_once(self.focus_text_input, 1)

        # Start listening for incoming messages
        socket_client.start_listening(self.incoming_message, show_error)


    # Called on key press
    def on_key_down(self, instance, keyboard, keycode, text, modifiers):

        # Take an action only when Enter key is being pressed, and send a message
        if keycode == 40:
            self.send_message(None)

    # Gets called when either Send button or Enter key is being pressed
    def send_message(self, _):

        # Get message text and clear message input field
        message = self.new_message.text
        self.new_message.text = ''

        # If there is any message - add it to chat history and send to the server
        if message:
            self.history.update_chat_history(f'[color=dd2020]{chat_app.connect_page.username.text}[/color] > {message}')
            socket_client.send(message)

        Clock.schedule_once(self.focus_text_input, 0.1)


    # Sets focus to text input field
    def focus_text_input(self, _):
        self.new_message.focus = True

    # Passed to sockets client, called on new message
    def incoming_message(self, username, message):
        # Update chat history with username and message, green color for username
        self.history.update_chat_history(f'[color=20dd20]{username}[/color] > {message}')


# Simple information/error page
class InfoPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cols = 1

        self.message = Label(halign="center", valign="middle", font_size=30)

        self.message.bind(width=self.update_text_width)

        # Add text widget to the layout
        self.add_widget(self.message)

    # Called with a message, to update message text in widget
    def update_info(self, message):
        self.message.text = message

    def update_text_width(self, *_):
        self.message.text_size = (self.message.width * 0.9, None)


class KwikMedical(App):
    def build(self):

        # Allows the use of multiple screens and the option to switch between them
        self.screen_manager = ScreenManager()

        # Initial, connection screen (we use passed in name to activate screen)
        self.connect_page = ConnectPage()
        screen = Screen(name='Connect')
        screen.add_widget(self.connect_page)
        self.screen_manager.add_widget(screen)

        # Info page
        self.info_page = InfoPage()
        screen = Screen(name='Info')
        screen.add_widget(self.info_page)
        self.screen_manager.add_widget(screen)

        return self.screen_manager

    def create_chat_page(self):
        self.chat_page = ChatPage()
        screen = Screen(name='Chat')
        screen.add_widget(self.chat_page)
        self.screen_manager.add_widget(screen)


# Error callback function, used by sockets client
def show_error(message):
    chat_app.info_page.update_info(message)
    chat_app.screen_manager.current = 'Info'
    Clock.schedule_once(sys.exit, 10)

if __name__ == "__main__":
    chat_app = KwikMedical()
    chat_app.run()