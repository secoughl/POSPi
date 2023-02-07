import tkinter as tk
import json
import requests
import tkinter.scrolledtext as tkscrolled
import os
import random
import config
from tkinter.font import BOLD
from tkinter import font
from tkinter.constants import RAISED
from playsound import playsound
from pygame import mixer




base_url = config.grocy_base_url
stockReqUrl = "stock/products/by-barcode/"
GROCY_API = config.api_key
working_dir = os.getcwd()

#Initialzing pyamge mixer
mixer.init()
# Default to consume mode
mode = "consume"
product_id = ""

# Ping Grocy's API to resolve barcode string to Grocy's products and call the appropriate modification function if successful
def product_id_lookup(upc):
        # Need to declare this as a global and we'll do this again with a few others because we need them elsewhere
        global product_id
        printHistory("Looking up the UPC: %s" %upc)
        # Lets check to see if the UPC exists in grocy
        url = base_url+"/stock/products/by-barcode/%s" % (upc)
        headers = {
        'cache-control': "no-cache",
        'GROCY-API-KEY': GROCY_API
        }
        r = requests.get(url, headers=headers)
        r.status_code
        print (r.status_code)
        if r.status_code != 200:
            printHistory("I dunno, bud")
            strErrorCode.set("Last HTTP Response: %i" % (r.status_code))
            product_id = 0
            playRandom(sad_dir)
            return
        # Going to check and make sure that we found a product to use.  If we didn't find it lets search the internets and see if we can find it.
        j = r.json()
        global product_id_lookup
        product_id = j['product']['id']
        global purchase_amount
        purchase_amount = float(j['product']['qu_factor_purchase_to_stock'])
        global consume_amount
        consume_amount = float(j['product']['quick_consume_amount'])
        global product_name
        product_name = j['product']['name']
        print ("Our product_id is %s" % (product_id))
        global stock_amount
        stock_amount = int(j['stock_amount'])
        if mode == "purchase" and product_id != 0:
            # Debug Info. Probably should clean this up but meh
            #printHistory("would add %f to %s" % (purchase_amount, product_name))
            purchase_product(product_id,product_name,purchase_amount)
        if mode == "consume" and product_id != 0:
            # Debug Info. Probably should clean this up but meh
            #printHistory("would remove %f from %s" % (consume_amount, product_name))
            consume_product(product_id,product_name,consume_amount,stock_amount)

def consume_product(product_id,product_name,consume_amount,stock_amount):
        if stock_amount > 0:
            new_stock_amount = stock_amount - consume_amount
            printHistory("Will remove %f from %s resulting in %f remaining" % (consume_amount, product_name,new_stock_amount))
            url = base_url+"/stock/products/%s/consume" % (str(product_id))
            data = {'amount': consume_amount,
            'transaction_type': 'consume',
            'spoiled': 'false'}
            grocy_api_call_post(url, data)
            playRandom(happy_dir)
        else:
            printHistory("Out of product %s" % (product_name))
            playRandom(sad_dir)


# Build info and pass it to POST helper for adding product to Grocy
def purchase_product(product_id,product_name,purchase_amount):
        global response_code
        new_stock_amount = stock_amount + purchase_amount
        printHistory("Will add %f to %s resulting in %f remaining" % (purchase_amount, product_name,new_stock_amount)) 
        url = base_url+"/stock/products/%s/add" % (product_id)
        data = {'amount': purchase_amount,
        'transaction_type': 'purchase'}
        grocy_api_call_post(url, data)
        if response_code == 200:
            playRandom(happy_dir)
        if response_code != 200:
            printHistory("Increasing the value of %s failed" % (product_name))
            strErrorCode.set("Last HTTP Response: %i" % (response_code))
            playRandom(sad_dir)

# Function to handle POST's, manipulate inventory values based on product
def grocy_api_call_post(url, data):
    headers = {
        'cache-control': "no-cache",
        'GROCY-API-KEY': GROCY_API
        }
    try:
        r = requests.post(url=url, json=data, headers=headers)
        r.status_code
        global response_code
        response_code = r.status_code
        # print (r.status_code)
        strErrorCode.set("Last HTTP Response: %i" % (response_code))
    except requests.exceptions.Timeout:
        printHistory("The connection timed out")
    except requests.exceptions.TooManyRedirects:
        printHistory("Too many redirects")
    except requests.exceptions.RequestException as e:
        printHistory(e)

# Set logic after scan / update label to reflect 
def change_mode(desmode):
    global mode 
    mode = desmode
    strMode.set("Mode: %s ensure below box is highlighted" %desmode)
    inputtxt.focus_set()

# Submit barcode on return keystroke to (eventually) Grocy's API
def printInput():
    inp = inputtxt.get()
    inputtxt.delete(0, 'end')
    if (inp != ''):
        product_id_lookup(inp.strip())

# Got tired of formatting and force-scrolling text box. Made a function for it
def printHistory(text):
    historytxt.insert(tk.END,text +'\n')
    historytxt.see(tk.END)

def playRandom(path):
    # Get a list of files in the supplied directory
    list = os.listdir(path)
    # Loading Random Music File
    mixer.music.load(path + random.choice(list)) 
    # Playing Music with Pygame
    mixer.music.play() 


screen_height = 480
screen_width = 800

window = tk.Tk()
window.defaultFont = font.nametofont("TkDefaultFont")
window.defaultFont.configure(size=19,weight=font.BOLD)
window.minsize(width= screen_width,height=screen_height,)
window.title("Grocy Buddy")

# Ignore all tab hits from input text box
# This is to deal with keeping my scanner compatible to other uses
def no_tab(event):
    return 'break'

# Wait for return keystroke and act on it (Scanner submitted)
def func(event):
    printInput()
window.bind('<Return>', func)




strMode = tk.StringVar()
strMode.set("Mode: %s ensure below box is highlighted" %mode)
strErrorCode = tk.StringVar()
strErrorCode.set("Last HTTP Response: ")

frame1 = tk.Frame( width = screen_width/2, height = screen_height/2)
frame1.grid(row=0, column=0, padx=5, pady=5, rowspan=2)

frame2 = tk.Frame( width = screen_width/2, height = screen_height/2)
frame2.grid(row=0, column=1, padx=5, pady=5, rowspan=2)

frame4 = tk.Frame( width = screen_width/2, height = screen_height/2)
frame4.grid(row=2, column=0, padx=5, pady=5, rowspan=2)

#region Interactable Elements
PurchaseButton = tk.Button(
    master = frame1,
    text="Purchase Mode",
    command= lambda: change_mode("purchase"),
    width=25,
    height=5,
    bg="blue",
    fg="yellow",
)

ConsumeButton = tk.Button(
    master = frame1,
    text="Consumption Mode",
    command= lambda: change_mode("consume"),
    width=25,
    height=5,
    bg="blue",
    fg="yellow",
)

modelabel = tk.Label(
    master=frame4,
    textvariable=strMode,
    relief=RAISED,
    width=len(strMode.get()),  
    font=(BOLD),
)

inputtxt = tk.Entry(
    master=frame4,
    width = 50,
)

historytxt = tkscrolled.ScrolledText(
    master=frame2,
    height=20, 
    width=30, 
    wrap='word',
)    

lblErrorCode = tk.Label(
    master=frame2,
    textvariable=strErrorCode,
    relief=RAISED,
    width=len(strErrorCode.get())+3,  
    font=BOLD,
)
#endregion Interactable Elements

# Pack Calls
PurchaseButton.pack()
ConsumeButton.pack()

modelabel.pack()
inputtxt.pack()
historytxt.pack()
lblErrorCode.pack()

# Specific settings to control flow of control interaction in UI
inputtxt.bind('<Tab>',no_tab)
inputtxt.focus_set()

# Determine / or \ to find media path
if os.name == 'nt':
    media_dir = working_dir + '\media\\'
    welcome_dir = media_dir + 'welcome\\'
    happy_dir = media_dir + 'happy\\'
    sad_dir = media_dir + 'sad\\'
else:
    media_dir = working_dir + '/media/'
    welcome_dir = media_dir + 'welcome/'
    happy_dir = media_dir + 'happy/'
    sad_dir = media_dir + 'sad/'

playRandom(welcome_dir)
window.mainloop()