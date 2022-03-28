from googletrans import Translator
import random

t = Translator()
translator = Translator(service_urls=['translate.googleapis.com'])

string = t.translate("Hello", dest="fr").text

print(string)