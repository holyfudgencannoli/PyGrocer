from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
import shutil
import sqlite3
from kivy.utils import platform
from kivy.resources import resource_find
import sqlite3
import os
import requests
from kivy.logger import Logger
from datetime import datetime

class DateInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_length = 10
        self.multiline = False
        self.hint_text = 'YYYY-MM-DD'
        self.input_filter = 'int'

    def insert_text(self, substring, from_undo=False):
        # Remove non-digits
        filtered = ''.join(filter(str.isdigit, substring))
        raw = self.text.replace('-', '') + filtered
        raw = raw[:8]  # Max 8 digits (YYYYMMDD)

        # Format to YYYY-MM-DD
        formatted = ''
        if len(raw) >= 4:
            formatted += raw[:4] + '-'
            if len(raw) >= 6:
                formatted += raw[4:6] + '-'
                formatted += raw[6:]
            else:
                formatted += raw[4:]
        else:
            formatted += raw

        self.text = formatted
        self.cursor = (len(self.text), 0)

        # Full validation only when input is complete
        if len(self.text) == 10:
            self.validate_date(self.text)

    def validate_date(self, date_str):
        try:
            year, month, day = map(int, date_str.split('-'))

            # Validate basic year range
            if year < 2022:
                raise ValueError("Year before 2022.")

            # Will raise ValueError if the date is invalid
            date_obj = datetime(year, month, day)

            # Check if date is in the future
            if date_obj.date() > datetime.today().date():
                raise ValueError("Date is in the future.")

            print("✅ Valid date:", date_str)

        except ValueError as e:
            print("❌ Invalid date:", e)
            self.text = ''  # Clear the input (or show error in app)

class ColoredBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.2, 0.6, 0.8, 1)  # Light blue
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos

class Integer12DigitInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_filter = 'int'
        self.multiline = False
        self.hint_text = 'Enter up to 12 digits'

    def insert_text(self, substring, from_undo=False):
        # Only allow digits and limit to 12 total
        filtered = ''.join(filter(str.isdigit, substring))
        new_text = self.text + filtered
        if len(new_text) > 12:
            filtered = filtered[:12 - len(self.text)]
        super().insert_text(filtered, from_undo=from_undo)


class UPCInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_filter = 'int'
        self.multiline = False
        self.hint_text = 'Enter 12-digit UPC'

    def insert_text(self, substring, from_undo=False):
        # Only allow digits and limit to 12 total
        filtered = ''.join(filter(str.isdigit, substring))
        new_text = self.text + filtered
        if len(new_text) > 12:
            filtered = filtered[:12 - len(self.text)]
        super().insert_text(filtered, from_undo=from_undo)

        # Validate if 12 digits are reached
        if len(self.text) + len(filtered) == 12:
            self.validate_upc(self.text + filtered)

    def validate_upc(self, code):
        if len(code) != 12:
            print("❌ UPC must be exactly 12 digits.")
            return

        digits = [int(d) for d in code]
        odd_sum = sum(digits[i] for i in range(0, 11, 2))
        even_sum = sum(digits[i] for i in range(1, 11, 2))
        total = (odd_sum * 3) + even_sum
        check_digit = (10 - (total % 10)) % 10

        if check_digit == digits[-1]:
            print("✅ Valid UPC:", code)
        else:
            print(f"❌ Invalid UPC. Expected check digit: {check_digit}")
            self.text = ''  # Optionally clear input

class DatabaseManager:
    def __init__(self, db_filename='../grocer.db'):
        # Determine where the writable DB should live
        if platform == 'android':
            from android.storage import app_storage_path
            app_path = app_storage_path()  # e.g. /data/data/org.yourname/files
            self.db_path = os.path.join(app_path, db_filename)

            # If not yet copied, copy the blank DB from assets
            if not os.path.exists(self.db_path):
                asset_path = resource_find(db_filename)
                shutil.copy(asset_path, self.db_path)
        else:
            # On desktop just use the local file
            self.db_path = db_filename

        # Now open the database normally
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create_table()  # ensures table exists if file was truly blank
        self.conn.commit()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS items 
                                (id INTEGER PRIMARY KEY, name TEXT, pkg_unit TEXT, pkg_qty REAL, inv_unit TEXT, 
                                 inv_qty REAL, price REAL, store TEXT, date TEXT, sku INTEGER, upc INTEGER)''')
        self.conn.commit()
    
    def add_item(self, name, pkg_unit, pkg_qty, inv_unit, inv_qty, price, store, date, sku, upc):
        try:
            pkg_unit = pkg_unit[0]
            pkg_qty = pkg_qty[0]
            inv_unit = inv_unit[0]
            inv_qty = inv_qty[0]
            price = price[0]
            store = store[0]
            date = date[0]
            self.cursor.execute('INSERT INTO items (name, pkg_unit, pkg_qty, inv_unit, inv_qty, price, store, date, sku, upc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (name, pkg_unit, pkg_qty, inv_unit, inv_qty, price, store, date, sku, upc))
            self.conn.commit()
            print(f"Added item: {name}")
        except sqlite3.Error as e:
            print(f"Database error: {e}")


        

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()


class home(Screen):
    def __init__(self, **kwargs):
        super(home, self).__init__(**kwargs)
        layout = FloatLayout(size=(1080, 1920))
        label = Label(text="Grocer",size_hint=(.75,.2),pos_hint={'x':.125,'y':.7},font_size='100sp')
        button1 = Button(text="Create a new item",size_hint=(.75,.2),pos_hint={'x':.125,'y':.4})
        button2 = Button(text="Current items & inventory",size_hint=(.75,.2),pos_hint={'x':.125,'y':.2})
        button3 = Button(text="Print a grocery list",size_hint=(.75,.2),pos_hint={'x':.125,'y':0})
        button1.bind(on_press=self.go_to_new_item)
        button2.bind(on_press=self.go_to_inventory)
        button3.bind(on_press=self.go_to_list)
        layout.add_widget(label)
        layout.add_widget(button1)
        layout.add_widget(button2)
        layout.add_widget(button3)
        self.add_widget(layout)

    def go_to_new_item(self, instance):
        self.manager.current = 'new_item'

    def go_to_inventory(self, instance):
        self.manager.current = 'inventory'

    def go_to_list(self, instance):
        self.manager.current = 'create_list'

class new_item(Screen):
    def __init__(self, **kwargs):
        super(new_item, self).__init__(**kwargs)
        self.db = DatabaseManager()
        layout = FloatLayout(size=(1080, 1920))
        label = Label(text="Create a new item for your inventory",size_hint=(.5,.05),pos_hint={'x':.25,'y':.9})

        self.name_input=TextInput(hint_text='Name',size_hint=(.5,.03),pos_hint={'x':.25,'y':.8})

        self.pkg_qty_input=TextInput(hint_text='Package Quantity', input_filter='float',size_hint=(.5,.03),pos_hint={'x':.25,'y':.77})

        self.pkg_unit_input=Spinner(text='Package Unit',values=('Pack','Case','Box','Bag','Bottle','Sack'),size_hint=(.5,.03),pos_hint={'x':.25,'y':.74})
        
        self.inv_qty_input=TextInput(hint_text='Count per Package', input_filter='float',size_hint=(.5,.03),pos_hint={'x':.25,'y':.71})

        self.inv_unit_input=Spinner(text='Counting Unit',values=('Ct.','Pcs.','Milliliters','Liters','Fluid Ounces','Pints','Quarts','Gallons','Grams','Kilograms','Ounces','Pounds'),size_hint=(.5,.03),pos_hint={'x':.25,'y':.68})

        self.price_input=TextInput(hint_text='Price', input_filter='float',size_hint=(.5,.03),pos_hint={'x':.25,'y':.65})

        self.store_input=TextInput(hint_text='Store',size_hint=(.5,.03),pos_hint={'x':.25,'y':.62})

        self.date_input=DateInput(hint_text='Date',size_hint=(.5,.03),pos_hint={'x':.25,'y':.59})

        self.sku_input=Integer12DigitInput(hint_text='SKU',size_hint=(.5,.03),pos_hint={'x':.25,'y':.56})
        
        self.upc_input=UPCInput(hint_text='UPC', input_filter='int',size_hint=(.5,.03),pos_hint={'x':.25,'y':.53})
        
        

        submit = Button(text="Submit",size_hint=(.6,.1),pos_hint={'x':.2,'y':.1})

        back = Button(text="Go Back",size_hint=(.6,.1),pos_hint={'x':.2,'y':0})

        submit.bind(on_press=self.add_item)
        back.bind(on_press=self.go_back)
        
        layout.add_widget(label)
        layout.add_widget(self.name_input)
        layout.add_widget(self.pkg_qty_input)
        layout.add_widget(self.pkg_unit_input)
        layout.add_widget(self.inv_qty_input)
        layout.add_widget(self.inv_unit_input)
        layout.add_widget(self.price_input)
        layout.add_widget(self.store_input)
        layout.add_widget(self.date_input)
        layout.add_widget(self.sku_input)
        layout.add_widget(self.upc_input)
        layout.add_widget(submit)
        layout.add_widget(back)
        self.add_widget(layout)

    def go_back(self, instance):
        self.manager.current = 'home'

    def create_item(self, instance):
        if (not self.name_input.text or not self.pkg_unit_input.text or not self.pkg_qty_input.text or not self.inv_unit_input.text or not self.inv_qty_input.text or not self.price_input.text or not self.store_input.text or not self.date_input.text or not self.sku_input.text):
            self.show_warning('empty fields')
        else:
            item = [self.name_input.text, self.pkg_unit_input.text, self.pkg_qty_input.text, self.inv_unit_input.text, self.inv_qty_input.text, self.price_input.text, self.store_input.text, self.date_input.text, self.sku_input.text, self.upc_input.text]
            print(item)

    # def send_data(self, instance):
    #     session = requests.Session()

    #     session.headers.update({
    #         'Authorization': 'token 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',
    #         'User-Agent': 'Mozilla/5.0',
    #         'Accept': 'application/json',
    #         'Content-Type': 'application/json'
    #     })
    #     url='https://github.com/holyfudgencannoli/grocerAPI/blob/main/grocerAPI.json'
    #     data = {
    #         'name': self.name_input.text,
    #         'pkg_unit': self.pkg_unit_input.text,
    #         'pkg_qty': self.pkg_qty_input.text,
    #         'inv_unit': self.inv_unit_input.text,
    #         'inv_qty': self.inv_qty_input.text,
    #         'price': self.price_input.text,
    #         'store': self.store_input.text,
    #         'date': self.date_input.text,
    #         'sku': self.sku_input.text
    #     }
        
        # try:
        #     response = session.post(url, json=data)
        #     print("Response:", response.text)
        # except Exception as e:
        #     print("Error:", e)
    
    def show_warning(self, message):
        popup = Popup(
            title='Input Error',
            content=Label(text=message),
            size_hint=(None,None),
            size=(300,150)
            )
        popup.open()

    def add_item(self, instance):
        name = self.name_input.text
        pkg_unit = self.pkg_unit_input.text,
        pkg_qty = self.pkg_qty_input.text,
        inv_unit = self.inv_unit_input.text,
        inv_qty = self.inv_qty_input.text,
        price = self.price_input.text,
        store = self.store_input.text,
        date = self.date_input.text,
        sku = self.sku_input.text
        upc = self.upc_input.text
        self.db.add_item(name, pkg_unit, pkg_qty, inv_unit, inv_qty, price, store, date, sku, upc)
        self.name_input.text = ''
        self.pkg_unit_input.text = ''
        self.pkg_qty_input.text = ''
        self.inv_unit_input.text = ''
        self.inv_qty_input.text = ''
        self.price_input.text = ''
        self.store_input.text = ''
        self.date_input.text = ''
        self.sku_input.text = ''
        self.upc_input.text = ''
    

    # def create_item(self, instance):
    #     item = self.item
    #     print(item)
    #     print(self.pkg_qty_input)

class inventory(Screen):
    def __init__(self, db_manager, **kwargs):
        super(inventory, self).__init__(**kwargs)
        self.db_manager = db_manager

        layout = FloatLayout(size=(1080, 1920))
        label = Label(text="Current Items & Inventory", size_hint=(.75, .2), pos_hint={'x': .125, 'y': 0.8})

        # ScrollView wraps content_box
        scroll_view = ScrollView(
            size_hint=(0.5, 1),
            pos_hint={'center_x': 0.5, 'top': 0.85}
        )

        self.content_box = ColoredBox(
            orientation='vertical',
            size_hint_y=None,
            padding=10,
            spacing=10
        )
        self.content_box.bind(minimum_height=self.content_box.setter('height'))

        scroll_view.add_widget(self.content_box)
        layout.add_widget(scroll_view)

        button = Button(text="Load Items", size_hint=(.6, .1), pos_hint={'x': .2, 'y': 0})
        button.bind(on_press=self.load_items_to_content_box)

        layout.add_widget(label)
        layout.add_widget(button)
        self.add_widget(layout)


    def go_back(self, instance):
        self.manager.current = 'home'

    def load_items_to_content_box(self, instance):
        """
        Fetches items from the database and populates self.content_box.
        """
        try:
            self.content_box.clear_widgets()

            self.db_manager.cursor.execute("SELECT id, name, pkg_unit, pkg_qty, inv_unit, inv_qty, price, store, date, sku, upc FROM items")
            rows = self.db_manager.cursor.fetchall()

            if not rows:
                self.content_box.add_widget(Label(text="No items found in database."))
                return

            for id, name, pkg_unit, pkg_qty, inv_unit, inv_qty, price, store, date, sku, upc in rows:
                label_text = f"ID: {id} | Item: {name} | {pkg_qty}  {pkg_unit} | {inv_qty}  {inv_unit} | Price: {price} | Store: {store} | Bought: {date} | SKU: {sku} | UPC: {upc}"
                item_label = Label(
                    text=label_text,
                    size_hint_y=None,
                    height=100,  # or dynamically based on content
                    text_size=(self.content_box.width, None),
                    halign='left',
                    valign='top'
                )

                self.content_box.add_widget(item_label)

        except Exception as e:
            self.content_box.add_widget(Label(text=f"Error: {e}"))



class create_list(Screen):
    def __init__(self, **kwargs):
        super(create_list, self).__init__(**kwargs)
        layout = FloatLayout(size=(1080, 1920))
        label = Label(text="Create & Print a new grocery list",size_hint=(.75,.2),pos_hint={'x':.125,'y':.8})

        content_box = ColoredBox(
            orientation='vertical',
            size_hint=(0.5, 0.3),  # 50% width, 30% height of screen
            pos_hint={'center_x': 0.5, 'center_y': 0.5},  # Centered
            padding=10,
            spacing=10)
        
        content_box.add_widget(Label(text="Hello inside a BoxLayout!"))
        content_box.add_widget(Button(text="Click Me"))

        layout.add_widget(content_box)

        button = Button(text="Go Back",size_hint=(.6,.1),pos_hint={'x':.2,'y':0})
        button.bind(on_press=self.go_back)
        layout.add_widget(label)
        layout.add_widget(button)
        self.add_widget(layout)

    def go_back(self, instance):
        self.manager.current = 'home'

class GrocerApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 1, 1)
        sm = ScreenManager(transition=SwapTransition())

        # Create DB manager
        db_manager = DatabaseManager()

        # Create screens
        home_page = home(name='home')
        new_item_page = new_item(name='new_item')
        inventory_page = inventory(name='inventory', db_manager=db_manager)
        create_list_page = create_list(name='create_list')

        # Add screens to manager
        sm.add_widget(home_page)
        sm.add_widget(new_item_page)
        sm.add_widget(inventory_page)
        sm.add_widget(create_list_page)

        return sm


if __name__ == '__main__':
    GrocerApp().run()