from PyQt5.QtGui import  QStandardItem, QStandardItemModel
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QAbstractItemModel
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QFileDialog, QListView, QTreeView

#http://doc.qt.digia.com/4.6/itemviews-editabletreemodel.html

class EntryTreeView(QTreeView):
    pass

class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, data, parent=None):
        super(TreeModel, self).__init__(parent)
        self.parents=[]
        self.dbdata = data
        self.rootItem = TreeItem([["Attributes"], ["Values"]])
        self.setupModelData(self.dbdata, self.rootItem)

    def clear(self):
        self.rootItem.removeChildren()
        self.layoutChanged.emit()
        #self.rootItem = TreeItem([["Attributes"], ["Values"]])
        #self.setupModelData(self.dbdata, self.rootItem)
        pass


    def setData(self, index, value, role):
       if index.isValid() and role == QtCore.Qt.EditRole:

            prev_value = self.getValue(index)
            item = index.internalPointer()

            item.setData(value, index.column())

            return True
       else:
           return False

    def removeRows(self, position=0, count=1,  parent=QtCore.QModelIndex()):

       node = self.nodeFromIndex(parent)
       self.beginRemoveRows(parent, position, position + count - 1)
       node.childItems.pop(position)
       self.endRemoveRows()

    def nodeFromIndex(self, index):
       if index.isValid():
           return index.internalPointer()
       else:
           return self.rootItem

    def getValue(self, index):
       item = index.internalPointer()
       return item.data(index.column())

    def columnCount(self, parent):
       if parent.isValid():
           return parent.internalPointer().columnCount()
       else:
           return self.rootItem.columnCount()

    def data(self, index, role):
       if not index.isValid():
           return None
       if role != QtCore.Qt.DisplayRole:
           return None

       item = index.internalPointer()
       return QtCore.QVariant(item.data(index.column()))

    def flags(self, index):
        if not index.isValid():
           return QtCore.Qt.NoItemFlags

        if index.column() == 0:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable


    def headerData(self, section, orientation, role):
       if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
           return QtCore.QVariant(self.rootItem.data(section)[0])

       return None

    def index(self, row, column, parent):

       if row < 0 or column < 0 or row >= self.rowCount(parent) or column >= self.columnCount(parent):
           return QtCore.QModelIndex()

       if not parent.isValid():
           parentItem = self.rootItem
       else:
           parentItem = parent.internalPointer()

       childItem = parentItem.child(row)
       if childItem:
           return self.createIndex(row, column, childItem)
       else:
           return QtCore.QModelIndex()

    def parent(self, index):
       if not index.isValid():
           return QtCore.QModelIndex()

       childItem = index.internalPointer()
       parentItem = childItem.parent()

       if parentItem == self.rootItem or parentItem is None:
           return QtCore.QModelIndex()

       return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
       if parent.column() > 0:
           return 0

       if not parent.isValid():
           parentItem = self.rootItem
       else:
           parentItem = parent.internalPointer()

       return parentItem.childCount()

    def setupModelData(self, lines, parent):
       ind = []
       self.parents.append(parent)
       ind.append(0)
       col_numb=parent.columnCount()
       numb = 0

       for line in lines:
           numb+=1
           lineData=line[0]
           self.parents[-1].appendChild(TreeItem(lineData, self.parents[-1]))

           columnData = line[1]

           self.parents.append(self.parents[-1].child(self.parents[-1].childCount() - 1))

           for j in columnData:
                self.parents[-1].appendChild(TreeItem(j, self.parents[-1]))
           if len(self.parents) > 0:
                self.parents.pop()


    def createTreeFromDict(self, data, parent, top=False):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    node = TreeItem([key, ""], parent)
                    parent.appendChild(node)
                    self.createTreeFromDict(value, node)

                elif isinstance(value, list):
                    node = TreeItem([key, ""], parent)
                    parent.appendChild(node)
                    self.createTreeFromDict(value, node)

                else:
                    print(key)
                    print(value)
                    node = TreeItem([key, value], parent)
                    parent.appendChild(node)


        if isinstance(data, list):
            for index, value in enumerate(data):
                if isinstance(value, dict):

                    node = TreeItem([index+1, ""], parent)
                    parent.appendChild(node)
                    self.createTreeFromDict(value, node)

                elif isinstance(value, list):
                    node = TreeItem([index+1, ""], parent)
                    parent.appendChild(node)
                    self.createTreeFromDict(value, node)

                else:
                    node = TreeItem(["juttu", value], parent)
                    parent.appendChild(node)

        if top:
            self.layoutChanged.emit()



class TreeItem(object):
      def __init__(self, data, parent=None):
          self.parentItem = parent
          self.itemData = data
          self.childItems = []

      def appendChild(self, item):
          self.childItems.append(item)

      def child(self, row):
          return self.childItems[row]

      def childCount(self):
          return len(self.childItems)

      def columnCount(self):
          return len(self.itemData)

      def data(self, column):
          try:
              return self.itemData[column]

          except IndexError:
              return None

      def parent(self):
          return self.parentItem

      def row(self):
          if self.parentItem:
              return self.parentItem.childItems.index(self)

          return 0
      def setData(self, data, column):
          self.itemData[column] = data

      def removeChildren(self):
          self.childItems = []
          return True



"""
class TreeItem():

    _parent = None
    _children = []
    _itemData = []
    def __init__(self, data, parent):
        self._parent = parent
        self._itemData = data
        #super(TreeItem, self).__init__(data)

    def child(self, number):
        return self._children[number]

    def childCount(self):
        return len(self._children)

    def columnCount(self):
        return len(self._itemData)

    def insertChildren(self, position, data):
        if position < 0 or position > len(self._itemData):
            return False

        t = TreeItem(data, self)
        self._children.append(t)
        return True


    def insertColumns(self, position, columns):
        pass

    def removeChildren(self, position, columns):
        pass

    def childNumber(self):
        if self._parent is not None:
            return self._parent.childItems.indexOf(self)
        return None

    def setData(self, column, value):
        pass

    def parent(self):
        return self._parent

    def data(self, column):
        return self._itemData[column]

    def setData(self, column, value):
        if column < 0 or column > len(self._itemData):
            return False

        self._itemData[column] = value
        return True
"""
