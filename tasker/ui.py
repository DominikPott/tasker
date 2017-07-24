import inspect, os

from qtpy import QtCore, QtWidgets, QtGui

import tasker.control
from tasker import log



TASKER_DIR = os.path.dirname(inspect.getfile(tasker))
STYLESHEET = os.path.join(TASKER_DIR, 'stylesheets', 'darkorange.stylesheet')
#STYLESHEET = os.path.join(TASKMANAGER_DIR, 'stylesheets', 'houdini2016.stylesheet')
TASKER_ICON= os.path.join(TASKER_DIR, 'icons', 'tasker.png')
PICTURE_PLACEHOLDER= os.path.join(TASKER_DIR, 'icons', 'template.png')


def update_trees_afterwards(func):
    """Decorator to refresh the ui for context menu functions.

    Args:
        func: Context menu function to be decorated.

    Returns:
        fund: Decorated function.

    """
    def update_wrapper(*args, **kwargs):
        func(*args, **kwargs)
        args[0].update_trees()
    return update_wrapper


class ProjectTree(QtWidgets.QWidget):
    """Tree Widget to display project , working and done lists."""

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.settings = None
        self.project = None

        self.create_layout()
        self.apply_settings()
        self.connect_signals()

    def create_layout(self):
        root_layout = QtWidgets.QVBoxLayout()
        self.setLayout(root_layout)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText('Filter for asset or shot')
        root_layout.addWidget(self.search_bar)

        self.overview_tab_container = QtWidgets.QTabWidget()
        root_layout.addWidget(self.overview_tab_container)

        # Project Tab
        self.project_widget = QtWidgets.QTreeWidget()
        self.project_widget.setLayout(QtWidgets.QVBoxLayout())
        HEADER = ['Task', 'State', 'User']
        self.project_widget.setColumnCount(len(HEADER))
        self.project_widget.setHeaderLabels(HEADER)
        self.project_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        # Work List Tab
        self.worklist_widget = QtWidgets.QTreeWidget()
        self.worklist_widget.setLayout(QtWidgets.QVBoxLayout())
        HEADER = ['Asset', 'Task', 'State']
        self.worklist_widget.setColumnCount(len(HEADER))
        self.worklist_widget.setHeaderLabels(HEADER)
        self.worklist_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.overview_tab_container.addTab(self.project_widget, 'Project')
        self.overview_tab_container.addTab(self.worklist_widget, 'Worklist')

    def apply_settings(self):
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.search_bar.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.overview_tab_container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def connect_signals(self):
        self.project_widget.customContextMenuRequested.connect(self.project_context_menu)
        self.worklist_widget.customContextMenuRequested.connect(self.worklist_context_menu)
        self.search_bar.returnPressed.connect(self.update_trees)

    def project_context_menu(self, pos):
        clicked_item = self.project_widget.itemAt(pos)
        if not clicked_item.parent():
            self.creation_menu(pos=pos)
        elif not clicked_item.parent().parent():
            self.asset_menu(pos=pos)
        else:
            self.assignment_menu(pos=pos)

    def assignment_menu(self, pos):
        """Creates an assignment context menu.

        Args:
            pos: cursor position

        """
        menu = QtWidgets.QMenu(self)
        set_state_action = QtWidgets.QAction('Set state', self)
        set_state_action.triggered.connect(self.set_state)
        menu.addAction(set_state_action)
        assign_user_action = QtWidgets.QAction('Assign User', self)
        assign_user_action.triggered.connect(self.assign_user)
        menu.addAction(assign_user_action)
        menu.popup(self.project_widget.mapToGlobal(pos))

    def creation_menu(self, pos):
        """Creates a context menu at cursor position to create new shots and assets.

        Args:
            pos: cursor position

        """
        menu = QtWidgets.QMenu(self)
        new_asset_action = QtWidgets.QAction('New Asset', self)
        new_asset_action.triggered.connect(self.parent().parent().new_asset)
        menu.addAction(new_asset_action)
        new_shot_action= QtWidgets.QAction('New Shot', self)
        new_shot_action.triggered.connect(self.parent().parent().new_shot)
        menu.addAction(new_shot_action)
        menu.popup(self.project_widget.mapToGlobal(pos))

    def asset_menu(self, pos):
        """context menu do handling existing assets. Renaming and deletion.

        Args:
            pos: cursor position

        """
        menu = QtWidgets.QMenu(self)
        rename_asset_action = QtWidgets.QAction('Rename', self)
        #rename_asset_action.triggered.connect(self.parent().parent().new_asset)
        rename_asset_action.setEnabled(False)
        menu.addAction(rename_asset_action)
        delete_asset_action = QtWidgets.QAction('Delete', self)
        delete_asset_action.triggered.connect(self.delete_asset)
        menu.addAction(delete_asset_action)
        menu.addSeparator()
        edit_tasks_aciton= QtWidgets.QAction('Edit tasks', self)
        # edit_tasks_aciton.triggered.connect(self.parent().parent().new_asset)
        edit_tasks_aciton.setEnabled(False)
        menu.addAction(edit_tasks_aciton)
        menu.popup(self.project_widget.mapToGlobal(pos))

    def worklist_context_menu(self, pos):
        """context menu for the worklist widget to user action for the current task.

        Args:
            pos:

        Returns:

        """
        menu = QtWidgets.QMenu(self)
        set_state_action = QtWidgets.QAction('Set state', self)
        set_state_action.triggered.connect(self.set_state)
        menu.addAction(set_state_action)
        menu.popup(self.worklist_widget.mapToGlobal(pos))

    def update_trees(self):
        """Slot to update the project and worklist trees for the current project."""
        try:
            sender = self.sender()
            self.project=sender._project
            self.settings=sender.settings
        except AttributeError as e:
            pass
        if self.project and self.settings:
            self.update_project_tree(project=self.project)
            self.update_work_list(settings=self.settings)

    def update_project_tree(self, project):
        """Updates the displayed data of the project tree.
        :param project: Tasker.control.Project instance which holds relevant data to be displayed."""
        self.project_widget.clear()
        if not project:
            return
        assets_root = QtWidgets.QTreeWidgetItem()
        assets_root.setText(0, 'Assets')

        self.project_widget.insertTopLevelItem(0, assets_root)
        assets = self.filter_by_searchbar(project.assets)
        self.fill_tree(items_to_add=assets, parent=assets_root)

        shots_root= QtWidgets.QTreeWidgetItem()
        shots_root.setText(0, 'Shots')
        self.project_widget.insertTopLevelItem(1, shots_root)
        shots = self.filter_by_searchbar(project.shots)
        self.fill_tree(items_to_add=shots, parent=shots_root)

        self.project_widget.expandAll()
        self.project_widget.resizeColumnToContents(0)

    def filter_by_searchbar(self, unfiltered):
        filter_word = self.search_bar.text()
        if filter_word:
            filtered = set()
            for item in unfiltered:  # filter the item names
                if filter_word in item.name:
                    filtered.add(item)
                    continue
                for task in item.tasks:  # Filter the items tasks
                    if filter_word in task.name:
                        filtered.add(item)
                        break
                    try:
                        if filter_word in task.user.name:  # Filter assigned user
                            filtered.add(item)
                            break
                    except AttributeError:
                        pass
            return filtered
        return unfiltered

    def fill_tree(self, items_to_add, parent):
        for item in items_to_add:
            widget = QtWidgets.QTreeWidgetItem(parent)
            widget.setText(0, item.name)
            widget.setData(0, QtCore.Qt.UserRole, item)
            self.add_task_items(widget)

    def add_task_items(self, parent):
        if not parent:
            return
        parent.takeChildren()
        for task in parent.data(0, QtCore.Qt.UserRole).tasks:
            task_item = QtWidgets.QTreeWidgetItem(parent)
            task_item.setText(0, task.name)
            task_item.setData(0, QtCore.Qt.UserRole, task)
            task_item.setText(1, task.state)
            if task.user:
                task_item.setText(2, task.user.name)
            if task.child_tasks:
                self.add_task_items(parent=task_item)

    def update_work_list(self, settings):
        user_name = settings.value('user')
        try:
            user = tasker.control.get_user_by_name(name=user_name)
        except ValueError as e:
            log.error(e)
            return
        tasks = user.tasks  # TODO: this will only work if theres just on project otherwise tasks gets mixed up.
        self.worklist_widget.clear()
        for task in tasks:
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, task.parent.name)
            item.setData(0, QtCore.Qt.UserRole, task)
            item.setText(1, task.name)
            item.setText(2, task.state)
            self.worklist_widget.addTopLevelItem(item)

    # Task Context Menu Functions
    @update_trees_afterwards
    def set_state(self):
        """Context Menu Slot to set the state of the selected task."""
        log.debug('Running set state.')
        current_widget=self.overview_tab_container.currentWidget()
        # Tree widget allows only one selected item
        for item in current_widget.selectedItems():
            task = item.data(0, QtCore.Qt.UserRole)
            index = task.registered_states.index(task.state)
            new_state, ok = QtWidgets.QInputDialog.getItem(self, 'Set State:', 'States:', task.registered_states, index, False)
            if ok and new_state and task.is_state_allowed(state=new_state):
                self.add_comment(task=task, new_state=new_state)
                task.state=new_state
                self.add_task_items(parent=item.parent())

    def add_comment(self, task, new_state):
        comment, ok = QtWidgets.QInputDialog.getText(self, 'Write Comment', 'Comment:')
        if ok and comment:
            text = '{old_state} >> {new_state}.\nComment: {comment}'.format(old_state=task.state,
                                                                            new_state=new_state,
                                                                            comment=comment
                                                                            )
            task.add_comment(text=text)

    @update_trees_afterwards
    def assign_user(self):
        """Context Menu Slot to assign a user to the selected task."""
        log.debug('Running assign user.')
        # Tree widget allows only one selected item
        users = tasker.control.get_all_users()
        for item in self.project_widget.selectedItems():
            user_names = [user.name for user in users]
            user, ok = QtWidgets.QInputDialog.getItem(self, 'Assign User:', 'Users:', user_names, 0, False)
            if ok and user:
                task = item.data(0, QtCore.Qt.UserRole)
                user_index = user_names.index(user)
                task.user = users[user_index]
                self.add_task_items(parent=item.parent())


    # Asset Context Menu
    @update_trees_afterwards
    def delete_asset(self):
        """Deletes the selected item from the database.
        """
        log.debug('Running delete_asset.')
        current_widget=self.overview_tab_container.currentWidget()
        # Tree widget allows only one selected item
        item = current_widget.selectedItems()[0]
        name, ok = QtWidgets.QInputDialog.getText(self, 'Delete Item', 'Enter Asset Name to delete:')
        if ok and name == item.text(0):
            data = item.data(0, QtCore.Qt.UserRole)
            data.delete()


class CommentsList(QtWidgets.QWidget):
    """Widget to display the task changes comments."""

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setLayout(QtWidgets.QVBoxLayout())

    def add_comment_widget(self, text):
        comment = QtWidgets.QLabel()
        comment.setText('{comment}'.format(comment=text))
        comment.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        comment.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        comment.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.layout().addWidget(comment)

    def add_comments_to_layout(self):
        self.clear_layout(layout=self.layout())
        sender = self.sender()
        items = sender.selectedItems()
        for item in items:
            task = item.data(0, QtCore.Qt.UserRole)
            try:
                log.debug('Task: {data}, {comments}'.format(data=task.name, comments=task.comments))
                for c in task.comments:
                    self.add_comment_widget(text=c)
            except Exception as e:
                log.error(e)

    @staticmethod
    def clear_layout(layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


class AssemblyWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.create_layout()
        self.apply_settings()

    def create_layout(self):
        # Layouts
        self.root_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.root_layout)

        # Widgets
        self.project_tree = ProjectTree(parent=self)
        self.comments = CommentsList(parent=self)

        # Build Hirarchy
        self.root_layout.addWidget(self.project_tree)
        self.root_layout.addWidget(self.comments)

        # Connect Signals
        self.project_tree.project_widget.itemClicked.connect(self.comments.add_comments_to_layout)
        self.project_tree.worklist_widget.itemClicked.connect(self.comments.add_comments_to_layout)


    def apply_settings(self):
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)


class MainWindow(QtWidgets.QMainWindow):

    refresh_ui = QtCore.Signal()

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.settings = QtCore.QSettings('Sagenkoenige', 'Tasker')
        self.setWindowTitle('tasker')
        self.setWindowIcon(QtGui.QIcon(TASKER_ICON))
        self.setGeometry(50, 50, 500, 400)
        self.apply_stylesheet()

        self.init_project()

        self.task_manager_widget = AssemblyWidget(parent=self)
        self.setCentralWidget(self.task_manager_widget)

        self.make_menu_bar()
        self.connect_signals()
        self.refresh_ui.emit()
        self.setFocus()

    def make_menu_bar(self):
        menu_bar = self.menuBar()

        new_project_action = QtWidgets.QAction('New Project', self)
        new_project_action.triggered.connect(self.new_project)
        set_project_action = QtWidgets.QAction('Set Project', self)
        set_project_action.triggered.connect(self.set_project)
        new_asset_action = QtWidgets.QAction('New Asset', self)
        new_asset_action.triggered.connect(self.new_asset)
        new_shot_action = QtWidgets.QAction('New Shot', self)
        new_shot_action.triggered.connect(self.new_shot)
        project_menu = menu_bar.addMenu('Project')
        project_menu.addAction(new_project_action)
        project_menu.addAction(set_project_action)
        project_menu.addSeparator()
        project_menu.addAction(new_asset_action)
        project_menu.addAction(new_shot_action)

        new_user_action = QtWidgets.QAction('New User', self)
        new_user_action.triggered.connect(self.new_user)
        set_user_action= QtWidgets.QAction('Set User', self)
        set_user_action.triggered.connect(self.set_user)
        user_menu = menu_bar.addMenu('User')
        user_menu.addAction(new_user_action)
        user_menu.addAction(set_user_action)

        help_action = QtWidgets.QAction('Help', self)
        help_action.triggered.connect(self.show_help)
        about_action= QtWidgets.QAction('About', self)
        about_action.triggered.connect(self.show_about)
        about_menu = menu_bar.addMenu('Help')
        about_menu.addAction(help_action)
        about_menu.addAction(about_action)

    def init_project(self):
        """
        Initialises the UI to use the set project from the last run if still available in the database.
        """
        log.debug('Initialize Project.')
        self._project = None
        last_project = self.settings.value('project')
        if not last_project:
            log.debug('No Project previously set. Please set project before creating assets and shots.')
            return
        log.debug('Last set Project {name}'.format(name=last_project))
        try:
            self._project = tasker.control.get_project_by_name(last_project)
            self.statusBar().showMessage('Project: {project}'.format(project=self._project.name), 5000)
        except:
            log.debug('Last set Project {name} does not exists anymore.'.format(name=last_project))
            pass

    def new_project(self):
        name, ok = QtWidgets.QInputDialog.getText(self, 'New Project', 'New Project Name:')
        if ok and name:
            tasker.control.new_project(name=name)
            self._project = tasker.control.get_project_by_name(name)
            self.settings.setValue('project', self._project)
            self.statusBar().showMessage('New Project: {project}'.format(project=self._project.name), 5000)
            self.refresh_ui.emit()

    def set_project(self):
        projects = tasker.control.get_all_projects()
        log.debug('Available Projects {p}'.format(p=projects))
        project_names = [p.name for p in projects]
        current_project_index = 0
        if self._project:
            log.debug('Current Project {name}'.format(name=self._project))
            current_project_index = project_names.index(self._project.name)
        name, ok = QtWidgets.QInputDialog.getItem(self, 'Set Projects:', 'Available Projects:', project_names, current_project_index, False)
        if ok and name:
            self._project = tasker.control.get_project_by_name(name)
            self.settings.setValue('project', self._project.name)
            self.statusBar().showMessage('Set Project: {project}'.format(project=self._project.name), 5000)
            self.refresh_ui.emit()

    def new_asset(self):
        asset_name, ok = QtWidgets.QInputDialog.getText(self, 'New Asset', 'New Asset Name:')
        if not(ok and asset_name):
            log.info('No asset name given. Aborted creation!')
            return
        template = self.choose_template(category='asset')
        self._project.new_asset(name=asset_name, template=template)
        self.statusBar().showMessage('Created Asset: {asset_name}'.format(asset_name=asset_name), 5000)
        self.refresh_ui.emit()

    def new_shot(self):
        name, ok = QtWidgets.QInputDialog.getText(self, 'New Shot', 'New Shot:')
        if not(ok and name):
            log.info('No shot name given. Aborted creation!')
            return
        template = self.choose_template(category='shot')
        self._project.new_shot(name=name, template=template)
        self.statusBar().showMessage('Created Shot: {shot_name}'.format(shot_name=name), 5000)
        self.refresh_ui.emit()

    def choose_template(self, category):
        default_template = 0
        asset_templates = tasker.control.get_task_templates_by_category_name(category=category)
        template_name, ok = QtWidgets.QInputDialog.getItem(self, 'Select Template:', 'Available Templates:',
                                                           asset_templates.keys(),
                                                           default_template, False)
        if template_name and ok:
            template = asset_templates[template_name]
        log.debug('Choosen Template: {name}'.format(name=template_name))
        return template

    def new_user(self):
        name, ok = QtWidgets.QInputDialog.getText(self, 'Set username', 'Username:')
        if ok and name:
            tasker.control.new_user(name)

    def set_user(self):
        users = tasker.control.get_all_users()
        if not users:
            log.debug('No users in database. Stopping set user.')
            self.statusBar().showMessage('Create Users first!', 5000)
            return None
        user_names = [user.name for user in users]
        log.debug('Available User:{user}'.format(user=user_names))
        current_user = 0
        last_user = self.settings.value('user')
        if last_user and last_user in user_names:
            log.debug('Current User {name}'.format(name=last_user))
            current_user = user_names.index(self.settings.value('user'))
        name, ok = QtWidgets.QInputDialog.getItem(self, 'Set User:', 'Available User:', user_names,
                                                  current_user, False)
        if ok and name:
            self.settings.setValue('user', name)
            self.statusBar().showMessage('Current User: {user}.'.format(user=name), 5000)

    @staticmethod
    def show_help():
        message = QtWidgets.QMessageBox()
        message.setText('No Help yet!')
        message.exec_()

    @staticmethod
    def show_about():
        message = QtWidgets.QMessageBox()
        message.setText('Copyright 2017 Dominik Pott!')
        message.exec_()

    def apply_stylesheet(self):
        with open(STYLESHEET, "r") as stylesheet_file:
            self.setStyleSheet(stylesheet_file.read())

    def connect_signals(self):
        log.debug('Connecting signal refresh_project to project_tree update().')
        self.refresh_ui.connect(self.task_manager_widget.project_tree.update_trees)


def main():
    """Display the ui from within the IDE for faster debugging.
    This shouldn't be used in an application.
    """
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
