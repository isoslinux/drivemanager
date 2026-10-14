"""Review a subset of imported preferences with explicit target folders."""
from dataclasses import replace
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QTableWidget,QTableWidgetItem,QLineEdit,QDialogButtonBox,QPushButton,QHBoxLayout,QFileDialog,QWidget
from .providers import PROVIDERS

class ImportReview(QDialog):
    def __init__(self,owner,rows):
        super().__init__(owner);self.rows=rows;self.controls=[];self.t=owner.t
        self.setWindowTitle(self.t['import_settings']);self.resize(900,470)
        layout=QVBoxLayout(self);note=QLabel(self.t['import_select_note']);note.setWordWrap(True);layout.addWidget(note)
        table=QTableWidget(len(rows),3);self.table=table
        table.setHorizontalHeaderLabels([self.t['account'],self.t['choose'],self.t['import_mode']]);layout.addWidget(table)
        for i,(name,provider,prefs) in enumerate(rows):
            item=QTableWidgetItem(name+' · '+next(p.label for p in PROVIDERS if p.key==provider));item.setFlags(Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsUserCheckable);item.setCheckState(Qt.CheckState.Checked);table.setItem(i,0,item)
            folder=prefs.mount_path or str(owner.manager.home/'DriveManager'/owner.manager.settings.path(name).stem)
            editor=QLineEdit(folder);button=QPushButton('…');button.setToolTip(self.t['choose'])
            def choose(checked=False,editor=editor):
                path=QFileDialog.getExistingDirectory(self,self.t['choose'],editor.text())
                if path:editor.setText(path)
            button.clicked.connect(choose);widget=QWidget();line=QHBoxLayout(widget);line.setContentsMargins(0,0,0,0);line.addWidget(editor);line.addWidget(button);table.setCellWidget(i,1,widget)
            text=self.t['mode_rw' if prefs.writable else 'mode_ro']+' · '+self.t['automount']+': '+('✓' if prefs.automount else '—')+'\n'+self.t['upload_limit']+': '+(str(prefs.upload_kib)+' KiB/s' if prefs.upload_kib else self.t['unlimited'])+' · '+self.t['download_limit']+': '+(str(prefs.download_kib)+' KiB/s' if prefs.download_kib else self.t['unlimited'])
            details=QTableWidgetItem(text);details.setFlags(Qt.ItemFlag.ItemIsEnabled);table.setItem(i,2,details);self.controls.append((item,editor))
        table.resizeColumnsToContents();table.resizeRowsToContents()
        from PySide6.QtWidgets import QHeaderView
        table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
        self.save=buttons.button(QDialogButtonBox.StandardButton.Save)
        self.save.setText(self.t["import_apply"]);buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.t["import_cancel"])
        table.itemChanged.connect(lambda:self.save.setEnabled(any(item.checkState()==Qt.CheckState.Checked for item,_ in self.controls)))

    def selected(self):
        return [(name,provider,replace(prefs,mount_path=editor.text())) for (name,provider,prefs),(item,editor) in zip(self.rows,self.controls) if item.checkState()==Qt.CheckState.Checked]
