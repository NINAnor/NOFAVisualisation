# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NOFAVisualisation
                                 A QGIS plugin
 Loads layers with predefined styes from the NOFA database
                             -------------------
        begin                : 2015-12-01
        copyright            : (C) 2015 by Stefan Blumentrath - Norwegian Institute for Nature Research
        email                : stefan dot blumentrath at nina dot no
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load NOFAVisualisation class from file NOFAVisualisation.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .nofa_visualisation import NOFAVisualisation
    return NOFAVisualisation(iface)
