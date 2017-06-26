[![Build Status](https://travis-ci.org/DominikPott/tasker.svg?branch=master)](https://travis-ci.org/DominikPott/tasker)
[![Codecov](https://codecov.io/github/DominikPott/tasker/coverage.svg?branch=master)](https://codecov.io/github/DominikPott/tasker?branch=master)
[![Code Climate](https://codeclimate.com/github/DominikPott/tasker/badges/gpa.svg)](https://codeclimate.com/github/DominikPott/tasker)
[![Documentation Status](https://readthedocs.org/projects/tasker/badge/?version=latest)](http://tasker.readthedocs.io/en/latest/?badge=latest)

![tasker](https://github.com/DominikPott/tasker/blob/master/tasker/icons/tasker.png" tasker - taskManagement")

# tasker
A task manager for animation and vfx film projects.

[wiki]:http://tasker.readthedocs.io/en/latest


#### requirement:
- pyhton 2.7+
- qtpy
- sqlalchemy


and if you run it as a standalone tool and NOT from a dcc application like maya, nuke or houdini:
- PyQt5
- PyQt4
- PySide2
- PySide


Example SideEffects Houdini:

    import hou  # Houdini Api
    import tasker.ui as tasker
    houdini_window = hou.ui.mainQtWindow()  # Get the application
    window = tasker.MainWindow(parent=houdini_window)
    window.show()

Example Foundry Nuke:

    import tasker.ui as tasker
    reload(tasker)
    window = tasker.MainWindow()
    window.show()



After that you want to create a new project. To do so go to "Project > New Project".
After that you can create new assets and shots for this project also from the same menu.
To assign users:
- "User>New User"
- right click on the task and choose "assign user"

To change the state of an task:
- right click on an task and choose "set state".
Not all state sets are allowed because tasks are dependend on each other. To see and edit these dependencies
have a look into the template.py There you can define new tasks, task templates and their dependencies.




TODO:
- adding subtasks to existing tasks
- exchange the current state handling implementation with a finite state machine
- increase test coverage