#!/usr/bin/env python
#
# Copyright 2010 Map Of Life
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from google.appengine.api import images, memcache
from google.appengine.ext import db
from mapreduce import operation as op
from mol.db import Tile, TileUpdate
import cStringIO
import png

def delete(entity):
    """Deletes the entity from the datastore."""
    #if len(entity.key().name().split('/')[1]) < 6:
    yield op.db.Delete(entity)


def interpolate(entity):
    """Processes any changed tiles

    description

    Args:
      entity: A TileUPdate entity
    """
    key = entity.key().name()
    delList = []
    tile = Tile.get_by_key_name(key)
    fullStart = False
    if tile: #if it does exist, turn it into a binary 256x256 matrix
        n = []
        row = 0
        try:
            tmp = str(tile.band)
        except:
            tmp = 0
        if cmp(tmp, 'f') == 0:
            fullStart = True
            n = [[255 if (i + 1) % 4 == 0 else 0 for i in range(256 * 4)] for i in range(256)]
        else:
            for s in png.Reader(bytes=tile.band).asRGBA8()[2]:
                n.append(list(s))
    else: #if tile doesn't exist, create 256x256 matrix
        n = [[0 for i in range(256 * 4)] for i in range(256)]
        tile = Tile(key=db.Key.from_path('Tile', key))

    fullCt = 0
    qtCt = 0
    mod = False
    for qt in range(4): #cycle through each of the four higher resolution tiles that make up this single tile
        tmpK = key.split("/")
        tmpK[1] = tmpK[1] + str(qt)
        tmpK = '/'.join(tmpK)
        band = None
        band = memcache.get("tile-%s" % tmpK)
        if band is None:
            t = Tile.get(db.Key.from_path('Tile', tmpK))
            if t is not None:
                band = t.band

        orow = 0 if qt in [0, 1] else 128 #row offset if the tile is either sub-quadtree 1,3
        ocol = 0 if qt in [0, 2] else 128 #col offset if the tile is either sub-quadtree 2,3
        if band:
            mod = True
            qtCt += 1
            try:
                tmp = str(band)
            except:
                tmp = 0
            if cmp(tmp, 'f') == 0: #represents a full tile
                fullCt += 1
                row = 0
                while row < 128:
                    n[row + orow][4 * ocol:4 * (ocol + 128)] = [255 if (i + 1) % 4 == 0 else 0 for i in range(128 * 4)]
                    row += 1
            else:
                poss = []
                row = 0
                for s in png.Reader(bytes=images.resize(band, 128, 128)).asRGBA8()[2]: #iterate through each of the 128 rows of the tile
                    n[row + orow][4 * ocol:4 * (ocol + 128)] = list(s)
                    row += 1

    yield op.db.Delete(db.Key.from_path('TileUpdate', key)) #delete the sub-tiles from the TileUpdates table

    if mod:
        fullTile = False
        if fullCt == 4:
            fullTile = True
        elif fullStart is True and qtCt == fullCt:
            fullTile = True

        if fullTile:
            tile.band = 'f'
        else:
            f = cStringIO.StringIO()
            w = png.Writer(256, 256, planes=4, alpha=True, greyscale=False, bitdepth=8)
            #w.write_array(f,n)
            w.write_passes(f, n, packed=False)
            tile.band = db.Blob(f.getvalue())
            f.close()

        yield op.db.Put(tile)

        tmpK = key.split("/")
        tmpK[1] = tmpK[1][0:-1]
        zoom = len(str(tmpK[1]))
        tmpK = '/'.join(tmpK)

        if zoom > 0:
            update = TileUpdate(key=db.Key.from_path('TileUpdate', tmpK))
            update.zoom = zoom
            yield op.db.Put(update)
