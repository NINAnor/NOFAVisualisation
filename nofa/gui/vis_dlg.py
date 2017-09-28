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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QDialog, QTreeWidgetItem, QMessageBox

from collections import Counter

from qgis.core import *
from qgis.gui import *

import os.path
import psycopg2
import logging
import os
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
        except:
            self.mc.disp_err()

    def vis(self):
        """Visualises data."""

        try:
            # Get values from GUI
            geometry_type = self.geometry_type.currentText()
            language_type = self.language_type.currentText()
            reliabilityList = list(self.reliab_lw.selectedItems()) if self.reliab_lw.selectedItems() else None
            taxaList = list(self.txn_lw.selectedItems()) if self.txn_lw.selectedItems() else None
            adminUnitList = list(self.admu_tw.selectedItems()) if self.admu_tw.selectedItems() else None
            columnList = list(self.tbl_col_lw.selectedItems()) if self.tbl_col_lw.selectedItems() else None
            datasetList = list(self.dtst_lw.selectedItems()) if self.dtst_lw.selectedItems() else None
            visualisation_type = self.visualisation_type.currentText()
            afterDate = self.after.date()
            beforeDate = self.before.date()
            
            sql_where = None
            
            if beforeDate > afterDate:
                after = afterDate.toString(u'yyyy-MM-dd')
                before = beforeDate.toString(u'yyyy-MM-dd')
                
                # Select only events which begin or end in the relevant time frame
                sql_where = u""" WHERE ("dateEnd" >= CAST('{}' AS date)""".format(before)
                sql_where += u""" AND "dateEnd" < CAST('{}' AS date))""".format(after)
                sql_where += u""" OR ("dateStart" < CAST('{}' AS date)""".format(before)
                sql_where += u""" AND "dateStart" >= CAST('{}' AS date))""".format(after)
            
            # Reliability filter
            if reliabilityList:
                rList = []
                for r in reliabilityList:
                    rList.append(r.text()) 
                if not sql_where:
                    sql_where = u""" WHERE "reliability" IN ('{}')""".format(u"""', '""".join(rList))
                else:
                    sql_where += u""" AND "reliability" IN ('{}')""".format(u"""', '""".join(rList))
                sql_where += u""" OR "reliability" IS NULL"""
                    
            # dataset filter
            if datasetList:
                dList = []
                for d in datasetList:
                    dList.append(d.text().split(' - ')[1]) 
                if not sql_where:
                    sql_where = u""" WHERE "datasetName" IN ('{}')""".format(u"""', '""".join(dList))
                else:
                    sql_where += u""" AND "datasetName" IN ('{}')""".format(u"""', '""".join(dList))
    
            selMun = []
            selCtry = []
            selCty = []
            subSelCtry = []
            subSelCty = []
    
            if adminUnitList:
                for o in adminUnitList:
                    # get countries, counties and test if subunits are selected
                    if o.parent():
                        if o.parent().parent():
                            selMun.append(o.text(0))
                        else:
                            selCty.append(o.text(0))
                    else:
                        selCtry.append(o.text(0))
    
                admin_where = None
                if selCtry:
                    admin_where = u""""countryCode" IN ('{}')""".format(u"""', '""".join(selCtry))
                if selCty:
                    if not admin_where:
                        admin_where = u""""county" IN ('{}')""".format(u"""', '""".join(selCty))
                    else:
                        admin_where += u""" OR "county" IN ('{}')""".format(u"""', '""".join(selCty))
                if selMun:
                    if not admin_where:
                        admin_where = u""""municipality" IN ('{}')""".format(u"""', '""".join(selMun))
                    else:
                        admin_where += u""" OR "municipality" IN ('{}')""".format(u"""', '""".join(selMun))
    
                if not sql_where:
                    sql_where = u""" WHERE ({})""".format(admin_where)
                else:
                    sql_where += u""" AND  ({})""".format(admin_where)
                 # For debugging
                # print adminUnitList
                # print columnList
                # print self.tbl_col_lw.items()
            # Compile list of columns to be selected
            column_list = db.get_tbl_col_list(self.mc.con)
            cList = []
            if not columnList:
                for c in column_list:
                    if len([col for col in column_list if c.split(' - ')[1] in col]) == 1:
                        cList.append('{}."{}"'.format(c[0], c.split(' - ')[1]))
                    else:
                        cList.append('{0}."{2}" AS "{1}_{2}"'.format(c[0], c.split(' - ')[0], c.split(' - ')[1]))
            else:
                for c in columnList:
                    if len([col for col in columnList if c.split(' - ')[1] in col]) == 1:
                        cList.append('{}."{}"'.format(c[0], c.split(' - ')[1]))
                    else:
                        cList.append('{0}."{2}" AS "{1}_{2}"'.format(c[0], c.split(' - ')[0], c.split(' - ')[1]))
            if 'o."{}"'.format(visualisation_type) not in cList:
                cList.append('o."{}"'.format(visualisation_type))
    
            # self.iface.messageBar().pushWidget(widget, QgsMessageBar.WARNING, duration=3)
            # define a lookup: value -> (color, label)
            # introduction = {
                # 1: ('#f5f532', 'Unknown'),
                # 2: ('#19cd37', 'Natural'),
                # 3: ('#c80000', 'Introduced'),
                # '': ('#ffffff', 'No data')
            # }
            # # create the renderer and assign it to a layer
            # expression = 'establishmentMeansID' # field name
    
            # # create a category for each item in introduction
            # point_categories = []
            # for introduction_name, (color, label) in introduction.items():
                # symbol = QgsSymbolV2.defaultSymbol(0)
                # symbol.setColor(QColor(color))
                # category = QgsRendererCategoryV2(introduction_name, symbol, label)
                # point_categories.append(category)
    
            # point_renderer = QgsCategorizedSymbolRendererV2(expression, point_categories)
    
            # # create a category for each item in introduction
            # line_categories = []
            # for introduction_name, (color, label) in introduction.items():
                # symbol = QgsSymbolV2.defaultSymbol(1)
                # symbol.setColor(QColor(color))
                # category = QgsRendererCategoryV2(introduction_name, symbol, label)
                # line_categories.append(category)
    
            # line_renderer = QgsCategorizedSymbolRendererV2(expression, line_categories)
    
            # # create a category for each item in introduction
            # polygon_categories = []
            # for introduction_name, (color, label) in introduction.items():
                # symbol = QgsSymbolV2.defaultSymbol(2)
                # symbol.setColor(QColor(color))
                # category = QgsRendererCategoryV2(introduction_name, symbol, label)
                # polygon_categories.append(category)
    
            # polygon_renderer = QgsCategorizedSymbolRendererV2(expression, polygon_categories)
    
            uri = QgsDataSourceURI()
            # set host name, port, database name, username and password
            host = self.mc.con_info[self.mc.host_str]
            port = self.mc.con_info[self.mc.port_str]
            db_name = self.mc.con_info[self.mc.db_str]
            user = self.mc.con_info[self.mc.usr_str]
            password = self.mc.con_info[self.mc.pwd_str]
            uri.setConnection(host, port, db_name, user, password)
    
            if geometry_type == 'Points':
                geom = "geom"
            else:
                geom = "geom"
    
            # Generate part of SQL-string for columns to show
            sql_part1 = u'(SELECT "occurrenceID", geom, "taxonID", "eventID", "locationID"'
            for c in cList:
                sql_part1 += u', {}'.format(c)
            sql_part1 += u' FROM '
            
            sql_part3 = u'LEFT JOIN nofa.l_taxon AS t USING ("taxonID") '
            sql_part3 += u'LEFT JOIN nofa.event AS e USING ("eventID") '
            sql_part3 += u'LEFT JOIN nofa.location AS l USING ("locationID")'
            sql_part3 += u'LEFT JOIN nofa.m_dataset AS d USING ("datasetID")'
            
            if taxaList is None:
                QMessageBox.warning(
                    self,
                    u'Taxon',
                    u'Select at least one taxon.')
            else:
                for t in taxaList:
                    # Get taxonID
                    cur = self.mc.con.cursor()
                    cur.execute(u"""SELECT "taxonID" FROM nofa."l_taxon" 
                                WHERE "{}" = '{}';""".format(self.lang_spec_dict[self.cur_lang], t.text()))
                    taxonID = int(cur.fetchall()[0][0])
                    
                    layerName = t.text()
                    
                    # Fetch taxon keys from database
                   
                    sql_part2 = u' (SELECT * FROM nofa.occurrence WHERE "taxonID" = {}) AS o '.format(taxonID)
    
                    if sql_where is None:
                        sql_where = 'WHERE TRUE'
    
                    sql = sql_part1 + sql_part2 + sql_part3 + sql_where + ')'
        
                    uri.setDataSource("",sql,"geom","","occurrenceID")
        
                    vlayer = QgsVectorLayer(uri.uri(),layerName,"postgres")
                    # set database schema, table name, geometry column and optionally
                    # subset (WHERE clause), primary key
                    # print layerName
        
                    # uri = '{0} key={1} table={2} (geom) sql='.format(con_string,'occurrenceID', sql)
                    #layer = QgsVectorLayer(uri, "testlayer", "postgres")
        
                    # uri.setDataSource("nofa", sql, geom,"","occurrenceID")
                    # vlayer = QgsVectorLayer(uri.uri(), layerName, "postgres")
                    # vlayer = QgsVectorLayer(uri, layerName, "postgres")
                    if vlayer.geometryType() == 0:
                        vlayer.loadNamedStyle(os.path.join(self.plugin_dir, 'introduction_points.qml'))
                    elif vlayer.geometryType() == 2:
                        vlayer.loadNamedStyle(os.path.join(self.plugin_dir, 'introduction_polygons.qml'))
                    QgsMapLayerRegistry.instance().addMapLayer(vlayer)
        except:
            self.mc.disp_err()
