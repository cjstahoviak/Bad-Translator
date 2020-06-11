import googletrans as g
import re
import random
from spellchecker import SpellChecker
 
spell = SpellChecker(language='en')
allLanguages = len(g.LANGUAGES)
t = g.Translator()

print("------------------------------------")
print("Welcome to the worst translator ever")
print("")
print("[*] Enter \"q\" to quit")
print("[*] To make text go through more languages, enter \"-n\" and the desired number of languages")
print("[*] Otherwise enter text to translate")
print("------------------------------------")

# Absolutley destroys your english
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

def CorrectSpelling(string):
    words = spell.split_words(string)
    [spell.correction(word) for word in words]
    string = ''.join(string)

    print("After fix")
    print(string)
    return string

def main():
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
            s = CorrectSpelling(s)
            print("[*] Result: {}".format(ruinSentence(s, numLang)))

if __name__ == "__main__":
    main()
