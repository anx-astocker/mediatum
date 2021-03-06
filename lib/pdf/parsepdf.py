"""
 mediatum - a multimedia content repository

 Copyright (C) 2007 Arne Seifert <seiferta@in.tum.de>
 Copyright (C) 2007 Matthias Kramm <kramm@in.tum.de>

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys
if __name__ == "__main__":
    sys.path += [sys.argv[1], "../../", "."]

import logging
import random
from PIL import Image, ImageDraw
import logging
import sys
import os

from subprocess import Popen, PIPE, call


class PDFException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class EncryptedException:
    pass


class PDFInfo:

    def __init__(self, data={}):
        self.data = data

    def getInfo(self, name):
        if name in self.data.keys():
            return self.data[name]
        return ""

    def isEncrypted(self):
        if self.getInfo("Encrypted") == "yes":
            return 1
        return 0

    def __getitem__(self, key):
        return self.data[key]

    def items(self):
        return self.data


def parsePDF(filename, tempdir):
    # process info file
    def parseInfo(lines):
        attrs = ["Title", "Subject", "Keywords", "Author", "Creator", "Producer", "CreationDate", "ModDate",
                 "Tagged", "Pages", "Encrypted", "Page size", "File size", "Optimized", "PDF Version", "Metadata"]
        data = {}
        for line in lines:
            for attr in attrs:
                parts = line.replace("\n", "").replace("\r", "").split(attr + ":")
                if len(parts) == 2:
                    data[attr] = parts[1].strip()

                    if attr == "Encrypted" and parts[1].strip().startswith("yes"):
                        for s_option in parts[1].strip()[5:-1].split(" "):
                            option = s_option.split(":")
                            if option[1] == "":
                                break
                            data[option[0]] = option[1]
                        data[attr] = "yes"
                    break
        return PDFInfo(data)

    name = ".".join(filename.split(".")[:-1])
    imgfile = tempdir + "tmp" + str(random.random()) + ".png"
    thumb128 = name + ".thumb"
    thumb300 = name + ".thumb2"
    fulltext = name + ".txt"
    infoname = name + ".info"

    # pdf info (xpdf)
    p = Popen(("pdfinfo -meta %s" % filename).split(" "), stdout=PIPE)
    info = parseInfo(p.communicate()[0].strip().split("\n"))

    # test for correct rights
    if info.isEncrypted():
        raise PDFException("error:document encrypted")

    finfo = open(infoname, "w")
    for item in info.items():  # infokeys:
        finfo.write(item + ":" + (" " * (15 - len(item)) + info[item] + "\n"))
    finfo.close()

    # convert first page to image (imagemagick + ghostview)
    os.system("convert -alpha off -colorspace RGB %s[0] -background white -thumbnail x300  %s" % (filename, imgfile))
    makeThumbs(imgfile, thumb128, thumb300)

    # extract fulltext (xpdf)
    os.system("pdftotext -enc UTF-8 %s %s" % (filename, fulltext))
    os.remove(imgfile)


def parsePDF2(filename, tempdir):
    from core.config import basedir
    retcode = call([sys.executable, os.path.join(basedir, "lib/pdf/parsepdf.py"), filename, tempdir])
    if retcode == 111:
        raise PDFException("error:document encrypted")
    elif retcode == 1:  # normal run
        pass


"""  create preview image for given pdf """


def makeThumbs(src, thumb128, thumb300):
    pic = Image.open(src)
    pic.load()
    pic = pic.convert("RGB")
    width = pic.size[0]
    height = pic.size[1]

    if width > height:
        newwidth, newheight = 300, height * 300 / width
    else:
        newwidth, newheight = width * 300 / height, 300

    pic = pic.resize((newwidth, newheight), Image.ANTIALIAS)
    im = Image.new("RGB", (300, 300), (255, 255, 255))
    x = (300 - newwidth) / 2
    y = (300 - newheight) / 2
    im.paste(pic, (x, y, x + newwidth, y + newheight))
    draw = ImageDraw.ImageDraw(im)
    draw.line([(x, y), (x + newwidth, y), (x + newwidth, y + newheight), (x, y + newheight), (x, y)], (200, 200, 200))

    draw.line([(0, 0), (299, 0), (299, 299), (0, 299), (0, 0)], (128, 128, 128))
    im.save(thumb300, "jpeg")

    im = im.resize((128, 128), Image.ANTIALIAS)
    draw = ImageDraw.ImageDraw(im)
    draw.line([(0, 0), (127, 0), (127, 127), (0, 127), (0, 0)], (128, 128, 128))
    im.save(thumb128, "jpeg")


if __name__ == "__main__":
    import sys
    try:
        import signal
        signal.alarm(600)  # try processing the file for 10 minutes - then abort
    except:
        pass
    try:
        parsePDF(sys.argv[1], sys.argv[2])

    except PDFException, e:
        sys.exit(111)
