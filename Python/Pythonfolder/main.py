import sys
import os
import shutil
import paramiko
import posixpath
import stat
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMenu, QSplitter, QTreeView, QFileSystemModel,
    QMessageBox, QDialog, QLineEdit, QPushButton, QFormLayout, QInputDialog, QHBoxLayout, QHeaderView, QAbstractItemView,
    QProgressBar, QStatusBar, QLabel, QVBoxLayout, QWidget, QTextEdit, QScrollArea
)
from PySide6.QtCore import QDir, Qt, Signal, QMimeData, QTimer, QThread
from PySide6.QtGui import QAction, QIcon, QStandardItemModel, QStandardItem, QDrag, QKeySequence, QPixmap

# SFTPConnectDialog class is correct and unchanged
class SftpConnectDialog(QDialog):
    """A dialog to get SFTP connection details from the user."""
    connection_successful = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to SFTP Server")
        self.layout = QFormLayout(self)
        self.host_input = QLineEdit(); self.port_input = QLineEdit("22")
        self.user_input = QLineEdit(); self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.layout.addRow("Host:", self.host_input); self.layout.addRow("Port:", self.port_input)
        self.layout.addRow("Username:", self.user_input); self.layout.addRow("Password:", self.pass_input)
        buttons = QHBoxLayout(); self.connect_button = QPushButton("Connect"); self.cancel_button = QPushButton("Cancel")
        buttons.addWidget(self.connect_button); buttons.addWidget(self.cancel_button)
        self.layout.addRow(buttons)
        self.connect_button.clicked.connect(self.attempt_connection); self.cancel_button.clicked.connect(self.reject)

    def attempt_connection(self):
        try:
            transport = paramiko.Transport((self.host_input.text(), int(self.port_input.text())))
            transport.connect(username=self.user_input.text(), password=self.pass_input.text())
            sftp = paramiko.SFTPClient.from_transport(transport)
            self.connection_successful.emit(sftp)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {e}")

class CustomTreeView(QTreeView):
    """Custom Tree View to handle drag and drop"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # CORRECTED LINE: Access the Enum correctly
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def startDrag(self, supportedActions):
        indexes = self.selectedIndexes()
        if not indexes:
            return

        name_indexes = [idx for idx in indexes if idx.column() == 0]
        if not name_indexes:
            return

        mime_data = self.model().mimeData(name_indexes)
        if not mime_data:
            return
            
        mime_data.setProperty("source_view_name", self.objectName())
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction | Qt.DropAction.CopyAction)

class DualPaneFileManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyForklift")
        self.setGeometry(100, 100, 1400, 800)
        
        self.left_sftp_client = None; self.right_sftp_client = None
        self.left_remote_path = ''; self.right_remote_path = ''
        self.bookmarks = []  # Store bookmarked paths
        self.current_search_filter = ""

        self.splitter = QSplitter(Qt.Horizontal)
        
        self.left_tree = CustomTreeView()
        self.left_tree.setObjectName("left_tree")
        self.right_tree = CustomTreeView()
        self.right_tree.setObjectName("right_tree")

        self.go_local(self.left_tree, QDir.homePath())
        self.go_local(self.right_tree, QDir.homePath())

        self.splitter.addWidget(self.left_tree)
        self.splitter.addWidget(self.right_tree)
        self.setCentralWidget(self.splitter)
        self.create_toolbar()
        self.create_status_bar()
        self.setup_keyboard_shortcuts()

    def setup_tree_view(self, view_object):
        view_object.setSortingEnabled(True)
        view_object.setAnimated(True)
        view_object.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        view_object.customContextMenuRequested.connect(self.show_context_menu)
        view_object.doubleClicked.connect(self.on_double_click)
        view_object.dropEvent = self.on_drop
        view_object.dragEnterEvent = lambda e: e.acceptProposedAction()
        view_object.dragMoveEvent = lambda e: e.acceptProposedAction()
        return view_object
    
    def on_drop(self, event):
        source_view_name = event.mimeData().property("source_view_name")
        if not source_view_name: return

        source_view = self.findChild(CustomTreeView, source_view_name)
        dest_view = self.sender()
        if source_view is dest_view: return

        op = 'move' if event.proposedAction() == Qt.DropAction.MoveAction else 'copy'
        
        for index in source_view.selectionModel().selectedRows():
            if op == 'copy': self._execute_copy(source_view, dest_view, index)
            else: self._execute_move(source_view, dest_view, index)
        event.accept()

    def on_double_click(self, index):
        tree_view = self.sender()
        if self._is_local_pane(tree_view):
            path = tree_view.model().filePath(index)
            if os.path.isdir(path):
                tree_view.setRootIndex(index)
        else:
            item_text = index.data(Qt.ItemDataRole.DisplayRole)
            if item_text == "..":
                self.go_up_directory(); return
            
            sftp, current_path = self.get_remote_info(tree_view)
            new_path = posixpath.join(current_path, item_text)
            try:
                if stat.S_ISDIR(sftp.stat(new_path).st_mode):
                    self.navigate_remote_directory(tree_view, new_path)
            except Exception as e:
                print(f"Error navigating remote: {e}")
    
    def create_toolbar(self):
        toolbar = self.addToolBar("Main Toolbar")
        up_action = QAction(QIcon.fromTheme("go-up"), "Up", self); up_action.triggered.connect(self.go_up_directory); toolbar.addAction(up_action)
        sftp_action = QAction(QIcon.fromTheme("network-server"), "Connect...", self); sftp_action.triggered.connect(self.show_sftp_dialog); toolbar.addAction(sftp_action)
        toolbar.addSeparator()
        copy_action=QAction(QIcon.fromTheme("edit-copy"), "Copy", self); copy_action.triggered.connect(lambda:self.process_operation('copy')); toolbar.addAction(copy_action)
        move_action=QAction(QIcon.fromTheme("edit-cut"), "Move", self); move_action.triggered.connect(lambda:self.process_operation('move')); toolbar.addAction(move_action)
        delete_action=QAction(QIcon.fromTheme("edit-delete"), "Delete", self); delete_action.triggered.connect(lambda:self.process_operation('delete')); toolbar.addAction(delete_action)
        toolbar.addSeparator()
        
        # New file/folder actions
        new_folder_action = QAction(QIcon.fromTheme("folder-new"), "New Folder", self)
        new_folder_action.triggered.connect(lambda: self.create_new_folder(self.get_active_and_destination_panes()[0]))
        toolbar.addAction(new_folder_action)
        
        new_file_action = QAction(QIcon.fromTheme("document-new"), "New File", self)
        new_file_action.triggered.connect(lambda: self.create_new_file(self.get_active_and_destination_panes()[0]))
        toolbar.addAction(new_file_action)
        toolbar.addSeparator()
        
        # Bookmarks
        bookmarks_action = QAction(QIcon.fromTheme("bookmark-new"), "Bookmarks", self)
        bookmarks_action.triggered.connect(self.show_bookmarks_menu)
        toolbar.addAction(bookmarks_action)
        
        # Search
        search_action = QAction(QIcon.fromTheme("edit-find"), "Search", self)
        search_action.triggered.connect(self.show_search_dialog)
        toolbar.addAction(search_action)

    def show_context_menu(self, position):
        tree_view = self.sender()
        index = tree_view.indexAt(position)
        menu = QMenu()
        
        # Add file/folder creation options
        new_folder_action = menu.addAction("New Folder")
        new_file_action = menu.addAction("New File")
        menu.addSeparator()
        
        if index.isValid():
            rename_action = menu.addAction("Rename")
            copy_action = menu.addAction("Copy")
            move_action = menu.addAction("Move")
            delete_action = menu.addAction("Delete")
            menu.addSeparator()
            bookmark_action = menu.addAction("Add to Bookmarks")
            preview_action = menu.addAction("Preview")
        else:
            # Empty space context menu
            copy_action = None; move_action = None; delete_action = None
            rename_action = None; bookmark_action = None; preview_action = None
        
        action = menu.exec(tree_view.viewport().mapToGlobal(position))
        
        if action == new_folder_action:
            self.create_new_folder(tree_view)
        elif action == new_file_action:
            self.create_new_file(tree_view)
        elif action == rename_action:
            self.rename_item(tree_view, index)
        elif action == copy_action:
            self.process_operation('copy')
        elif action == move_action:
            self.process_operation('move')
        elif action == delete_action:
            self.process_operation('delete')
        elif action == bookmark_action:
            self.add_bookmark(tree_view, index)
        elif action == preview_action:
            self.preview_file(tree_view, index)

    def process_operation(self, op_type):
        active_tree, dest_tree = self.get_active_and_destination_panes()
        if not active_tree.selectionModel().hasSelection(): return

        for index in active_tree.selectionModel().selectedRows(0):
            if op_type == 'copy': self._execute_copy(active_tree, dest_tree, index)
            elif op_type == 'move': self._execute_move(active_tree, dest_tree, index)
            elif op_type == 'delete': self._execute_delete(active_tree, index)
    
    def _execute_copy(self, source_view, dest_view, source_index):
        s_local = self._is_local_pane(source_view); d_local = self._is_local_pane(dest_view)
        try:
            self.show_progress("Copying...", 100)
            if s_local and d_local: self._local_to_local(source_view, dest_view, source_index, 'copy')
            elif not s_local and d_local: self._remote_to_local(source_view, dest_view, source_index)
            elif s_local and not d_local: self._local_to_remote(source_view, dest_view, source_index)
            else: QMessageBox.warning(self, "Unsupported", "Remote-to-remote copy is not supported.")
            self.hide_progress("Copy completed")
        except Exception as e: 
            self.hide_progress("Copy failed")
            QMessageBox.critical(self, "Copy Error", str(e))
    
    def _execute_move(self, source_view, dest_view, source_index):
        s_local = self._is_local_pane(source_view); d_local = self._is_local_pane(dest_view)
        try:
            self.show_progress("Moving...", 100)
            if s_local and d_local: self._local_to_local(source_view, dest_view, source_index, 'move')
            elif not s_local and d_local: self._remote_to_local(source_view, dest_view, source_index, delete_source=True)
            elif s_local and not d_local: self._local_to_remote(source_view, dest_view, source_index, delete_source=True)
            else: QMessageBox.warning(self, "Unsupported", "Remote-to-remote move is not supported.")
            self.hide_progress("Move completed")
        except Exception as e: 
            self.hide_progress("Move failed")
            QMessageBox.critical(self, "Move Error", str(e))

    def _execute_delete(self, source_view, source_index):
        try:
            if self._is_local_pane(source_view):
                path = source_view.model().filePath(source_index)
                if os.path.isdir(path): shutil.rmtree(path)
                else: os.remove(path)
            else:
                sftp, current_path = self.get_remote_info(source_view); item_name = source_index.data()
                remote_path = posixpath.join(current_path, item_name)
                if stat.S_ISDIR(sftp.stat(remote_path).st_mode): self._delete_remote_dir(sftp, remote_path)
                else: sftp.remove(remote_path)
        except Exception as e:
            QMessageBox.critical(self, "Delete Error", str(e))

    def create_new_folder(self, tree_view):
        """Create a new folder in the current directory"""
        if self._is_local_pane(tree_view):
            current_path = tree_view.model().filePath(tree_view.rootIndex())
            name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
            if ok and name:
                new_path = os.path.join(current_path, name)
                try:
                    os.makedirs(new_path, exist_ok=False)
                    tree_view.model().refresh(tree_view.rootIndex())
                except OSError as e:
                    QMessageBox.warning(self, "Error", f"Failed to create folder: {e}")
        else:
            QMessageBox.information(self, "Info", "Creating folders on remote servers is not yet supported.")

    def create_new_file(self, tree_view):
        """Create a new file in the current directory"""
        if self._is_local_pane(tree_view):
            current_path = tree_view.model().filePath(tree_view.rootIndex())
            name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
            if ok and name:
                new_path = os.path.join(current_path, name)
                try:
                    with open(new_path, 'w') as f:
                        pass  # Create empty file
                    tree_view.model().refresh(tree_view.rootIndex())
                except OSError as e:
                    QMessageBox.warning(self, "Error", f"Failed to create file: {e}")
        else:
            QMessageBox.information(self, "Info", "Creating files on remote servers is not yet supported.")

    def rename_item(self, tree_view, index):
        """Rename a file or folder"""
        current_name = index.data()
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=current_name)
        if ok and new_name and new_name != current_name:
            if self._is_local_pane(tree_view):
                current_path = tree_view.model().filePath(index)
                new_path = os.path.join(os.path.dirname(current_path), new_name)
                try:
                    os.rename(current_path, new_path)
                    tree_view.model().refresh(tree_view.rootIndex())
                except OSError as e:
                    QMessageBox.warning(self, "Error", f"Failed to rename: {e}")
            else:
                QMessageBox.information(self, "Info", "Renaming on remote servers is not yet supported.")

    def add_bookmark(self, tree_view, index):
        """Add current directory to bookmarks"""
        if self._is_local_pane(tree_view):
            path = tree_view.model().filePath(tree_view.rootIndex())
            name = os.path.basename(path) or path
        else:
            sftp, path = self.get_remote_info(tree_view)
            name = f"Remote: {path}"
        
        bookmark = {"name": name, "path": path, "is_remote": not self._is_local_pane(tree_view)}
        if bookmark not in self.bookmarks:
            self.bookmarks.append(bookmark)
            QMessageBox.information(self, "Bookmark Added", f"Added '{name}' to bookmarks")

    def preview_file(self, tree_view, index):
        """Preview file content"""
        if self._is_local_pane(tree_view):
            file_path = tree_view.model().filePath(index)
            if os.path.isfile(file_path):
                self.show_file_preview(file_path)
        else:
            QMessageBox.information(self, "Info", "File preview for remote files is not yet supported.")

    def show_file_preview(self, file_path):
        """Show file preview dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Preview: {os.path.basename(file_path)}")
        dialog.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Check if it's an image
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # It's an image
                scroll_area = QScrollArea()
                label = QLabel()
                label.setPixmap(pixmap)
                label.setScaledContents(True)
                scroll_area.setWidget(label)
                layout.addWidget(scroll_area)
            else:
                # Try as text file
                self.show_text_preview(file_path, layout)
        except:
            # Try as text file
            self.show_text_preview(file_path, layout)
        
        dialog.exec()

    def show_text_preview(self, file_path, layout):
        """Show text file preview"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(10000)  # Limit to first 10KB
                if len(content) == 10000:
                    content += "\n... (truncated)"
        except:
            content = "Unable to preview this file"
        
        text_edit = QTextEdit()
        text_edit.setPlainText(content)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

    def create_status_bar(self):
        """Create status bar with progress indicator"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        # F2 for rename
        rename_shortcut = QAction(self)
        rename_shortcut.setShortcut(QKeySequence("F2"))
        rename_shortcut.triggered.connect(self.rename_selected)
        self.addAction(rename_shortcut)
        
        # F5 for refresh
        refresh_shortcut = QAction(self)
        refresh_shortcut.setShortcut(QKeySequence("F5"))
        refresh_shortcut.triggered.connect(self.refresh_current_pane)
        self.addAction(refresh_shortcut)
        
        # Ctrl+F for search
        search_shortcut = QAction(self)
        search_shortcut.setShortcut(QKeySequence("Ctrl+F"))
        search_shortcut.triggered.connect(self.show_search_dialog)
        self.addAction(search_shortcut)

    def rename_selected(self):
        """Rename currently selected item"""
        active_tree, _ = self.get_active_and_destination_panes()
        if active_tree.selectionModel().hasSelection():
            index = active_tree.selectionModel().selectedIndexes()[0]
            self.rename_item(active_tree, index)

    def refresh_current_pane(self):
        """Refresh the currently active pane"""
        active_tree, _ = self.get_active_and_destination_panes()
        if self._is_local_pane(active_tree):
            active_tree.model().refresh(active_tree.rootIndex())
        else:
            # Refresh remote directory
            sftp, path = self.get_remote_info(active_tree)
            if sftp:
                self.navigate_remote_directory(active_tree, path)

    def show_search_dialog(self):
        """Show search dialog"""
        text, ok = QInputDialog.getText(self, "Search Files", "Enter search term:")
        if ok and text:
            self.current_search_filter = text
            self.filter_files(text)

    def filter_files(self, search_term):
        """Filter files based on search term"""
        active_tree, _ = self.get_active_and_destination_panes()
        if self._is_local_pane(active_tree):
            # For local files, we'll implement a simple filter
            # This is a basic implementation - could be enhanced
            self.status_label.setText(f"Searching for: {search_term}")
        else:
            self.status_label.setText(f"Search not yet supported for remote directories")

    def show_bookmarks_menu(self):
        """Show bookmarks menu"""
        if not self.bookmarks:
            QMessageBox.information(self, "Bookmarks", "No bookmarks saved yet.\nRight-click on a directory and select 'Add to Bookmarks' to save it.")
            return
        
        menu = QMenu(self)
        for i, bookmark in enumerate(self.bookmarks):
            action = menu.addAction(bookmark["name"])
            action.setData(i)
        
        action = menu.exec(self.mapToGlobal(self.toolBar().pos()))
        if action:
            bookmark_index = action.data()
            self.navigate_to_bookmark(bookmark_index)

    def navigate_to_bookmark(self, bookmark_index):
        """Navigate to a bookmarked location"""
        if 0 <= bookmark_index < len(self.bookmarks):
            bookmark = self.bookmarks[bookmark_index]
            active_tree, _ = self.get_active_and_destination_panes()
            
            if bookmark["is_remote"]:
                QMessageBox.information(self, "Info", "Remote bookmarks not yet supported for navigation")
            else:
                self.go_local(active_tree, bookmark["path"])

    def show_progress(self, message, maximum=100):
        """Show progress bar with message"""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText(message)

    def update_progress(self, value, message=None):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)

    def hide_progress(self, message="Ready"):
        """Hide progress bar"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)

    def _local_to_local(self, s_view, d_view, s_idx, op):
        s_path = s_view.model().filePath(s_idx); d_path = d_view.model().filePath(d_view.rootIndex())
        dest_full_path = os.path.join(d_path, os.path.basename(s_path))
        if os.path.exists(dest_full_path): return

        if op == 'copy':
            if os.path.isdir(s_path): shutil.copytree(s_path, dest_full_path)
            else: shutil.copy2(s_path, d_path)
        elif op == 'move': shutil.move(s_path, d_path)

    def _remote_to_local(self, s_view, d_view, s_idx, delete_source=False):
        sftp, remote_path = self.get_remote_info(s_view)
        remote_item_path = posixpath.join(remote_path, s_idx.data())
        local_dest_dir = d_view.model().filePath(d_view.rootIndex())
        self._download_item(sftp, remote_item_path, local_dest_dir)
        if delete_source: self._execute_delete(s_view, s_idx)
    
    def _local_to_remote(self, s_view, d_view, s_idx, delete_source=False):
        sftp, remote_dest_dir = self.get_remote_info(d_view)
        local_item_path = s_view.model().filePath(s_idx)
        self._upload_item(sftp, local_item_path, remote_dest_dir)
        if delete_source: self._execute_delete(s_view, s_idx)
   
    def _download_item(self, sftp, remote_path, local_dest_dir):
        item_name=posixpath.basename(remote_path); local_path=os.path.join(local_dest_dir, item_name)
        if stat.S_ISDIR(sftp.stat(remote_path).st_mode):
            os.makedirs(local_path, exist_ok=True)
            for item in sftp.listdir(remote_path): self._download_item(sftp, posixpath.join(remote_path, item), local_path)
        else: sftp.get(remote_path, local_path)

    def _upload_item(self, sftp, local_path, remote_dest_dir):
        item_name=os.path.basename(local_path); remote_path=posixpath.join(remote_dest_dir, item_name)
        if os.path.isdir(local_path):
            try: sftp.mkdir(remote_path)
            except IOError: pass
            for item in os.listdir(local_path): self._upload_item(sftp, os.path.join(local_path, item), remote_path)
        else: sftp.put(local_path, remote_path)

    def _delete_remote_dir(self, sftp, path):
        for item in sftp.listdir_attr(path):
            item_path = posixpath.join(path, item.filename)
            if stat.S_ISDIR(item.st_mode): self._delete_remote_dir(sftp, item_path)
            else: sftp.remove(item_path)
        sftp.rmdir(path)
    
    def go_local(self, tree_view, path):
        self.setup_tree_view(tree_view)
        model = QFileSystemModel()
        model.setRootPath("/")
        tree_view.setModel(model)
        tree_view.setRootIndex(model.index(path))
        for i in range(1, 4): tree_view.header().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        tree_view.header().setStretchLastSection(False)
        sftp, _ = self.get_remote_info(tree_view)
        if sftp: sftp.close();
        if tree_view is self.left_tree: self.left_sftp_client = None
        else: self.right_sftp_client = None

    def navigate_remote_directory(self, tree_view, path):
        sftp, _ = self.get_remote_info(tree_view);
        if not sftp: return
        self.setup_tree_view(tree_view)
        remote_model=QStandardItemModel(); remote_model.setHorizontalHeaderLabels(['Name', 'Size', 'Type', 'Date Modified'])
        if path != '/': up_item = QStandardItem(".."); up_item.setIcon(QIcon.fromTheme("go-up")); remote_model.appendRow(up_item)
        try:
            for attr in sftp.listdir_attr(path):
                name=QStandardItem(attr.filename); is_dir=stat.S_ISDIR(attr.st_mode); name.setIcon(QIcon.fromTheme("folder" if is_dir else "text-x-generic"))
                size=QStandardItem(str(attr.st_size)); type=QStandardItem("Folder" if is_dir else "File"); date=QStandardItem(datetime.fromtimestamp(attr.st_mtime).strftime('%Y-%m-%d %H:%M'))
                remote_model.appendRow([name,size,type,date])
        except Exception as e: print(e)
        tree_view.setModel(remote_model)
        for i in range(1,4): tree_view.header().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        tree_view.header().setStretchLastSection(False)
        if tree_view is self.left_tree: self.left_remote_path = path
        else: self.right_remote_path = path

    def show_sftp_dialog(self): active_tree, _ = self.get_active_and_destination_panes(); dialog=SftpConnectDialog(self); dialog.connection_successful.connect(lambda sftp:self.connect_pane_to_sftp(active_tree,sftp)); dialog.exec()
    def connect_pane_to_sftp(self,tree_view,sftp):
        if tree_view is self.left_tree: self.left_sftp_client=sftp
        else: self.right_sftp_client=sftp
        self.navigate_remote_directory(tree_view,sftp.getcwd() or '/')
    def get_remote_info(self, tree_view): return (self.left_sftp_client, self.left_remote_path) if tree_view is self.left_tree else (self.right_sftp_client, self.right_remote_path)
    def get_active_and_destination_panes(self): return (self.left_tree, self.right_tree) if self.left_tree.hasFocus() else (self.right_tree, self.left_tree)
    def _is_local_pane(self,tree_view): return isinstance(tree_view.model(), QFileSystemModel)
    def go_up_directory(self):
        active_tree, _ = self.get_active_and_destination_panes()
        if self._is_local_pane(active_tree):
            active_tree.setRootIndex(active_tree.rootIndex().parent())
        else:
            if active_tree.model().rowCount() > 0: self.on_double_click(active_tree.model().index(0,0))
    def closeEvent(self,e):
        if self.left_sftp_client: self.left_sftp_client.close()
        if self.right_sftp_client: self.right_sftp_client.close()
        e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DualPaneFileManager()
    window.show()
    sys.exit(app.exec())