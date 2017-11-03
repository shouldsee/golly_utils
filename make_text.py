import golly as g
from glife import *
from glife.text import make_text
t=g.getstring('what text?',g.getclipstr())
make_text(t).put(-50,-50)