from typing import Dict
import PyPDF2
import glob
import csv
import common
from hashlib import md5
import os

from datetime import datetime


"""
http://www.verypdf.com/pdfinfoeditor/pdf-date-format.htm

>>  D:YYYYMMDDHHmmSSOHH'mm'

O is the seperator (-, + or Z)
"""


_DOWNLOAD_PATH = "pdfinfo_data/"  # store downloaded urls here
_DBFILE = "pdfinfo_data/db.csv"


HEADER = (
    "row",
    "creation_date",
    "mod_date",
    "title",
    "author",
    "creator",
    "filepath",
    "url",
)


def _get_cached(url: str):
    try:
        os.stat(_DBFILE)
    except FileNotFoundError as e:
        return None

    with open(_DBFILE, "r", encoding="utf-8", newline="") as f:
        csv_reader = csv.DictReader(f, HEADER)
        next(csv_reader)
        for row in csv_reader:
            if url == row["url"]:
                return row
    return None


def save_info_to_db(info):

    # check if db exists
    try:
        os.stat(_DBFILE)
    except FileNotFoundError as e:
        # create db file
        with open(_DBFILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, HEADER)
            writer.writeheader()

    with open(_DBFILE, "a+", encoding="utf-8", newline="") as f:
        f.seek(0, 0)  # Beginning
        rowcount = len(f.readlines())
        f.seek(0, 2)  # EOF

        info["row"] = rowcount + 1
        csv.DictWriter(f, HEADER, extrasaction="ignore").writerow(info)


def _download_pdf(url: str) -> (str, bool):
    """Download pdf at url and return its stored path.
        return storedpath, errorstring
    """

    name = md5(url.encode("utf-8")).hexdigest() + ".pdf"
    dlpath = _DOWNLOAD_PATH + name

    # check if already downloaded
    try:
        os.stat(dlpath)
        print("pdf previously downloaded url:", url)

    except FileNotFoundError as e:
        print("trying to download pdf at url:", url, "...")
        common.download_file(url, dlpath)
        print("success! saved at:", dlpath)

    if is_valid_pdf(dlpath):
        return dlpath, ''
    else:
        print(dlpath, 'doesnt seem like a valid pdf')
        return None, f"'{dlpath}' doesn't seem like a valid pdf"

def get_pdf_metadata(url):

    # check in cache
    info = _get_cached(url)
    if info:
        print("[cached]", url)
        info["_cached"] = True
        return info

    # download
    try:
        path, err = _download_pdf(url)
    except Exception as e:
        print("COULDNT DOWNLOAD PDF: ", url)
        print(e)
        return {'error': 'couldnt download pdf:' + repr(e), 'url': url}

    if err or not path:
        return {'error': err, 'url': url}

    info, err = _parse_pdf_metadata(path)

    if err:
        return {'error': info['_error_msg'], 'url': url}

    info["url"] = url
    save_info_to_db(info)

    return info


def _parse_date_str(date_str: str) -> datetime:

    date_str = date_str.strip("D:")  # remove leading 'D:'

    for sep in ["-", "+", "Z"]:
        if sep in date_str:
            date_str = date_str.split(sep)[0]
            break

    return datetime.strptime(date_str, "%Y%m%d%H%M%S")


def is_valid_pdf(filepath) -> bool:
    try:
        with open(filepath, "rb") as fp:
            PyPDF2.PdfFileReader(fp).getDocumentInfo()
            return True

    except OSError as e:
        # occurs if file is not a pdf
        print("file is not a valid pdf:", filepath)
        print(repr(e))
    except Exception as e:
        print("Error for file:", filepath)
        print(repr(e))
    return False



def _parse_pdf_metadata(filepath) -> (dict, bool):
    # return pdf_info, bool(error)

    pdf_data = {
        "creation_date": "",
        "mod_date": "",
        "title": "",
        "author": "",
        "creator": "",
        "filepath": "",
        "_error_msg": "",
        "_log": "",
    }

    try:
        with open(filepath, "rb") as fp:

            pdf = PyPDF2.PdfFileReader(fp)
            info = pdf.getDocumentInfo()

            pdf_data["author"] = info.get("/Author", "")
            pdf_data["creator"] = info.get("/Creator", "")
            pdf_data["title"] = info.get("/Title", "")
            pdf_data["filepath"] = filepath

            crn_str = info.get("/CreationDate", "")
            if crn_str:
                date = _parse_date_str(crn_str)
                # pdf_data["creation_date"] = date.strftime("%d-%m-%Y (%H:%M)")
                pdf_data["creation_date"] = date.strftime("%d-%m-%Y")

            mod_str = info.get("/ModDate", "")
            if mod_str:
                date = _parse_date_str(mod_str)
                # pdf_data["mod_date"] = date.strftime("%d-%m-%Y (%H:%M)")
                pdf_data["mod_date"] = date.strftime("%d-%m-%Y")

            return pdf_data, False

    except Exception as e:
        print('ERROR while parsing pdf:', filepath)
        print(repr(e))
        pdf_data["_error_msg"] = filepath + ': ' + repr(e)

        return pdf_data, True


def test():
    for path in glob.glob("test_data/*.pdf"):
        print(get_pdf_metadata(path))


if __name__ == "__main__":

    with open(_DBFILE, "r", newline="") as f:
        csv_reader = csv.reader(f)
        header = next(csv_reader)  # skip first row
        for row in csv_reader:
            print(row)
