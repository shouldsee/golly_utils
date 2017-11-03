import golly
import webbrowser

rule=golly.getrule().split(':')[0];
qrule=rule.replace('/','').lower();

webbrowser.open('http://fano.ics.uci.edu/ca/rules/{}/'.format(qrule)); 