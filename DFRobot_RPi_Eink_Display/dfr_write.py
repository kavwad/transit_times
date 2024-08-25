from DFRobot_RPi_Eink_Display import DFRobot_RPi_Eink_Display

fontFilePath = '/home/kavwad/Documents/DFRobot_RPi_Eink_Display/resources/NotoMono-Regular.ttf'
eink_display = DFRobot_RPi_Eink_Display(0, 0, 27, 17, 4, 26)


def write(lines):
    eink_display.begin()
    eink_display.clear_screen()

    ft = DFRobot_RPi_Eink_Display.FreetypeHelper(fontFilePath)
    # set display lower limit, adjust this to effect fonts color depth
    ft.set_dis_lower_limit(48)
    eink_display.set_ex_fonts(ft)  # init with fonts file
    eink_display.set_text_format(
        1, eink_display.BLACK, eink_display.WHITE, 1, 1)
    # set extension fonts width and height
    eink_display.set_ex_fonts_fmt(13, 13)

    for line in lines:
        eink_display.flush(eink_display.PART)
        eink_display.print_str_ln(line)
        print(line)

    # eink_display.bitmap_file(0, 0, 'resources/images/muni.bmp')
