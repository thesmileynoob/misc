import glob
import csv
from pprint import pprint
from telnetlib import SE
from typing import Tuple

import pdfplumber
import random



PDF_FILE_PATH = "./prediction_data/merit_list.pdf"
CSV_FILE_PATH = "./prediction_data/data.csv"
CATEGORIES = set(
        (
            "SC",
            "NT(B)",
            # "SBC",
            "Unreserved",
            "DT(A)",
            "ST",
            "EWS",
            "NT(D)",
            "OBC",
            "NT(C)",
        )
    )

# "cat": [pwd(aee, ae1, ae2), wrd(aee, ae1, ae2), wcd(ae1, ae2)]
class SeatManager:
    SEATS = {
        "Unreserved": [[2,2,118], [1,8,221], [32,75]],
        "SC": [[1,1,40], [0,2,68], [11,23]],
        "ST": [[0,6,10], [0,1,27], [6,16]],
        "EWS": [[1,0,26], [0,2,55], [8,19]],
        "OBC": [[0,1,47], [4,7,142], [16,35]],
        "DT(A)": [[0,2,6], [0,1,5], [3,6]],
        "NT(B)": [[0,3,10], [1,0,11], [2,5]],
        "NT(C)": [[0,1,5], [1,0,5], [3,7]],
        "NT(D)": [[1,0,1], [0,0,10], [1,4]],
    }

    def __init__(self) -> None:
        self.seats = dict(self.SEATS)

    def get_key(self, post) -> (int, int):
        if post == 'aee pwd':
            return 0, 0,
        if post == 'aee wrd':
            return 1, 0,
        if post == 'ae1 pwd':
            return 0, 1,
        if post == 'ae1 wrd':
            return 1, 1,
        if post == 'ae1 wcd':
            return 2, 0,
        if post == 'ae2 pwd':
            return 0, 2,
        if post == 'ae2 wrd':
            return 1, 2,
        if post == 'ae2 wcd':
            return 2, 1,


    def seats_left(self, cat, post) -> int:
        avail = self.seats[cat]
        k1, k2 = self.get_key(post)
        return avail[k1][k2]


    def allot(self, cat, post) -> (bool, bool):
        # return (alloted[t/f], alloted_different_cat[t/f])
        if cat == 'Unreserved':
            # open wala
            if self.seats_left(cat, post) <= 0:
                return False, False     # Open -> None
            else:
                avail = self.seats[cat]
                k1, k2 = self.get_key(post)
                avail[k1][k2] -= 1
                return True, False      # Open -> Open
     
        else:
            
            # reservation wala
            try_for_open = self.allot('Unreserved', post)   # find an "open" spot

            if try_for_open == True:
                return True, True           # ST -> Open
            
            elif self.seats_left(cat, post) <= 0:
                    return False, False     # ST -> None
            else:
                avail = self.seats[cat]
                k1, k2 = self.get_key(post)
                avail[k1][k2] -= 1
                return True, False          # ST -> ST
     

    def print_seats(self, cat=None):
        if cat:
            pprint((cat, self.seats[cat]))
        else:
            pprint(self.seats)


def extract_data():
    with pdfplumber.open(PDF_FILE_PATH) as pdf:
        print(len(pdf.pages), "pages found.")

        data = []
        unknowns = []
        for page in pdf.pages[:]:  # IMPORTANT!!!!

            # print('***' * 20)
            print("on page:", page.page_number)
            text = page.extract_text()
            text = text.split("\n")[8:][:-1]
            # print('lines:', len(text))
            # pprint(text)

            marks = []
            ranks = []
            cats = []
            rolls = []

            for line in text:
                # print(line)
                # continue
                if len(line.split()) == 5:
                    # marks
                    # print(line, "**MARKS**")
                    m = tuple(int(x) for x in line.split())
                    marks.append(m)
                    continue

                if len(line.split()) == 1 and line.count("-") == 2:
                    # print(line, "**DATE**")
                    continue

                if len(line.split()) > 6:
                    # rank roll name etc
                    splits = line.split()
                    ranks.append(int(splits[0]))
                    rolls.append(splits[1])
                    continue

                if line.strip() in CATEGORIES:
                    cats.append(line)
                    continue

                else:
                    print("UNKNOWN:", line)
                    unknowns.append(line)

            # pprint(list(zip(ranks, rolls, marks)))
            data.extend(zip(ranks, rolls, marks, cats))

        # all done!
        pprint(data)

        # error check
        for d in data:
            if len(d[1]) != 8:
                print("possibly invalid rollnumber!", d)
            if len(d[2]) != 5:
                print("possibly invalid marks!", d)

        # cats = set(d[3] for d in data)
        # print(cats)
        # print(unknowns)

        # write to csv
        with open(CSV_FILE_PATH, "w", newline="") as f:
            writer = csv.writer(f)

            for d in data:
                rank = d[0]
                roll = d[1]
                cat = d[3]
                marks = d[2]
                print(rank, roll, marks)
                writer.writerow((rank, roll, *marks, cat))

            print("DATA WRITTEN TO:", CSV_FILE_PATH)





if __name__ == "__main__":
    # extract_data()

    preferences = [
        'aee pwd', 'aee wrd', # AEE
        'ae1 pwd', 'ae1 wrd', 'ae1 wcd', # AE-1
        'ae2 pwd', 'ae2 wrd', 'ae2 wcd', # AE-2
    ]

    dude = SeatManager()
    
    dude.print_seats()

    # _names =  ['Dude', 'yolo', 'Saki-na-ka', 'Akshay', 'cholo', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'W', 'X', 'Y', 'Z']
    # candidates = list(zip(_names, random.choices(list(CATEGORIES), k=len(_names))))
    # pprint(candidates)

    my_allot = None
    allot_count = 0
    no_seat_count = 0

    with open(CSV_FILE_PATH, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in list(reader):
            candidate = row[1]
            cat = row[7]
            for pref in preferences:
                alloted = dude.allot(cat, pref)
                if alloted:
                    allot_count += 1
                    print(f"Alloted '{pref}' to '{candidate}'")
                    if candidate == 'AU005240':
                        my_allot = pref
                    break
            else:
                no_seat_count += 1
                print(f"No seat for you!", candidate, f"({cat})")


    dude.print_seats()
    print("alloted:", allot_count)
    print("better luck next time:", no_seat_count)
    print("my future is...", my_allot)

    

