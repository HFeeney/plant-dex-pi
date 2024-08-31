import json
import sys
import os
import plant_record
from blessed import Terminal

term = Terminal()

# returns a list of all plant records stored in the file system
def load_records():
    res = []
    # iterate through the files of the records directory, converting the json to real
    # plant records
    plant_dir = os.path.join(os.path.dirname(__file__), "records")
    for plant_json in os.scandir(plant_dir):
        with open(plant_json) as file:
            plant = json.load(file)
            res.append(plant_record.Record(
                    plant["name"],
                    plant["img"],
                    plant["info"],
                    plant["msgid"]
                ))
    return res

def display_img(img_name, img_h):
    if img_h < 0:
        return

    img_path = os.path.join(plant_record.IMG_SAVE_DIR, img_name)
    img_w, rows = os.get_terminal_size()

    if img_h < img_w:
        os.system(f'viu -h {img_h} "{img_path}"')
    else:
        os.system(f'viu -w {img_w} "{img_path}"')

class MenuScreen:
    def __init__(self, records):
        self.selected = 0
        # window size is based on terminal size and number of records
        self.window_size = max(min((len(records), term.height - 5)), 0)
        self.window_start = 0
        self.records = records

    def update(self, key):
        self.window_size = max(min((len(self.records), term.height - 5)), 0)
        if key == 'l' or key == term.KEY_RIGHT:
            return PlantScreen(self.records, self.selected)
        elif key == 'q':
            exit()

        # navigating upwards at the top of the window or downwards at the
        # bottom slides the window
        if key == 'k' or key == term.KEY_UP:
            if self.selected == self.window_start:
                self.window_start -= 1
            self.selected -= 1
        elif key == 'j' or key == term.KEY_DOWN:
            bot_idx = (self.window_start + self.window_size - 1) % len(self.records)
            if self.selected == bot_idx:
                self.window_start += 1
            self.selected += 1

        self.window_start %= len(self.records) 
        self.selected %= len(self.records) 
        return self

    def display(self):
        # the display looks something like the following
        """
        plant-dex

            ^
            clematis
         -> rhododendron
            daisy
            holley hock
            v
        """
        print('plant-dex')
        print('')
        print('   ^')
        for i in range(self.window_size):
            plant_idx = (self.window_start + i) % len(self.records)
            plant = self.records[plant_idx]
            if plant_idx == self.selected:
                print(' -> %s' % plant.name)
            else:
                print('    %s' % plant.name)
        print('   v')

class PlantScreen:
    def __init__(self, records, idx):
        self.records = records
        self.idx = idx

    def update(self, key):
        if key == 'q':
            return MenuScreen(self.records)
        return self

    def display(self):
        # display name, info, and use viu to display image
        plant = self.records[self.idx]
        print('name: %s' % plant.name)
        print('info: %s' % plant.info)
        display_img(plant.img, term.height - term.get_location()[0] - 1)

def program():
    # load in plants
    records = load_records()
    # track current screen (menu, plant)
    screen = MenuScreen(records)
    # track user input
    key = ''
    while True: 
        screen = screen.update(key)
        print(term.home + term.clear, end='')
        screen.display()
        key = term.inkey() # blocks

with term.fullscreen(), term.hidden_cursor(), term.cbreak():
    program()
