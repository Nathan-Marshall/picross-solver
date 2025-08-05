def a():
    return d() or b() or d() or b() or c() or d()

def b():
    return c() or d() or c()

def c():
    return True

def d():
    return False


0:(0-0:False or 0-1:(0-1-0:True or 0-1-1:False or 0-1-2:True) or 0-2:False or 0-3:(0-3-0:True or 0-3-1:False or 0-3-2:True) or 0-4:True or 0-5:False)
0 open: draw pre, append(PRE) [] -> [PRE]
    0-0 open: skip identical pre, append(PRE) -> [PRE, PRE]
    0-0 close False: skip unchanged post, pop -> [PRE]

    0-1 open: skip identical pre, append(PRE) -> [PRE, PRE]
        0-1-0 open: skip identical pre, append(PRE) -> [PRE, PRE, PRE]
        0-1-0 close True: *DISPLAY* pre from 0, draw and *DISPLAY* changed post, pop and modify -> [PRE, MODDED]

        0-1-1 open: draw modded pre, append(PRE) -> [PRE, MODDED, PRE]
        0-1-1 close False: skip pre and unchanged post, pop -> [PRE, MODDED]

        0-1-2 open: draw modded pre, append(PRE) -> [PRE, MODDED, PRE]
        0-1-2 close True: *DISPLAY* pre, draw and *DISPLAY* changed post, pop and modify -> [PRE, MODDED]
    0-1 close True: skip pre not drawn at this level, draw and *DISPLAY* post despite not changing from internal display, pop and modify -> [MODDED]


NEW DELAYED POST ALGORITHM:

0:(0-0:False or 0-1:(0-1-0:True or 0-1-1:False or 0-1-2:True) or 0-2:False or 0-3:(0-3-0:True or 0-3-1:False or 0-3-2:True) or 0-4:True or 0-5:False)
0 open: draw pre, append(PRE) [] -> [PRE]
    0-0 open: skip drawing identical pre, append(PRE) -> [PRE, PRE]
    0-0 close False: skip unchanged post, pop -> [PRE]

    0-1 open: skip drawing identical pre, append(PRE) -> [PRE, PRE]
        0-1-0 open: skip drawing identical pre, append(PRE) -> [PRE, PRE, PRE]
        0-1-0 close True: *DISPLAY* pre from 0, draw changed post, pop and modify -> [PRE, MODDED]

        0-1-1 open: draw modded pre, append(PRE) -> [PRE, MODDED, PRE]
        0-1-1 close False: skip displaying pre and unchanged post, pop -> [PRE, MODDED]

        0-1-2 open: draw modded pre, append(PRE) -> [PRE, MODDED, PRE]
        0-1-2 close True: *DISPLAY* post from 0-1-0 and block, then *DISPLAY* pre, draw changed post, pop and modify -> [PRE, MODDED]
    0-1 close True: skip displaying already-displayed pre, redraw post despite not changing from internal display, pop and modify -> [MODDED]

    0-2 open: draw modded pre, append(PRE) -> [MODDED, PRE]
    0-2 close False: skip displaying pre and unchanged post, pop -> [MODDED]

    0-3 open: draw modded pre, append(PRE) -> [MODDED, PRE]
        0-3-0 open: skip drawing identical pre, append(PRE) -> [MODDED, PRE, PRE]
        0-3-0 close True: *DISPLAY* post from 0-1 and block, then *DISPLAY* pre from 0-3, draw changed post, pop and modify -> [MODDED, MODDED]