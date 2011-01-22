# -*- coding: utf-8 -*-

#    This file is part of Mumoro.
#
#    Mumoro is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Mumoro is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Mumoro.  If not, see <http://www.gnu.org/licenses/>.
#
#    © Université de Toulouse 1 2010
#    Author: Tristram Gräbener, Odysseas Gabrielides

import re
import hashlib

def md5_of_file(filename):
    block_size=2**20
    md5 = hashlib.md5()
    while True:
        data = filename.read(block_size)
        if not data:
            break
        md5.update(data)
    filename.close()
    return md5.hexdigest()

def valid_color_p( color ):
    return re.search("^#([0-9]|[a-f]|[A-F]){6}$", color)
