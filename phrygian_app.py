import webview
import os
import sys

def get_base():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    base = get_base()
    html_path = os.path.join(base, 'index.html')
    url = 'file:///' + html_path.replace('\\', '/')
    window = webview.create_window(
        'Chord.Rocks - Offline',
        url,
        width=1400,
        height=900,
        resizable=True
    )
    webview.start()
