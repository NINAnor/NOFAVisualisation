# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NOFAVisualisation
                                 A QGIS plugin
 Loads layers with predefined styes from the NOFA database
                              -------------------
        begin                : 2015-12-01
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Stefan Blumentrath - Norwegian Institute for Nature Research
        email                : stefan dot blumentrath at nina dot no
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
# from PyQt4.QtGui import QAction, QIcon, QColor
from PyQt4.QtGui import *

from collections import Counter

# from PyQt4.QtCore import *
# from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *
# from qgis.utils import *

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from nofa_visualisation_dialog import NOFAVisualisationDialog
import os.path
import psycopg2
import logging
import os

class NOFAVisualisation:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'NOFAVisualisation_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = NOFAVisualisationDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&NOFA Visualisation')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'NOFAVisualisation')
        self.toolbar.setObjectName(u'NOFAVisualisation')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('NOFAVisualisation', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToDatabaseMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/NOFAVisualisation/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'NOFA Visualisation'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(
                self.tr(u'&NOFA Visualisation'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # Load species list
        # prepare dialog parameters
        settings = QSettings()
        host = 'vm-srv-finstad.vm.ntnu.no'
        port = '5432'
        db = 'nofa_sandbox'
        user = 'nofa_guest'
        password = 'guest_nofa'
        con_string = "host='" + host + "' dbname='" + db + "' user='" + user + "' password='" + password + "'"
        #Conect to PostGIS using psycopg2 module
        try:
            conn = psycopg2.connect(con_string)
        except:
            logging.info("Unable to connect to the database")
        
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        # cur = conn.cursor()
        # cur.execute("""SELECT table_name FROM INFORMATION_SCHEMA.views WHERE table_schema = 'nofa' AND table_name LIKE '%_presence';""")
        # views = cur.fetchall()

        # Fetch species list for UI
        languages = ['Latin',
        'English',
        'Norwegian',
        'Swedish',
        'Finish']
        
        language = 'Norwegian'
        
        species_names = {'Latin': 'scientificName',
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
        cur = conn.cursor()
        cur.execute(u'SELECT reliability FROM nofa.l_reliability;')
        reliability = cur.fetchall()
        
        # Create a python-list from query result
        reliability_list = [s[0] for s in reliability]

        # Inject sorted python-list for species into UI
        reliability_list.sort()
        self.dlg.reliability.clear()
        self.dlg.reliability.addItems(reliability_list)

        # Get values from database
        cur = conn.cursor()
        cur.execute(u'SELECT "{0}" FROM nofa.l_taxon GROUP BY "{0}";'.format(species_names[language]))
        species = cur.fetchall()
        
        # Create a python-list from query result
        species_list = [s[0] for s in species]

        # Inject sorted python-list for species into UI
        species_list.sort()
        self.dlg.taxaList.clear()
        self.dlg.taxaList.addItems(species_list)

        # Get values from database
        cur = conn.cursor()
        cur.execute(u'SELECT "institutionCode", "datasetName" FROM nofa.m_dataset ORDER BY "institutionCode", "datasetName";')
        datasets_db = cur.fetchall()

        # Create a python-list from query result
        datasets_list = ['{},{}'.format(d[0], d[1]) for d in datasets_db]

        # Inject sorted python-list for species into UI
        datasets_list.sort()
        self.dlg.datasets.clear()
        self.dlg.datasets.addItems(datasets_list)

        # Fetch list of administrative units for filtering
        cur = conn.cursor()
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
        self.dlg.adminUnits.clear()
        
        for a in adminUnitList:
            #print a
            if a[0] not in countryCodes:
                countryCodes.append(a[0])
                ccTWIs.append(QTreeWidgetItem(self.dlg.adminUnits, [a[0]]))
 
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

        
        # self.dlg.adminUnits.addItems(adminUnit_list)
        #roots = []
        #for i in range(len(countryCodes)):
        #    roots.append(QTreeWidgetItem(self.dlg.adminUnits, [countryCodes[i]]))

        #countiesTWIs = []
        #for c in range(len(counties)):
        #    i = counties.index(counties[c])
        #    countiesTWIs.append(QTreeWidgetItem(roots[i], [counties[c]]))

        cur = conn.cursor()
        cur.execute(u"""SELECT replace(table_name, 'l_','') AS table_name, column_name 
        FROM information_schema.columns WHERE table_schema = 'nofa' AND 
        table_name IN ('location', 'event', 'occurrence', 'l_taxon') AND 
        column_name NOT LIKE '%_serial';""")
        columns = cur.fetchall()

        # Create a python-list from query result
        mandatory_columns = [u'occurrenceID', u'taxonID', u'eventID', u'locationID', u'geom']
        availableCols = [c[1] for c in columns]
        column_list = []
        for c in columns:
            if c[1] not in mandatory_columns:
                column_list.append(u'{0},{1}'.format(u''.join(c[0]), u''.join(c[1])))
        
        print column_list
        # Inject sorted python-list for administrative units into UI
        self.dlg.columns.clear()
        self.dlg.columns.addItems(column_list)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Get values from GUI
            geometry_type = self.dlg.geometry_type.currentText()
            language_type = self.dlg.language_type.currentText()
            reliabilityList = list(self.dlg.reliability.selectedItems()) if self.dlg.reliability.selectedItems() else None
            taxaList = list(self.dlg.taxaList.selectedItems()) if self.dlg.taxaList.selectedItems() else None
            adminUnitList = list(self.dlg.adminUnits.selectedItems()) if self.dlg.adminUnits.selectedItems() else None
            columnList = list(self.dlg.columns.selectedItems()) if self.dlg.columns.selectedItems() else None
            datasetList = list(self.dlg.datasets.selectedItems()) if self.dlg.datasets.selectedItems() else None
            visualisation_type = self.dlg.visualisation_type.currentText()
            afterDate = self.dlg.after.date()
            beforeDate = self.dlg.before.date()
            plugin_path = os.path.dirname(os.path.realpath(__file__))
            
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
                # print self.dlg.columns.items()
            # Compile list of columns to be selected
            cList = []
            if not columnList:
                for c in column_list:
                    if len([col for col in column_list if c.split(',')[1] in col]) == 1:
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
            
            
            for t in taxaList:
                # Get taxonID
                cur = conn.cursor()
                cur.execute(u"""SELECT "taxonID" FROM nofa."l_taxon" 
                            WHERE "{}" = '{}';""".format(species_names[language], t.text()))
                taxonID = int(cur.fetchall()[0][0])
                
                layerName = t.text()
                
                # Fetch taxon keys from database
               
                sql_part2 = u' (SELECT * FROM nofa.occurrence WHERE "taxonID" = {}) AS o '.format(taxonID)
                
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
                    vlayer.loadNamedStyle(os.path.join(plugin_path, 'introduction_points.qml'))
                elif vlayer.geometryType() == 2:
                    vlayer.loadNamedStyle(os.path.join(plugin_path, 'introduction_polygons.qml'))
                QgsMapLayerRegistry.instance().addMapLayer(vlayer)
