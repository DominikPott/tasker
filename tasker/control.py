"""API for the tasker module.

the :mod:`tasker.control` module contains the api to generate projects and work with tasks.

Example:

>>> import tasker.control
>>> import tasker.templates
>>> tasker.control.new_project(name='test_project')
>>> project = tasker.control.get_project_by_name('test_project')
>>> project.new_asset(name='baum_a')
>>> project.new_shot(name='01_010')
>>> assets = project.assets
>>> baum_a = None
>>> for asset in assets:
>>>     if 'baum_a' in asset.name:
>>>         baum_a = asset
>>> modeling = baum_a.get_task_by_name(name=tasker.templates.modeling)
>>> tasker.control.new_user(name='user1')
>>> user = tasker.control.get_user_by_name(name='user1')
>>> modeling.user=user
>>> state = modeling.state

"""

import datetime

from tasker import log, session_scope
from tasker.model import State, TaskData,CommentData, AssetData, ShotData, LayoutData, ProjectData, UserData

import tasker.templates as templates

__author__ = 'Dominik'
__version__ = '0.1.0'


class Task(object):
    """A ask is a single unit of process and may be chained together with other tasks via dependencies.
    Also a user can be associated with it and subtasks may be added.
    A task may be linked against a shot or asset where it belongs to.
    """

    def __init__(self, model):
        super(Task, self).__init__()
        self.id = model.id
        self.name = model.name
        self.registered_states = State.all_states

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Task Object: {name}, {state}'.format(name=self.name, state=self.state)

    @property
    def user(self):
        """ The user assigned to this task.

        Returns:
            User: which is assigned to this task

        """
        with session_scope() as session:
            task = session.query(TaskData).filter(TaskData.id == self.id).first()
            if task.user:
                return User(task.user)
            return None

    @user.setter
    def user(self, user):
        """Assigns an user to this task.

        Args:
            user(User): the new user which should be assigned to this task.

        """
        with session_scope() as session:
            task_data = session.query(TaskData).filter(TaskData.id == self.id).first()
            user_data = session.query(UserData).filter(UserData.id == user.id).first()
            log.debug('{user} assigned to {task}'.format(user=user_data.name, task=task_data.name))
            task_data.user = user_data

    @property
    def state(self):
        """The current state of the task.
        Returns:
            str: current state
        """
        with session_scope() as session:
            task_data = session.query(TaskData).filter(TaskData.id == self.id).first()
            return task_data.state

    @state.setter
    def state(self, state):
        """Change the state of this task.

        Args:
            state (str): name of the state to set this tasks state to.

        """
        with session_scope() as session:
            task_data = session.query(TaskData).filter(TaskData.id == self.id).first()
            log.info('{task} set to {state}'.format(task=self.name, state=state))
            task_data.state = state
            self._update_self(session=session)
            self.update_depender(session=session)

    def is_state_allowed(self, state):
        """Checks if the task may change its state to the given one.

        Args:
            state (str): name of the new state

        Returns:
            bool: True if state change is allowed. Otherwise False.
        """
        if self._is_new_state_same_as_current_state(new_state=state):
            return False
        if not self._is_state_set_allowed(new_state=state):
            return False
        if not self._are_dependencies_fulfilled():
            return False
        return True

    def _are_dependencies_fulfilled(self):
        """Checks if all dependencies (other tasks) for this task are done."""
        with session_scope() as session:
            task = session.query(TaskData).filter(TaskData.id == self.id).first()
            dependencies = task.dependencies
            if any(dependency.state != State.done for dependency in dependencies):
                log.warning('State set not allowed for {task}. Dependend tasks are not done.'.format(task=self.name))
                return False
            return True

    def _is_state_set_allowed(self, new_state):
        if self.state == State.done and new_state != State.reject:
            log.warning('State {new_state} not allowed for {task}. Task is done. Please reject first to work on task.'.format(task=self.name, new_state=new_state))
            return False
        return True

    def _is_new_state_same_as_current_state(self, new_state):
        if new_state == self.state:
            log.warning('{new_state} identical to current state.'.format(new_state=new_state))
            return True
        return False

    def update_tasks_states(self):
        """Updates states for this tasks and all dependencies.
        If a task state is set, other depending tasks may be ready to start.
        This method update tose and also the database entries.
        """
        with session_scope() as session:
            self._update_self(session=session)
            self.update_depender(session=session)

    def _update_self(self, session):
        task_data = session.query(TaskData).filter(TaskData.id == self.id).first()
        if not task_data.dependencies:  # No previous task so set state to can_start
            if task_data.state == State.pending:
                task_data.state = State.can_start
                log.info("Starting no dependencie task {task}".format(task=self.name))

        if any(dependencie.state == State.reject for dependencie in task_data.dependencies):
            log.info("Locking %s for parent reject" % self.name)
            task_data.state = State.hold
            return

        # all previews task done, start self
        if all(dependencie.state == State.done for dependencie in task_data.dependencies):
            # if already worked on shot, set to update
            if task_data.state == State.hold:
                task_data.state = State.to_continue
                log.info("To continue task %s" % self.name)
                return
            if task_data.state != State.pending:
                return
            log.info("Starting task %s" % self.name)
            task_data.state = State.can_start

    def update_depender(self, session):
        task = session.query(TaskData).filter(TaskData.id == self.id).first()
        for d in task.depender:
            t = Task(d)
            t._update_self(session=session)
            t.update_depender(session=session)

    @property
    def parent(self):
        with session_scope() as session:
            task = session.query(TaskData).filter(TaskData.id == self.id).first()
            parent = task.parent
            if not parent:
                return None
            if isinstance(parent, AssetData):
                return Asset(parent)
            if isinstance(parent, ShotData):
                return Shot(parent)

    @property
    def child_tasks(self):
        """All chilkd/subtasks which belong to this task.

        Returns:
             list(Task): all child tasks

        """
        with session_scope() as session:
            children_task_data = session.query(TaskData).filter(TaskData.parent_task_id == self.id).all()
            return [Task(child_task) for child_task in children_task_data]

    @property
    def comments(self):
        """All comments associated with this tasks. Normaly entered during state changes.

        Returns:
            list(Comment): All comments for this task.

        """
        with session_scope() as session:
            comments = session.query(CommentData).filter(CommentData.task_id==self.id).all()
            return [Comment(c) for c in comments]

    def add_comment(self, text):
        """Associates a new comment with this task.

        Args:
            text (str): comment for this task

        """
        time = datetime.datetime.now()
        with session_scope() as session:
            task_data = session.query(TaskData).filter(TaskData.id == self.id).first()
            task_data.comments.append(CommentData(text=text, datetime=time))


class Comment(object):
    """
    A Comment is associated with a task change and holds the test entered by the user.
    """

    def __init__(self, model):
        super(Comment, self).__init__()
        self.id = model.id
        self.text = model.text
        self.datetime = model.datetime

    def __str__(self):
        return "{date} {text}".format(date=self.datetime.strftime("%Y-%m-%d %H:%M:%S"), text=self.text)


class TaskHolder(object):
    """
    Base class which provides methods for the associated task object.
    """

    def __init__(self, model):
        super(TaskHolder, self).__init__()
        self.id = model.id
        self.name = model.name
        self.model_type = type(model)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{model_type}: {name}'.format(model_type=type(self).__name__, name=self.name)

    def get_task_by_name(self, name):
        for task in self.tasks:
            if task.name == name:
                return task
        else:
            raise KeyError('Task {name} not found in asset tasks'.format(name=name))

    @property
    def tasks(self):
        """All tasks for this item.
        Queries the database for all tasks associated with this item and returns them.

        Returns:
            list(Task): all tasks for this item.

        """
        with session_scope() as session:
            item = session.query(self.model_type).filter(self.model_type.id == self.id).first()
            return [Task(task) for task in item.tasks if not task.parent_task]


class Asset(TaskHolder):
    """Use this class to associate assets to shots, layouts, tasks and projects.

    An asset is a representation of an unit of work for a movie.
    For example: Tree_a is an asset.
    This asset may include some polygonal data, some texture maps and even some animation etc which are all associated
    via folder structures or some database to this asset. To complete an asset, different deparments and tasks are
    infolved which can/may be representet as task.
    """
    def __init__(self, model):
        super(Asset, self).__init__(model=model)


class Shot(TaskHolder):
    def __init__(self, model):
        super(Shot, self).__init__(model=model)


class Layout(object):
    def __init__(self, model):
        self.id = model.id
        self.name = model.name

    def get_assets(self):
        with session_scope() as session:
            assets = session.query(AssetData).filter(AssetData.layouts_id==self.id)


class Project(object):
    """A Project holds tasks, assets and shots. Is is also used for interaction with those.
    Use a project object to generate and interact with task, asstes and shots.

    """

    def __init__(self, model):
        self.id = model.id
        self.name = model.name

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Project Object {project_name}'.format(project_name=self.name)

    @property
    def assets(self):
        """Gets the assets associated with the current project.

        Returns:
            list(Asset): A list of Asset instances for the current project.

        """
        with session_scope() as session:
            assets = session.query(AssetData).filter(AssetData.project_id==self.id)
            return [Asset(asset_data) for asset_data in assets]

    @property
    def shots(self):
        """Get the shots associated with this project.

        Returns:
            list(Shot): Shot instances for all shots in the current project.

        """
        with session_scope() as session:
            shots = session.query(ShotData).filter(ShotData.project_id==self.id)
            return [Shot(shot_data) for shot_data in shots]

    @property
    def layouts(self):
        """Get the layouts associated with this project.

        Returns:
            list(Layouts): layout instances for all layouts in the current project.

        """
        with session_scope() as session:
            layouts = session.query(LayoutData).filter(LayoutData.project_id==self.id)
            return [Layout(layout_data) for layout_data in layouts]

    def new_asset(self, name, template=None):
        """ Creates a new asset with the given name in the project.
        The new shot will use the provided template to generate tasks and dependenciesfor itself.

        Args:
            name (str): name of the new asset. Aborts if an asset with this name already exists.
            template (dict): A configuration file to generate tasks and dependencies for the new asset from.
        """
        log.info('New Asset {name}'.format(name=name))
        if not template:
            log.info('No asset template supplied. Using animation_asset.')
            template = templates.asset['feature_animation_prop_asset']
        tasks = []
        for task_name in template['tasks']:
            tasks.append(TaskData(name=task_name, state=State.can_start))
        for task in tasks:
            log.info('Tasks {task}'.format(task=task.name))
            dependencies = []
            for dependency in template['dependencies'][task.name]:
                dependencies.extend([t for t in tasks if t.name == dependency])
            log.info('Dependencies: {d}'.format(d=[dep.name for dep in dependencies]))
            task.dependencies = dependencies
            if dependencies:
                task.state=State.pending

        asset = AssetData(name=name, tasks=tasks)
        with session_scope() as session:
            project = session.query(ProjectData).filter(ProjectData.id==self.id).first()
            project.assets.append(asset)

    def new_shot(self, name, template=None):
        """ Creates a new shot with the given name in the project.
        The new shot will use the provided template to generate tasks and dependenciesfor itself.

        Args:
            name (str): name of the new shot. Aborts if a shot with this name already exists.
            template (dict): A configuration file to generate tasks and dependencies for the new shot from.

        Returns:

        """
        log.info('New ShotData {name}'.format(name=name))
        if not template:
            log.info('No shot template supplied. Using animation_shot.')
            template = templates.shot['shortfilm_shot']
        tasks = []
        for task_name in template['tasks']:
            tasks.append(TaskData(name=task_name, state=State.can_start))
        for task in tasks:
            log.info('Task: {t}'.format(t=task.name))
            dependencies = []
            for dependency in template['dependencies'][task.name]:
                dependencies.extend([t for t in tasks if t.name == dependency])
            log.info('Dependencies: {d}'.format(d=[dep.name for dep in dependencies]))
            task.dependencies = dependencies
            if dependencies:
                task.state=State.pending

        shot = ShotData(name=name, tasks=tasks)
        with session_scope() as session:
            project = session.query(ProjectData).filter(ProjectData.id==self.id).first()
            project.shots.append(shot)


class User(object):
    """Allows assignment and querying of assignd tasks.

    """

    def __init__(self, model):
        self.id = model.id
        self.name = model.name

    def __str__(self):
        return self.name

    @property
    def tasks(self):
        """Get all tasks for the user.

        Returns:
            list(Task): all tasks which are associated with the user.

        """
        with session_scope() as session:
            tasksData = session.query(TaskData).filter(TaskData.user_id==self.id).all()
            return [Task(taskData) for taskData in tasksData]


def new_project(name):
    """Creates a new project with the given name.

    Create a project to hold tasks, assets and shots.
    Args:
        name (str): name of the new project
    """
    project = ProjectData(name=name)
    with session_scope() as session:
        exists = session.query(ProjectData).filter_by(name=name).first()
        if exists:
            log.warning('Project already exists. Skipping creation.')
            return None
        log.info('Creating new Project {name}'.format(name=name))
        session.add(project)


def get_project_by_name(name):
    """Returns a project instance for the given name if it exists in the database.

    Args:
        name (str): project to find and return

    Returns:
        Project: instance for the given name if exists. Otherwise None
    """
    with session_scope() as session:
        project_model = session.query(ProjectData).filter_by(name=name).first()
        return Project(model=project_model)


def get_all_projects():
    """All projects available in the database.

    Returns:
        list(Project): all projects available in the database

    """
    with session_scope() as session:
        project_models = session.query(ProjectData).all()
        return [Project(model=project_model) for project_model in project_models]


def get_all_tasks(user=None, state=None):
    """All tasks in the database. Optional for the given user and/or state.

    Args:
        user (User): tasks must be assigned to this user to be returned.
        state (str): tasks must have this state to be returned.

    Returns:
        list(Task): all task matching the criteria.

    """
    with session_scope() as session:
        tasks_models = session.query(TaskData)
        if user:
            tasks_models = tasks_models.filter(UserData.id == user.id)
        if state:
            tasks_models = tasks_models.filter_by(state=state)
        tasks_models = tasks_models.all()
        return [Task(model=task_model) for task_model in tasks_models]


def get_task_templates_by_category_name(category):
    """Get the task templates defined in tasker.templates for the given categorie.

    Args:
        category (str): 'shot' or 'asset'

    Returns:
        dict: of registered templates for the given category

    """
    all_templates = templates.templates_by_category
    if category not in all_templates:
        log.error('{category} is not defined in task templates.'.format(category=category))
        raise KeyError
    return all_templates[category]


def new_user(name):
    """Creates a new user in the databse.
    Creates a new user with the given name in the database. If a user with this name exists already creation is skipped.
    Args:
        name (str): name of the new user.

    """
    user = UserData(name=name)
    with session_scope() as session:
        exists = session.query(UserData).filter_by(name=name).first()
        if exists:
            log.warning('User already exists. Skipping creation.')
            return
        log.info('Created new User {name}'.format(name=name))
        session.add(user)


def get_all_users():
    """ Returns all users in the database.

    Returns:
        list(User): all users in the database

    """
    with session_scope() as session:
        users = [User(data) for data in session.query(UserData).all()]
        return users


def get_user_by_name(name):
    """Find a user in the database by it's name.
    Queries the database for the username. If it exists it's returned otherwise a ValueError is raised.
    Args:
        name (str): username to search for

    Returns:
        User: the user with the given name.

    """
    with session_scope() as session:
        user = session.query(UserData).filter_by(name=name).first()
        if not user:
            raise ValueError('Username {user} not in database'.format(user=name))
        return User(model=user)
