#!/usr/bin/env python3
import sys, os
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)
    sys.path.insert(0, os.path.dirname(sys.executable))

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('--gui', '--tui'):
        if sys.argv[1] == '--gui':
            from cachy_game_optimizer.gui import main as gui_main
            return gui_main()
        else:
            from cachy_game_optimizer.main import main as tui_main
            return tui_main()
    else:
        from cachy_game_optimizer.cli import main as cli_main
        if len(sys.argv) == 1:
            sys.argv = ['cgo', 'help']
        elif sys.argv[0].endswith(('cachy-game-optimizer', 'cachy-game-optimizer.AppImage')):
            sys.argv = ['cgo'] + sys.argv[1:]
        return cli_main()

if __name__ == '__main__':
    sys.exit(main())
