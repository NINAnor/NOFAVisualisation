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

    def prep(self):
        """
        Prepares the whole plugin to be shown.
        """

        try:
            # Fetch species list for UI
            languages = ['Latin',
            'English',
            'Norwegian',
            'Swedish',
            'Finish']
            
            self.language = 'Norwegian'
            
            self.species_names = {'Latin': 'scientificName',
                             'English': 'vernacularName',
                             'Norwegian': 'vernacularName_NO',
                             'Swedish': 'vernacularName_SE',
                             'Finish': 'vernacularName_FI'}
            
            countryCodes = {'Latin': None,
                             'English': None,
                             'Norwegian': 'NO',
                             'Swedish': 'SE',
                             'Finish': 'FI'}
    
            #
            qml = {'establishmentMeans': 'introduction_points',
                   '': ''}
    
            # Get values from database
            cur = self.mc.con.cursor()
            cur.execute(u'SELECT reliability FROM nofa.l_reliability;')
            reliability = cur.fetchall()
            
            # Create a python-list from query result
            reliability_list = [s[0] for s in reliability]
     
            # Inject sorted python-list for species into UI
            reliability_list.sort()
            self.reliability.clear()
            self.reliability.addItems(reliability_list)
     
            # Get values from database
            cur = self.mc.con.cursor()
            cur.execute(u'SELECT "{0}" FROM nofa.l_taxon GROUP BY "{0}";'.format(self.species_names[self.language]))
            species = cur.fetchall()
             
            # Create a python-list from query result
            species_list = [s[0] for s in species]
     
            # Inject sorted python-list for species into UI
            species_list.sort()
            self.taxaList.clear()
            self.taxaList.addItems(species_list)
     
            # Get values from database
            cur = self.mc.con.cursor()
            cur.execute(u'SELECT "institutionCode", "datasetName" FROM nofa.m_dataset ORDER BY "institutionCode", "datasetName";')
            datasets_db = cur.fetchall()
     
            # Create a python-list from query result
            datasets_list = ['{},{}'.format(d[0], d[1]) for d in datasets_db]
     
            # Inject sorted python-list for species into UI
            datasets_list.sort()
            self.datasets.clear()
            self.datasets.addItems(datasets_list)
     
            # Fetch list of administrative units for filtering
            cur = self.mc.con.cursor()
            cur.execute(u"""SELECT "countryCode", "county", "municipality" FROM "AdministrativeUnits"."Fenoscandia_Municipality_polygon";""")
            adminUnitList = cur.fetchall()
     
            # Create a python-list from query result
            adminUnit_list = []
            for a in adminUnitList:
                adminUnit_list.append(u'{0},{1},{2}'.format(u''.join(a[0]), u''.join(a[1]), u''.join(a[2])))
     
            # Inject sorted python-list for administrative units into UI
            adminUnit_list.sort()
            countryCodes = []
            counties = []
            cTWIs = []
            ccTWIs = []
            mTWIs = []
            self.adminUnits.clear()
              
            for a in adminUnitList:
                #print a
                if a[0] not in countryCodes:
                    countryCodes.append(a[0])
                    ccTWIs.append(QTreeWidgetItem(self.adminUnits, [a[0]]))
       
                if a[1] not in counties:
                    counties.append(a[1])
                    ccidx = countryCodes.index(a[0])
                    cTWIs.append(QTreeWidgetItem(ccTWIs[ccidx], [a[1]]))
                      
                cidx = counties.index(a[1])
                mTWIs.append(QTreeWidgetItem(cTWIs[cidx], [a[2]]))
                  
      
                      
                #countryCodes.append(a[0])
                #counties.append(a[1])
                  
            #counties_set = set(counties)
            #countryCodes_set = set(countryCodes)
              
            #counties = list(counties_set)
            #countryCodes = list(countryCodes_set)
      
              
            # self.adminUnits.addItems(adminUnit_list)
            #roots = []
            #for i in range(len(countryCodes)):
            #    roots.append(QTreeWidgetItem(self.adminUnits, [countryCodes[i]]))
      
            #countiesTWIs = []
            #for c in range(len(counties)):
            #    i = counties.index(counties[c])
            #    countiesTWIs.append(QTreeWidgetItem(roots[i], [counties[c]]))

            cur = self.mc.con.cursor()
            cur.execute(u"""SELECT replace(table_name, 'l_','') AS table_name, column_name 
            FROM information_schema.columns WHERE table_schema = 'nofa' AND 
            table_name IN ('location', 'event', 'occurrence', 'l_taxon') AND 
            column_name NOT LIKE '%_serial';""")
            columns = cur.fetchall()

            # Create a python-list from query result
            mandatory_columns = [u'occurrenceID', u'taxonID', u'eventID', u'locationID', u'geom']
            availableCols = [c[1] for c in columns]
            self.column_list = []
            for c in columns:
                if c[1] not in mandatory_columns:
                    self.column_list.append(u'{0},{1}'.format(u''.join(c[0]), u''.join(c[1])))
    
            # Inject sorted python-list for administrative units into UI
            self.columns.clear()
            self.columns.addItems(self.column_list)
        except:
            self.mc.disp_err()

    def vis(self):
        """Visualises data."""

        try:
            # Get values from GUI
            geometry_type = self.geometry_type.currentText()
            language_type = self.language_type.currentText()
            reliabilityList = list(self.reliability.selectedItems()) if self.reliability.selectedItems() else None
            taxaList = list(self.taxaList.selectedItems()) if self.taxaList.selectedItems() else None
            adminUnitList = list(self.adminUnits.selectedItems()) if self.adminUnits.selectedItems() else None
            columnList = list(self.columns.selectedItems()) if self.columns.selectedItems() else None
            datasetList = list(self.datasets.selectedItems()) if self.datasets.selectedItems() else None
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
                    dList.append(d.text().split(',')[1]) 
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
                # print self.columns.items()
            # Compile list of columns to be selected
            cList = []
            if not columnList:
                for c in self.column_list:
                    if len([col for col in self.column_list if c.split(',')[1] in col]) == 1:
                        cList.append('{}."{}"'.format(c[0], c.split(',')[1]))
                    else:
                        cList.append('{0}."{2}" AS "{1}_{2}"'.format(c[0], c.split(',')[0], c.split(',')[1]))
            else:
                for c in columnList:
                    if len([col for col in columnList if c.split(',')[1] in col]) == 1:
                        cList.append('{}."{}"'.format(c[0], c.split(',')[1]))
                    else:
                        cList.append('{0}."{2}" AS "{1}_{2}"'.format(c[0], c.split(',')[0], c.split(',')[1]))
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
            db = self.mc.con_info[self.mc.db_str]
            user = self.mc.con_info[self.mc.usr_str]
            password = self.mc.con_info[self.mc.pwd_str]
            uri.setConnection(host, port, db, user, password)
    
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
                                WHERE "{}" = '{}';""".format(self.species_names[self.language], t.text()))
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
