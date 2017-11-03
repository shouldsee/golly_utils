import golly
import webbrowser

rule=golly.getrule().split(':')[0];
qrule=rule.replace('/','').lower();

webbrowser.open('https://catagolue.appspot.com/census/{}/'.format(qrule)); 