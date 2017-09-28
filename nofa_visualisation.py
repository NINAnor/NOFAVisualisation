# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NOFAVisualisation
                                 A QGIS plugin
 Load layers with predefined styles from NOFA database
                              -------------------
        begin                : 2015-12-01
        git sha              : $Format:%H$
        copyright            : (C) 2015 by NINA
        contributors         : stefan.blumentrath@nina.no
                               ondrej.svoboda@nina.no
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.core import QgsMessageLog

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QMessageBox

import os
import psycopg2
import psycopg2.extras
import sys
import traceback

from nofa.gui import vis_dlg, con_dlg
from nofa import db

reload(sys)
sys.setdefaultencoding('utf8')


class NOFAVisualisation(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        psycopg2.extras.register_uuid()

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        self.org = u'NINA'
        self.app_name = u'NOFAVisualisation'

        self.settings = QSettings(self.org, u'NOFA')

        self.host_str = u'host'
        self.port_str = u'port'
        self.db_str = u'database'
        self.usr_str = u'user'
        self.pwd_str = u'password'

        self.con_str_tpl = (
            self.host_str,
            self.port_str,
            self.db_str,
            self.usr_str,
            self.pwd_str)

        self.sel_str = u'Select'
        self.none_str = str(None)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.nofa_act = QAction(self.iface.mainWindow())
        self.nofa_act.setText(self.app_name)
        nofa_icon = QIcon(os.path.join(
            self.plugin_dir, 'nofavisualisation.png'))
        self.nofa_act.setIcon(nofa_icon)
        self.nofa_act.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.nofa_act)
        self.iface.addPluginToMenu(self.app_name, self.nofa_act)

        self.con_act = QAction(self.iface.mainWindow())
        self.con_act.setText(u'Connection Parameters')
        con_icon = QIcon(
            os.path.join(self.plugin_dir, 'data', 'icons', 'options.png'))
        self.con_act.setIcon(con_icon)
        self.con_act.triggered.connect(self._open_con_dlg)
        self.iface.addPluginToMenu(self.app_name, self.con_act)

        self.vis_dlg = vis_dlg.VisDlg(self.iface, self, self.plugin_dir)

    def unload(self):
        """
        Removes the plugin menu and icon.
        """

        self.iface.removePluginMenu(self.app_name, self.nofa_act)
        self.iface.removePluginMenu(self.app_name, self.con_act)
        self.iface.removeToolBarIcon(self.nofa_act)
        self.vis_dlg.dsc_from_iface()

    @property
    def con_info(self):
        """
        Returns a connection information from QSettings.

        :returns: A connection information dictionary.
        :rtype: dict
        """

        _con_info = {}

        for con_str in self.con_str_tpl:
            _con_info[con_str] = self.settings.value(con_str, u'')

        self.username = _con_info[self.usr_str]

        return _con_info

    def _open_con_dlg(self, con_info=None):
        """
        Opens a connection dialog.

        :param con_info: A connection information dictionary.
        :type con_info: dict
        """

        if not con_info:
            con_info = self.con_info

        self.con_dlg = con_dlg.ConDlg(self, con_info, u'Set up connection.')
        self.con_dlg.exec_()

    def run(self):
        """Runs method that performs all the real work."""

        self.con = None

        try:
            con_info = self.con_info
            self.con = db.get_con(con_info)

            if not db.chck_nofa_tbls(self.con):
                self._open_con_dlg(con_info)
        except psycopg2.OperationalError:
            self._open_con_dlg(con_info)

        if not self.con:
            return

        self.vis_dlg.prep()
        self.vis_dlg.show()

    def disp_err(self):
        """
        Displays error in QMessageBox and logs it to plugin message log.
        """

        type, value, tb = sys.exc_info()

        if type:
            tb = traceback.format_exc()
            QgsMessageLog.logMessage(tb, self.app_name)

            QMessageBox.critical(None, u'Error', u'See log for more detail.')
