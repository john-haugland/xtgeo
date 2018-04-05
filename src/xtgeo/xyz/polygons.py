# -*- coding: utf-8 -*-
"""XTGeo xyz.polygons module, which contains the Polygons class."""

# For polygons, the order of the points sequence is important. In
# addition, a Polygons dataframe _must_ have a columns called 'POLY_ID'
# which identifies each polygon piece.

from __future__ import print_function, absolute_import
import pandas as pd

import xtgeo
from xtgeo.xyz import XYZ
from xtgeo.xyz._xyz_io import _convert_idbased_xyz

xtg = xtgeo.common.XTGeoDialog()
logger = xtg.functionlogger(__name__)


class Polygons(XYZ):
    """Class for a polygons (connected points) in the XTGeo framework.

    The term Polygons is hereused in a wider context, as it includes
    polylines that do not connect into closed polygons. A Polygons
    instance may contain several polylines/polygons, which are
    identified by POLY_ID

    The polygons are stored in Python as a Pandas dataframe, which
    allow for flexible manipulation and fast execution.

    A Polygons instance will have 4 mandatory columns:

    * X_UTME - for X UTM coordinate (Easting)
    * Y_UTMN - For Y UTM coordinate (Northing)
    * Z_TVDSS - For depth or property from mean SeaLevel; Depth positive down
    * POLY_ID - for polygon ID as there may be several polylines segments

    It is important that these column names are unique and protected.
    """

    def __init__(self, *args, **kwargs):

        super(Polygons, self).__init__(*args, **kwargs)

        self._ispolygons = True

    @property
    def nrow(self):
        """ Returns the Pandas dataframe object number of rows"""
        if self._df is None:
            return 0
        else:
            return len(self._df.index)

    @property
    def dataframe(self):
        """ Returns or set the Pandas dataframe object"""
        return self._df

    @dataframe.setter
    def dataframe(self, df):
        self._df = df.copy()

    def from_file(self, pfile, fformat='xyz'):
        """Import Polygons from a file.

        Supported import formats (fformat):

        * 'xyz' or 'poi' or 'pol': Simple XYZ format

        * 'zmap': ZMAP line format as exported from RMS (e.g. fault lines)

        * 'guess': Try to choose file format based on extension

        Args:
            pfile (str): Name of file
            fformat (str): File format, see list above

        Returns:
            Object instance (needed optionally)

        Raises:
            OSError: if file is not present or wrong permissions.

        """

        super(Polygons, self).from_file(pfile, fformat=fformat)

        # for polygons, a seperate column with POLY_ID is required; however this may
        # lack if the input is on XYZ format

        if 'POLY_ID' not in self._df.columns:
            self._df['POLY_ID'] = self._df.isnull().all(axis=1).cumsum().dropna()
            self._df.dropna(axis=0, inplace=True)
            self._df.reset_index(inplace=True, drop=True)

    def to_file(self, pfile, fformat='xyz', attributes=None, filter=None,
                wcolumn=None, hcolumn=None, mdcolumn=None):
        """Export Polygons to file.

        Args:
            pfile (str): Name of file
            fformat (str): File format xyz/poi/pol / rms_attr /rms_wellpicks
            attributes (list): List of extra columns to export (some formats)
            filter (dict): Filter on e.g. top name(s) with keys TopName
                or ZoneName as {'TopName': ['Top1', 'Top2']}
            wcolumn (str): Name of well column (rms_wellpicks format only)
            hcolumn (str): Name of horizons column (rms_wellpicks format only)
            mdcolumn (str): Name of MD column (rms_wellpicks format only)

        Returns:
            Number of points exported

        Note that the rms_wellpicks will try to output to:

        * HorizonName, WellName, MD  if a MD (mdcolumn) is present,
        * HorizonName, WellName, X, Y, Z  otherwise

        Raises:
            KeyError if filter is set and key(s) are invalid

        """



        super(Polygons, self).to_file(pfile, fformat=fformat,
                                      attributes=attributes, filter=filter,
                                      wcolumn=wcolumn, hcolumn=hcolumn,
                                      mdcolumn=mdcolumn)

    def from_wells(self, wells, zone, resample=1):

        """Get line segments from a list of wells and a zone number

        Args:
            wells (list): List of XTGeo well objects
            zone (int): Which zone to apply
            resample (int): If given, resample every N'th sample to make
                polylines smaller in terms of bit and bytes.
                1 = No resampling.

        Returns:
            None if well list is empty; otherwise the number of wells that
            have one or more line segments to return

        Raises:
            Todo
        """

        if len(wells) == 0:
            return None

        dflist = []
        maxid = 0
        for well in wells:
            wp = well.get_zone_interval(zone, resample=resample)
            if wp is not None:
                # as well segments may have overlapping POLY_ID:
                wp['POLY_ID'] += maxid
                maxid = wp['POLY_ID'].max() + 1
                dflist.append(wp)

        if len(dflist) > 0:
            self._df = pd.concat(dflist, ignore_index=True)
            self._df.reset_index(inplace=True, drop=True)
        else:
            return None

        return len(dflist)

    def get_xyz_dataframe(self):
        """Convert from POLY_ID based to XYZ, where a new polygon is marked
        with a 999.0 value as flag"""

        logger.info(self.dataframe)

        return _convert_idbased_xyz(self.dataframe)
