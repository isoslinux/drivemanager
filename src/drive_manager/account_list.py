"""Native account table with a small selection API shared by the controller."""
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView

class AccountList(QTableWidget):
    currentIndexChanged=Signal(int)
    def __init__(self, headers):
        super().__init__(0,len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True);self.setShowGrid(False)
        self.verticalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        self.itemSelectionChanged.connect(lambda:self.currentIndexChanged.emit(self.currentRow()))
    def currentText(self):
        item=self.item(self.currentRow(),0)
        return item.text() if item else ''
    def clear(self):
        self.clearContents();self.setRowCount(0)
    def addItems(self,names):
        self.setRowCount(len(names))
        for row,name in enumerate(names):
            for col in range(self.columnCount()):
                value=name if col==0 else '—'
                self.setItem(row,col,QTableWidgetItem(value))
        if names:self.setCurrentCell(0,0)
    def setCurrentText(self,name):
        for row in range(self.rowCount()):
            if self.item(row,0).text()==name:self.setCurrentCell(row,0);return
    def update_account(self,name,provider,path,mode,state):
        for row in range(self.rowCount()):
            if self.item(row,0).text()==name:
                for col,value in enumerate([name,provider,path,mode,state]):
                    self.item(row,col).setText(value)
                return
