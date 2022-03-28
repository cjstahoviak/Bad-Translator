import googletrans as g
import re
import random

print("------------------------------------")
print("Welcome to the worst translator ever")
print("")
print("[*] Enter \"q\" to quit")
print("[*] To make text go through more languages, enter \"-n\" and the desired number of languages")
print("[*] Otherwise enter text to translate")
print("------------------------------------")

allLanguages = len(g.LANGUAGES)

t = g.Translator()

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


s = input("[*] Enter number of languages to parse text through: ")

changeNumLang = False

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

        print("[*] Result: {}".format(ruinSentence(s, numLang)))
