# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VisDlg
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

from PyQt4 import uic
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import (
    QDialog, QMessageBox, QComboBox, QListWidget, QDateEdit, QTreeWidget,
    QTreeWidgetItem)

from qgis.core import (
    QgsDataSourceURI, QgsVectorLayer, QgsMapLayerRegistry, QgsMessageLog)

import logging
import os
import psycopg2
import sys
import traceback

from .. import db

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), 'vis_dlg.ui'))


class VisDlg(QDialog, FORM_CLASS):
    """
    A dialog for visualising data from NOFA database.
    """

    def __init__(self, iface, mc, plugin_dir):
        """
        Constructor.

        :param iface: A reference to the QgisInterface.
        :type iface: QgisInterface
        :param mc: A reference to the main class.
        :type mc: object
        :param plugin_dir: A plugin directory.
        :type plugin_dir: str
        """

        super(VisDlg, self).__init__()

        # set up the user interface from Designer.
        self.setupUi(self)

        self.iface = iface
        self.mc = mc
        self.plugin_dir = plugin_dir

        self._setup_self()

    def _setup_self(self):
        """
        Sets up self.
        """

        self.org = u'NINA'
        self.app_name = u'NOFAVisualisation - {}'.format(
            self.mc.con_info[self.mc.db_str])

        self.settings = QSettings(self.org, self.app_name)

        self.setWindowTitle(self.app_name)

        self.lang_list = [
            'Latin',
            'English',
            'Norwegian',
            'Swedish',
            'Finish']

        self.cur_lang = 'Norwegian'

        self.lang_spec_dict = {
            'Latin': 'scientificName',
            'English': 'vernacularName',
            'Norwegian': 'vernacularName_NO',
            'Swedish': 'vernacularName_SE',
            'Finish': 'vernacularName_FI'}

        self.lang_cntry_code_dict = {
            'Latin': None,
            'English': None,
            'Norwegian': 'NO',
            'Swedish': 'SE',
            'Finish': 'FI'}

        self.vis_type_qml_dict = {
            'establishmentMeans': 'introduction_points'}

        self._build_wdgs()

    def _build_wdgs(self):
        """
        Builds and sets up own widgets.
        """

        self.mindt_de.dateChanged.connect(self.maxdt_de.setMinimumDate)
        self.maxdt_de.dateChanged.connect(self.mindt_de.setMaximumDate)

        self.vis_btn.clicked.connect(self.vis)

    def dsc_from_iface(self):
        """
        Disconnects the plugin from the QGIS interface.
        """

        pass

    def pop_cb(self, cb_dict):
        """
        Populates combo boxe(s).

        :param cb_dict:
         | A combo box dictionary:
         |    - key - <combo box name>
         |    - value - [<fill method>, [<arguments>], <default value>]
        :type cb_dict: dict
        """

        for cb, cb_list in cb_dict.items():
            fnc = cb_list[0]
            args = cb_list[1]
            def_val = cb_list[2]

            item_list = fnc(*args)

            if def_val not in item_list:
                item_list.insert(0, def_val)

            self._add_cb_lw_items(cb, item_list)

            cb.setCurrentIndex(item_list.index(def_val))

    def pop_lw(self, lw_dict):
        """
        Populates list widget(s).

        :param lw_dict:
         | A list widget dictionary:
         |    - key - <list widge>
         |    - value - [<fill method>, [<arguments>]]
        :type lw_dict: dict
        """

        for lw, lw_list in lw_dict.items():
            fnc = lw_list[0]
            args = lw_list[1]

            item_list = fnc(*args)
            self._add_cb_lw_items(lw, item_list)

    def _add_cb_lw_items(self, wdg, item_list):
        """
        Adds items from the item list to a combo box or list widget.

        :param wdg: A combob box or list widget.
        :type wdg: QComboBox/QListWidget
        :param item_list: An item list.
        :type item_list: list
        """

        wdg.clear()

        for item in item_list:
            wdg.addItem(item)

    @property
    def _all_lw_dict(self):
        """
        Returns a list widget dictionary for all list widgets.

        :returns:
         | A list widget dictionary for all list widgets:
         |    - key - <list widget>
         |    - value - [<fill method>, [<arguments>]]
        :rtype: dict
        """

        all_lw_dict = {
            self.reliab_lw: [
                db.get_reliab_list,
                [self.mc.con]],
            self.txn_lw: [
                db.get_txn_name_list_no,
                [self.mc.con]],
            self.dtst_lw: [
                db.get_dtst_inst_list,
                [self.mc.con]],
            self.tbl_col_lw: [
                db.get_tbl_col_list,
                [self.mc.con]]}

        return all_lw_dict

    def pop_admu_tw(self):
        """
        Populates administrative units tree widget.
        """

        self.admu_tw.clear()

        admu_list = db.get_admu_list(self.mc.con)

        cntry_list = []
        cnty_list = []

        cntry_item_list = []
        cnty_item_list = []
        muni_item_list = []
          
        for admu in admu_list:
            cntry = admu[0]
            cnty = admu[1]
            muni = admu[2]

            if cntry not in cntry_list:
                cntry_list.append(cntry)
                cntry_item = QTreeWidgetItem(self.admu_tw, [cntry])
                cntry_item_list.append(cntry_item)
   
            if cnty not in cnty_list:
                cnty_list.append(cnty)
                cntry_idx = cntry_list.index(cntry)
                cnty_item = QTreeWidgetItem(cntry_item_list[cntry_idx], [cnty])
                cnty_item_list.append(cnty_item)
                  
            cnty_idx = cnty_list.index(cnty)
            muni_item = QTreeWidgetItem(cnty_item_list[cnty_idx], [muni])
            muni_item_list.append(muni_item)

    def prep(self):
        """
        Prepares the whole plugin to be shown.
        """

        try:
            self.pop_lw(self._all_lw_dict)

            self.pop_admu_tw()

            event_min_dt = db.get_event_min_dt(self.mc.con)
            self.mindt_de.setMinimumDate(event_min_dt)
            self.mindt_de.setDate(event_min_dt)

            event_max_dt = db.get_event_max_dt(self.mc.con)
            self.maxdt_de.setDate(event_max_dt)
        except:
            self.mc.disp_err()

    def _set_lyr_tbl_cfg(self, layer, vsbl_col_list):
        """
        Sets layer table config.
        
        :param layer: A reference to the layer.
        :type layer: QgsVectorLayer
        :param vsbl_col_list: A tuple of visible columns.
        :type vsbl_col_list: tuple
        """
        
        fields = layer.pendingFields()
        
        tableConfig = layer.attributeTableConfig()
        tableConfig.update(fields)
         
        columns = tableConfig.columns()

        if vsbl_col_list:
            for column in columns:
                if column.name not in vsbl_col_list:
                    column.hidden = True
         
        tableConfig.setColumns(columns)
        layer.setAttributeTableConfig(tableConfig)

    def _get_wdg_input(self, wdg):
        """
        Return widget input.

            - *QComboBox* -- current text
            - *QDateEdit* -- date
            - *QListWidget/QTreeWidget* -- list of selected items,
                None when no item is selected

        :param wdg: A widget.
        :type wdg: QWidget

        :returns: Widget input.
        :rtype: str/datetime.date/list/None
        """

        if isinstance(wdg, QComboBox):
            wdg_input = wdg.currentText()
        elif isinstance(wdg, QDateEdit):
            wdg_input = wdg.date().toPyDate()
        elif isinstance(wdg, (QListWidget, QTreeWidget)):
            if len(wdg.selectedItems()) != 0:
                wdg_input = wdg.selectedItems()
            else:
                wdg_input = None

        return wdg_input

    def vis(self):
        """Visualises data."""

        try:
            geom_type = self._get_wdg_input(self.geom_type)
            lang = self._get_wdg_input(self.lang_cb)
            reliab_list = self._get_wdg_input(self.reliab_lw)
            txn_list = self._get_wdg_input(self.txn_lw)
            vsbl_col_list = self._get_wdg_input(self.tbl_col_lw)
            dtst_list = self._get_wdg_input(self.dtst_lw)
            vis_type = self._get_wdg_input(self.vis_type_cb)
            min_dt = self._get_wdg_input(self.mindt_de)
            max_dt = self._get_wdg_input(self.maxdt_de)
            admu_list = self._get_wdg_input(self.admu_tw)
    
            uri = QgsDataSourceURI()
            host = self.mc.con_info[self.mc.host_str]
            port = self.mc.con_info[self.mc.port_str]
            db_name = self.mc.con_info[self.mc.db_str]
            user = self.mc.con_info[self.mc.usr_str]
            password = self.mc.con_info[self.mc.pwd_str]
            uri.setConnection(host, port, db_name, user, password)

            if txn_list is None:
                QMessageBox.warning(
                    self,
                    u'Taxon',
                    u'Select at least one taxon.')
            else:
                cntry_list, cnty_list, muni_list = self._get_admu_lists(
                    admu_list)

                for txn in txn_list:
                    txn_name = txn.text()
                    txn_id = db.get_txn_id_no(self.mc.con, txn_name)

                    vis_query = db.get_vis_query(
                        self.mc.con,
                        txn_id, min_dt, max_dt, reliab_list, dtst_list,
                        self._val_list(cntry_list),
                        self._val_list(cnty_list),
                        self._val_list(muni_list),
                        self._get_col_str(vsbl_col_list))

                    uri.setDataSource('', vis_query, 'geom','', 'occurrenceID')
                    lyr = QgsVectorLayer(uri.uri(), txn_name, 'postgres')
                    self._set_lyr_stl(lyr)
                    # self._set_lyr_tbl_cfg(lyr, vsbl_col_list)

                    if lyr.isValid():
                        QgsMapLayerRegistry.instance().addMapLayer(lyr)
                    else:
                        QMessageBox.warning(
                            self,
                            u'Layer',
                            u'Layer is not valid.')
        except:
            self.mc.disp_err()

    def _get_admu_lists(self, admu_list):
        """
        Returns administrative unit lists:

            - *list* -- country
            - *list* -- county
            - *list* -- municipality

        :param admu_list: A list of administrative units.
        :type admu_list: list

        :returns: A tuple containing:
         | A tuple containing:
         |    - *list* -- country
         |    - *list* -- county
         |    - *list* -- municipality
        :rtype: tuple
        """

        cntry_list = []
        cnty_list = []
        muni_list = []

        if admu_list:
            for admu in admu_list:
                if admu.parent():
                    if admu.parent().parent():
                        muni_list.append(admu.text(0))
                    else:
                        cnty_list.append(admu.text(0))
                else:
                    cntry_list.append(admu.text(0))

        return (cntry_list, cnty_list, muni_list)

    def _get_col_str(self, vsbl_col_list):
        """
        Returns a column string.

        .. warning::
        
           String formatting is only temporary workaround!
           Unfortunately `psycopg2.sql` module
           is only available from version 2.7.

           More information here:

              - https://stackoverflow.com/a/27291545
              - http://initd.org/psycopg/docs/sql.html

        :param vsbl_col_list: A list of visible columns,
            None when no item is selected.
        :type vsbl_col_list: list/None
        """

        if not vsbl_col_list:
            vsbl_col_list = [] 
            for idx in xrange(self.tbl_col_lw.count()):
                vsbl_col_list.append(self.tbl_col_lw.item(idx))

        col_str = ''

        for col in vsbl_col_list:
            splt_str = col.text().split(' - ')
            tbl = splt_str[0]
            col = splt_str[1]

            col_str += '{0}."{1}" AS "{2}_{1}",'.format(tbl[:1], col, tbl)

        return col_str

    def _val_list(self, input_list):
        """
        Validates the given list.

        :param input_list: An input list.
        :type input_list: list

        :returns: None when list is empty, the list itself otherwise.
        :rtype: list/None
        """

        if len(input_list) == 0:
            return None
        else:
            return input_list

    def _set_lyr_stl(self, lyr):
        """
        Sets layer style according to its geometry type.

        :param lyr: A layer.
        :type lyr: QgsVectorLayer
        """

        if lyr.geometryType() == 0:
            qml_fn = 'introduction_points.qml'
        elif lyr.geometryType() == 2:
            qml_fn = 'introduction_polygons.qml'

        qml_fp = os.path.join(self.plugin_dir, qml_fn)

        lyr.loadNamedStyle(qml_fp)
