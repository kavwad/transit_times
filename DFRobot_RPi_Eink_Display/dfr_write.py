import os
from .DFRobot_RPi_Eink_Display import DFRobot_RPi_Eink_Display

# Use a relative path for the font file
fontFilePath = os.path.join(os.path.dirname(__file__), 'resources', 'NotoMono-Regular.ttf')

def initialize_display():
    try:
        return DFRobot_RPi_Eink_Display(0, 0, 27, 17, 4, 26)
    except Exception as e:
        print(f"Error initializing display: {e}")
        return None

def dfr_write(lines):
    eink_display = initialize_display()
    if not eink_display:
        print("Failed to initialize display. Cannot write.")
        return

    eink_display.begin()
    eink_display.clear_screen()

    ft = DFRobot_RPi_Eink_Display.FreetypeHelper(fontFilePath)
    ft.set_dis_lower_limit(48)
    eink_display.set_ex_fonts(ft)
    eink_display.set_text_format(1, eink_display.BLACK, eink_display.WHITE, 1, 1)
    eink_display.set_ex_fonts_fmt(13, 13)

    for line in lines:
        eink_display.flush(eink_display.PART)
        eink_display.print_str_ln(line)
        print(line)

    # Cleanup
    del eink_display
