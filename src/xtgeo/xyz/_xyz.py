# -*- coding: utf-8 -*-
"""XTGeo xyz module (abstract class)"""

from __future__ import print_function, absolute_import

import abc
import os.path
from collections import OrderedDict
from copy import deepcopy

import six
import pandas as pd

import xtgeo
from xtgeo.common import XTGeoDialog, XTGDescription
from xtgeo.xyz import _xyz_io
from xtgeo.xyz import _xyz_roxapi
import xtgeo.common.sys as xtgeosys

xtg = XTGeoDialog()
logger = xtg.functionlogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class XYZ(object):
    """Abstract Base class for Points and Polygons in XTGeo, but with
    concrete methods."""

    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        """Initiate instance"""

        self._df = None
        self._ispolygons = False
        self._xname = "X_UTME"
        self._yname = "Y_UTMN"
        self._zname = "Z_TVDSS"
        self._pname = "POLY_ID"
        self._mname = "M_MDEPTH"
        self._filesrc = None
        # other attributes name: type, where type is
        # ~ ('str', 'int', 'float', 'bool')
        self._attrs = OrderedDict()

        if len(args) == 1:
            if isinstance(args[0], str):
                # make instance from file import
                pfile = args[0]
                logger.info("Instance from file")
                fformat = kwargs.get("fformat", "guess")
                self.from_file(pfile, fformat=fformat)

            if isinstance(args[0], list):
                # make instance from a list of 3 or 4 tuples
                plist = args[0]
                logger.info("Instance from list")
                self.from_list(plist)

        logger.info("XYZ Instance initiated (base class) ID %s", id(self))

    @abc.abstractmethod
    def copy(self, stype):
        """Returns a a deep copy of an instance"""

        if stype == "polygons":
            mycopy = xtgeo.Polygons()
        else:
            mycopy = xtgeo.Points()
        mycopy._df = self._df.copy()
        mycopy._ispolygons = self._ispolygons
        mycopy._xname = self._xname
        mycopy._yname = self._yname
        mycopy._zname = self._zname
        mycopy._pname = self._pname
        mycopy._mname = self._mname
        mycopy._filescr = self._filesrc = None
        mycopy._attrs = deepcopy(self._attrs)

        return mycopy

    @abc.abstractmethod
    def describe(self, flush=True):
        """Describe an instance by printing to stdout"""

        dsc = XTGDescription()
        dsc.title("Description of {} instance".format(self.__class__.__name__))
        dsc.txt("Object ID", id(self))
        dsc.txt("xname, yname, zname", self._xname, self._yname, self._zname)

        if flush:
            dsc.flush()
            return None

        return dsc.astext()

    # ==================================================================================
    # Import and export
    # ==================================================================================

    @abc.abstractmethod
    def from_file(self, pfile, fformat="guess"):
        """Import Points or Polygons from a file.

        Supported import formats (fformat):

        * 'xyz' or 'poi' or 'pol': Simple XYZ format

        * 'zmap': ZMAP line format as exported from RMS (e.g. fault lines)

        * 'rms_attr': RMS points formats with attributes (extra columns)

        * 'guess': Try to choose file format based on extension

        Args:
            pfile (str): Name of file
            fformat (str): File format, see list above

        Returns:
            Object instance (needed optionally)

        Raises:
            OSError: if file is not present or wrong permissions.

        """

        logger.info("Reading from file %s...", pfile)

        if not os.path.isfile(pfile):
            msg = "Does file exist? [{}]".format(pfile)
            logger.critical(msg)
            raise IOError(msg)

        froot, fext = os.path.splitext(pfile)
        if fformat == "guess":
            if not fext:
                logger.critical("File extension missing. STOP")
                raise SystemExit

            fformat = fext.lower().replace(".", "")

        if fformat in ["xyz", "poi", "pol"]:
            _xyz_io.import_xyz(self, pfile)
        elif fformat == "zmap":
            _xyz_io.import_zmap(self, pfile)
        elif fformat in ("rms_attr", "rmsattr"):
            _xyz_io.import_rms_attr(self, pfile)
        else:
            logger.error("Invalid file format (not supported): %s", fformat)
            raise SystemExit

        logger.info("Reading from file %s... done", pfile)
        logger.debug("Dataframe head:\n%s", self._df.head())
        self._filesrc = pfile

        return self

    @abc.abstractmethod
    def from_list(self, plist):
        """Import Points or Polygons from a list.

        [(x1, y1, z1, <id1>), (x2, y2, z2, <id2>), ...]

        It is currently not much error checking that lists/tuples are consistent, e.g.
        if there always is either 3 or 4 elements per tuple, or that 4 number is
        an integer.

        Args:
            plist (str): List of tuples, each tuple is length 3 or 4

        Raises:
            ValueError: If something is wrong with input

        .. versionadded: 2.6
        """

        first = plist[0]
        if len(first) == 3:
            self._df = pd.DataFrame(
                plist, columns=[self._xname, self._yname, self._zname]
            )

        elif len(first) == 4:
            self._df = pd.DataFrame(
                plist, columns=[self._xname, self._yname, self._zname, self._pname]
            )
        else:
            raise ValueError(
                "Wrong length detected of first tuple: {}".format(len(first))
            )

    @abc.abstractmethod
    def to_file(
        self,
        pfile,
        fformat="xyz",
        attributes=False,
        pfilter=None,
        filter=None,  # deprecated, not in use (only signature)
        wcolumn=None,
        hcolumn=None,
        mdcolumn="M_MDEPTH",
    ):  # pylint: disable=redefined-builtin
        """Export XYZ (Points/Polygons) to file.

        Args:
            pfile (str): Name of file
            fformat (str): File format xyz/poi/pol / rms_attr /rms_wellpicks
            attributes (bool or list): List of extra columns to export (some formats)
                or True for all attributes present
            pfilter (dict): Filter on e.g. top name(s) with keys TopName
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
            KeyError if pfilter is set and key(s) are invalid

        """
        xtgeosys.check_folder(pfile, raiseerror=OSError)

        if self.dataframe is None:
            ncount = 0
            logger.warning("Nothing to export!")
            return ncount

        if fformat is None or fformat in ["xyz", "poi", "pol"]:
            # NB! reuse export_rms_attr function, but no attributes
            # are possible
            ncount = _xyz_io.export_rms_attr(
                self, pfile, attributes=False, pfilter=pfilter
            )

        elif fformat == "rms_attr":
            ncount = _xyz_io.export_rms_attr(
                self, pfile, attributes=attributes, pfilter=pfilter
            )
        elif fformat == "rms_wellpicks":
            ncount = _xyz_io.export_rms_wpicks(
                self, pfile, hcolumn, wcolumn, mdcolumn=mdcolumn
            )

        if ncount is None:
            ncount = 0

        if ncount == 0:
            logger.warning("Nothing to export!")

        return ncount

    @abc.abstractmethod
    def from_roxar(
        self, project, name, category, stype="horizons", realisation=0, attributes=False
    ):
        """Load a points/polygons item from a Roxar RMS project.

        The import from the RMS project can be done either within the project
        or outside the project.

        Note that a shortform (for polygons) to::

          import xtgeo
          mypoly = xtgeo.xyz.Polygons()
          mypoly.from_roxar(project, 'TopAare', 'DepthPolys')

        is::

          import xtgeo
          mysurf = xtgeo.polygons_from_roxar(project, 'TopAare', 'DepthPolys')

        Note also that horizon/zone/faults name and category must exists
        in advance, otherwise an Exception will be raised.

        Args:
            project (str or special): Name of project (as folder) if
                outside RMS, og just use the magic project word if within RMS.
            name (str): Name of polygons item
            category (str): For horizons/zones/faults: for example 'DL_depth'
                or use a folder notation on clipboard.

            stype (str): RMS folder type, 'horizons' (default) or 'zones' etc!
            realisation (int): Realisation number, default is 0
            attributes (bool): If True, attributes will be preserved (from RMS 11)

        Returns:
            Object instance updated

        Raises:
            ValueError: Various types of invalid inputs.

        """
        stype = stype.lower()
        valid_stypes = ["horizons", "zones", "faults", "clipboard"]

        if stype not in valid_stypes:
            raise ValueError(
                "Invalid stype, only {} stypes is supported.".format(valid_stypes)
            )

        _xyz_roxapi.import_xyz_roxapi(
            self, project, name, category, stype, realisation, attributes
        )

        self._filesrc = "RMS: {} ({})".format(name, category)

    @abc.abstractmethod
    def to_roxar(
        self,
        project,
        name,
        category,
        stype="horizons",
        pfilter=None,
        realisation=0,
        attributes=False,
    ):
        """Export (store) a points/polygons item to a Roxar RMS project.

        The export to the RMS project can be done either within the project
        or outside the project.

        Note also that horizon/zone name and category must exists in advance,
        otherwise an Exception will be raised.

        Args:
            project (str or special): Name of project (as folder) if
                outside RMS, og just use the magic project word if within RMS.
            name (str): Name of polygons item
            category (str): For horizons/zones/faults: for example 'DL_depth'
            pfilter (dict): Filter on e.g. top name(s) with keys TopName
                or ZoneName as {'TopName': ['Top1', 'Top2']}
            stype (str): RMS folder type, 'horizons' (default), 'zones'
                or 'faults' or 'clipboard'  (in prep: well picks)
            realisation (int): Realisation number, default is 0
            attributes (bool): If True, attributes will be preserved (from RMS 11)


        Returns:
            Object instance updated

        Raises:
            ValueError: Various types of invalid inputs.
            NotImplementedError: Not supported in this ROXAPI version

        """

        valid_stypes = ["horizons", "zones", "faults", "clipboard", "horizon_picks"]

        if stype.lower() not in valid_stypes:
            raise ValueError(
                "Invalid stype, only {} stypes is supported.".format(valid_stypes)
            )

        _xyz_roxapi.export_xyz_roxapi(
            self,
            project,
            name,
            category,
            stype.lower(),
            pfilter,
            realisation,
            attributes,
        )

    # ==================================================================================
    # Get and Set properties
    # ==================================================================================

    # @abc.abstractproperty
    # def nrow(self):
    #     """NROW"""

    @property
    @abc.abstractmethod
    def dataframe(self):
        """Dataframe"""

    @dataframe.setter
    @abc.abstractmethod
    def dataframe(self, df):
        """Dataframe setter"""

    # @abc.abstractmethod
    # def get_carray(self, lname):
    #     """Returns the C array pointer (via SWIG) for a given log.

    #     Type conversion is double if float64, int32 if DISC log.
    #     Returns None of log does not exist.
    #     """
    #     try:
    #         np_array = self._df[lname].values
    #     except Exception:
    #         return None

    #     if self.get_logtype(lname) == 'DISC':
    #         carr = _xyz_lowlevel.convert_np_carr_int(self, np_array)
    #     else:
    #         carr = _xyz_lowlevel.convert_np_carr_double(self, np_array)

    #     return carr
