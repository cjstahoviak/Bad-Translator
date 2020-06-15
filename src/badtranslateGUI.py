import googletrans as g
import re
import random
from spellchecker import SpellChecker
from tkinter import *
from tkinter import scrolledtext 

spell = SpellChecker(language='en')
allLanguages = len(g.LANGUAGES)
t = g.Translator()

'''
    Absolutley destroys your english
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
def translateCallback(num_ent, input_txtbx, output_txtbx):
    print("Callback activated")

    # Clear the output text of the previoius translation
    output_txtbx.delete("1.0", END)
    
    # Grab whatever the user typed in and spell check
    user_input = input_txtbx.get("1.0",END)
    user_input = correctSpelling(user_input)

    # Put the the translation in the output box
    translated = ruinSentence(user_input, int(num_ent.get()))
    output_txtbx.insert("1.0", translated)

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
    showinfo("ShowInfo", "Hello World!")

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

    # Title widget
    title = Label(window, text="Bad Translator", font=("Helvetica", 82))
    title.place(x=window_width/2, y=window_height/4, anchor="center")

    # Number of languages entry widget and associated label
    lang_num_ent = Entry(window, width = 10)
    lang_num_ent.place(x=window_width/2, y=window_height*6/13, anchor="nw")
    lang_num_ent.insert(0, "10")
    lang_num_lbl = Label(window)
    lang_num_lbl.config(text="Total Languages", font=("Helvetica", 12))
    lang_num_lbl.place(x=window_width/2, y=window_height*6/13, anchor="ne")
    
    # Input scrollable textbox widget
    user_txtbx = scrolledtext.ScrolledText(window)
    user_txtbx.config(width=int(window_width/18), height=int(window_height/40))
    user_txtbx.place(x=window_width/50, y=window_height*16/30, anchor="nw")

    # Output scrollable textbox widget
    output_txtbx = scrolledtext.ScrolledText(window)
    output_txtbx.config(width=int(window_width/18), height=int(window_height/40))
    output_txtbx.place(x=window_width*53/100, y=window_height*16/30, anchor="nw")
    
    # Translation button widget
    translate_btn = Button(window, text="TRANSLATE")
    translate_btn.place(x=window_width/2, y=window_height*6/13, anchor="s")
    translate_btn.bind("<ButtonRelease-1>", lambda e : translateCallback(lang_num_ent, user_txtbx, output_txtbx))

    # Instructional popup window


    # Launch
    window.mainloop()

if __name__ == "__main__":
    mainGUI()
