# -*- coding: utf-8 -*-
from __future__ import division, absolute_import
from __future__ import print_function

import glob
from os.path import join as ojoin

import pytest

from xtgeo.well import Well
from xtgeo.well import Wells
from xtgeo.common import XTGeoDialog

import test_common.test_xtg as tsetup

xtg = XTGeoDialog()
logger = xtg.basiclogger(__name__)

if not xtg.testsetup():
    raise SystemExit

td = xtg.tmpdir
testpath = xtg.testpath

# =========================================================================
# Do tests
# =========================================================================

WFILES = "../xtgeo-testdata/wells/battle/1/*.rmswell"


@pytest.fixture()
def loadwells1():
    logger.info('Load well 1')
    wlist = []
    for wfile in glob.glob(WFILES):
        wlist.append(Well(wfile))
    return wlist


def test_import_wells(loadwells1):
    """Import wells from file to Wells."""

    mywell_list = loadwells1

    mywells = Wells()
    mywells.wells = mywell_list

    assert 'WELL33' in mywells.names


def test_get_dataframe_allwells(loadwells1):
    """Get a single dataframe for all wells"""

    mywell_list = loadwells1

    mywells = Wells()
    mywells.wells = mywell_list

    df = mywells.get_dataframe(filled=True)

    #    assert df.iat[95610, 4] == 345.4128

    logger.debug(df)


@tsetup.plotskipifroxar
def test_quickplot_wells(loadwells1):
    """Import wells from file to Wells and quick plot."""

    mywell_list = loadwells1

    mywells = Wells()
    mywells.wells = mywell_list
    mywells.quickplot(filename=ojoin(td, 'quickwells.png'))


def test_wellintersections(loadwells1):
    """Find well crossing"""

    mywell_list = loadwells1

    mywells = Wells()
    mywells.wells = mywell_list
    dfr = mywells.wellintersections()
    logger.info(dfr)
    dfr.to_csv(ojoin(td, 'wells_crossings.csv'))


def test_wellintersections_tvdrange_nowfilter(loadwells1):
    """Find well crossing using coarser sampling to Fence"""

    mywell_list = loadwells1

    mywells = Wells()
    mywells.wells = mywell_list
    print('Limit TVD and downsample...')
    mywells.limit_tvd(1300, 1400)
    mywells.downsample(interval=6)
    print('Limit TVD and downsample...DONE')

    dfr = mywells.wellintersections()
    print(dfr)


def test_wellintersections_tvdrange_no_wfilter(loadwells1):
    """Find well crossing using coarser sampling to Fence, no
    wfilter settings.
    """

    mywell_list = loadwells1

    mywells = Wells()
    mywells.wells = mywell_list
    print('Limit TVD and downsample...')
    mywells.limit_tvd(1300, 1400)
    mywells.downsample(interval=6)
    print('Limit TVD and downsample...DONE')

    dfr = mywells.wellintersections()
    print(dfr)


def test_wellintersections_tvdrange_wfilter(loadwells1):
    """Find well crossing using coarser sampling to Fence, with
    wfilter settings.
    """

    wfilter = {'parallel': {'xtol': 4.0, 'ytol': 4.0, 'ztol': 2.0, 'itol': 10,
                            'atol': 5.0}}

    mywell_list = loadwells1

    mywells = Wells()
    mywells.wells = mywell_list
    print('Limit TVD and downsample...')
    mywells.limit_tvd(1300, 1400)
    mywells.downsample(interval=6)
    print('Limit TVD and downsample...DONE')

    dfr = mywells.wellintersections(wfilter=wfilter)
    dfr.to_csv(ojoin(td, 'wells_crossings_filter.csv'))
    print(dfr)
