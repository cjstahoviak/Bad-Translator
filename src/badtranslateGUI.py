import googletrans as g
import re
import random
from spellchecker import SpellChecker
from tkinter import *
import tkinter.ttk as ttk
from tkinter import scrolledtext 
from tkinter.messagebox import showinfo
from tkinter.filedialog import askopenfile 

spell = SpellChecker(language='en')
allLanguages = len(g.LANGUAGES)
t = g.Translator()

'''
    Absolutley destroys your english, for the console
'''
def ruinSentence(string, numRounds):

    print("[*] Went through: ", end='')

    oldchoice = 'en'
    newchoice = ''
    for i in range(numRounds):

        print("{}->".format(g.LANGUAGES.get(oldchoice)), end='')

        newchoice = random.choice(list(g.LANGUAGES))

        string = t.translate(string, src=oldchoice, dest=newchoice).text

        oldchoice = newchoice

    string = t.translate(string, src=oldchoice, dest='en').text

    print(g.LANGUAGES.get('en'))

    return string

'''
    Absolutley destroys your english, for the GUI
'''
def ruinSentenceGUI(string, numRounds, parse_title):

    parse_list = ""

    oldchoice = 'en'
    newchoice = ''
    for i in range(numRounds):

        parse_list += "{}->".format(g.LANGUAGES.get(oldchoice))
        
        newchoice = random.choice(list(g.LANGUAGES))

        string = t.translate(string, src=oldchoice, dest=newchoice).text

        oldchoice = newchoice

    string = t.translate(string, src=oldchoice, dest='en').text

    parse_list += g.LANGUAGES.get('en')
    parse_title.config(text=parse_list)

    return string

'''
    Auto corrects any mispelled words in the input so that the translator
    doesn't freak out.

    Translator may have built in spell correction but this is a safe gaurd
'''
def correctSpelling(string):
    words = spell.split_words(string)
    #print("After fix")
    #print(' '.join([spell.correction(word) for word in words]))
    return ' '.join([spell.correction(word) for word in words])

'''
    Callback specifically for the translate GUI button
'''
def translateCallback(num_ent, input_txtbx, output_txtbx, parse_title, window):
    #print("Callback activated")

    # Activate and clear the output text of the previoius translation
    output_txtbx.config(state=NORMAL)
    output_txtbx.delete("1.0", END)

    # Let the user know I'm busy translating...
    parse_title.config(text="Translating...")
    #window.mainloop()
    
    # Grab whatever the user typed in and spell check
    user_input = input_txtbx.get("1.0",END)
    user_input = correctSpelling(user_input)

    # Put the the translation in the output box
    translated = ruinSentenceGUI(user_input, int(num_ent.get()), parse_title)
    output_txtbx.insert("1.0", translated)
    output_txtbx.config(state=DISABLED)



'''
    Stolen from StackOverflow

    Shows and instructional box when the program starts up
'''
def popup_window():
    window = Toplevel()

    label = Label(window, text="Hello World!")
    label.pack(fill='x', padx=50, pady=5)

    button_close = Button(window, text="Close", command=window.destroy)
    button_close.pack(fill='x')

def popup_showinfo():
    instructions  = "Welcome to the worlds worst translator!\n\n"
    instructions += "Enter in a message on the left hand side and "
    instructions += "specify how many languages you wish to parse "
    instructions += "through, then hit translate!"
    showinfo("Instuctions", instructions)

'''
    Opens a file browser to look for .txt to translate
'''
def open_file(user_txtbx): 
    file = askopenfile(mode ='r', initialdir="../Examples", filetypes =[('Text Files', '*.txt')]) 
    if file is not None:
        content = file.read() 
        user_txtbx.delete("1.0", END)
        user_txtbx.insert("1.0", content)
        

'''
    Base program for silly translation
'''
def mainConsole():
    print("------------------------------------")
    print("Welcome to the worst translator ever")
    print("")
    print("[*] Enter \"q\" to quit")
    print("[*] To make text go through more languages, enter \"-n\" and the desired number of languages")
    print("[*] Otherwise enter text to translate")
    print("------------------------------------")

    s = input("[*] Enter number of languages to parse text through: ")
    numLang = int(s)

    while(True):
        
        s = input("-> ")

        if s == "q":
            print("[X] Exiting")
            exit(0)
        elif s[0:2] == "-n":
            numLang = int(s[3:])
            print("[*] New Number is {}".format(numLang))
        else:
            s = correctSpelling(s)
            print("[*] Result: {}".format(ruinSentence(s, numLang)))

'''
    Version of the base program built to run on a GUI
'''
def mainGUI():

    # Initialize window and sizing variables
    window = Tk()
    window.title("Bad Translator")
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window_width = int(screen_width / 2)
    window_height = int(screen_height / 2)
    window.geometry(f'{window_width}x{window_height}')
    window.resizable(False, False)
    window.style = ttk.Style()
    window.style.theme_use("clam")

    # Title widget
    title = Label(window, text="Bad Translator", font=("Helvetica", 82))
    title.place(x=window_width/2, y=window_height/4, anchor="center")

    # Number of languages entry widget and associated label
    lang_num_ent = Entry(window, width = 10)
    lang_num_ent.place(x=window_width*8/50, y=window_height*6/13, anchor="nw")
    lang_num_ent.insert(0, "10")
    lang_num_lbl = Label(window)
    lang_num_lbl.config(text="Total Languages", font=("Helvetica", 13))
    lang_num_lbl.place(x=window_width/50, y=window_height*6/13, anchor="nw")
    
    # Input scrollable textbox widget
    user_txtbx = scrolledtext.ScrolledText(window)
    user_txtbx.config(width=int(window_width/18), height=int(window_height/45))
    user_txtbx.config(wrap=WORD)
    user_txtbx.insert("1.0", "Type a sentence here")
    user_txtbx.place(x=window_width/50, y=window_height*16/30, anchor="nw")

    # Output scrollable textbox widget
    output_txtbx = scrolledtext.ScrolledText(window)
    output_txtbx.config(width=int(window_width/18), height=int(window_height/45))
    output_txtbx.config(wrap=WORD, state=DISABLED)
    output_txtbx.place(x=window_width*53/100, y=window_height*16/30, anchor="nw")

    # Display all parsed languages
    parse_title = Label(window, text="", font=("Helvetica", 10))
    parse_title.config(wraplength=550)
    parse_title.place(x=window_width*7/20, y=window_height*6/15, anchor="nw")
    
    # Translation button widget
    translate_btn = Button(window, text="TRANSLATE")
    translate_btn.config(width = 24, height = 1)
    translate_btn.place(x=window_width/50, y=window_height*6/13, anchor="sw")
    translate_btn.bind("<ButtonRelease-1>", lambda e : translateCallback(lang_num_ent, user_txtbx, output_txtbx, parse_title, window))

    # Instructional popup window
    instruction_btn = Button(window, text="INSTRUCTIONS")
    instruction_btn.place(x=10, y=10, anchor="nw")
    instruction_btn.bind("<ButtonRelease-1>", lambda e : popup_showinfo())

    # Select a txt file instead of typing   
    file_btn = Button(window, text ='Browse Files', command = lambda:open_file(user_txtbx)) 
    file_btn.place(x=window_width/50,y=window_height*59/60, anchor="sw")

    # Launch
    popup_showinfo()
    window.mainloop()

if __name__ == "__main__":
    mainGUI()
