"""API for the tasker module.

the :mod:`tasker.control` module contains the api to generate projects and work with tasks.

This file is the api which should be used to work with the tasker module.

- :mod:`tasker.db_cofig`
- :mod:`tasker.templates`


One can use the :func:`tasker.control.new_project` to create a new project in the database to hold tasks relationships
and states.

Example:

>>> import tasker.control
>>> tasker.control.new_project(name='test_project')
"""

import datetime
from contextlib import contextmanager

from tasker import Session, log
from tasker.model import State, TaskData,CommentData, AssetData, ShotData, LayoutData, ProjectData, UserData

import tasker.templates as templates

__author__ = 'Dominik'
__version__ = '0.1.0'

@contextmanager
def session_scope():
    """Provides a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class Task(object):
    """Task function object for handeling and manipulating taskData objects."""

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
        with session_scope() as session:
            task = session.query(TaskData).filter(TaskData.id == self.id).first()
            if task.user:
                return User(task.user)
            return None

    @user.setter
    def user(self, user):
        with session_scope() as session:
            task_data = session.query(TaskData).filter(TaskData.id == self.id).first()
            user_data = session.query(UserData).filter(UserData.id == user.id).first()
            log.debug('{user} assigned to {task}'.format(user=user_data.name, task=task_data.name))
            task_data.user = user_data

    @property
    def state(self):
        with session_scope() as session:
            task_data = session.query(TaskData).filter(TaskData.id == self.id).first()
            return task_data.state

    @state.setter
    def state(self, state):
        with session_scope() as session:
            task_data = session.query(TaskData).filter(TaskData.id == self.id).first()
            log.info('{task} set to {state}'.format(task=self.name, state=state))
            task_data.state = state
            self._update_self(session=session)
            self.update_depender(session=session)

    def is_state_allowed(self, state):
        if self._is_new_state_same_as_current_state(new_state=state):
            return False
        if not self._is_state_set_allowed(new_state=state):
            return False
        if not self._are_dependencies_fulfilled():
            return False
        return True

    def _are_dependencies_fulfilled(self):
        """Checks if all dependencies for the given task are done."""
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
        with session_scope() as session:
            children_task_data = session.query(TaskData).filter(TaskData.parent_task_id == self.id).all()
            return [Task(child_task) for child_task in children_task_data]

    @property
    def comments(self):
        with session_scope() as session:
            comments = session.query(CommentData).filter(CommentData.task_id==self.id).all()
            return [Comment(c) for c in comments]

    def add_comment(self, text):
        time = datetime.datetime.now()
        with session_scope() as session:
            task_data = session.query(TaskData).filter(TaskData.id == self.id).first()
            task_data.comments.append(CommentData(text=text, datetime=time))


class Comment(object):
    """
    Wraps to recive database comment objects.
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
    Base class which provides base functionality to return associated task objects.
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
        with session_scope() as session:
            asset = session.query(self.model_type).filter(self.model_type.id == self.id).first()
            return [Task(task) for task in asset.tasks if not task.parent_task]


class Asset(TaskHolder):
    """
    Asset control for AssetModels. Use this class to associate assets to shots, layouts and tasks.
    :param model: taskManager.model.AssetData
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
    """Used to control the ProjectModel from the database.
    It should handle asset and shot creation and most functions which needs an association to the actual project.
    :param model.ProjectModel: data for the current object from the database.
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
        with session_scope() as session:
            assets = session.query(AssetData).filter(AssetData.project_id==self.id)
            return [Asset(asset_data) for asset_data in assets]

    @property
    def shots(self):
        with session_scope() as session:
            shots = session.query(ShotData).filter(ShotData.project_id==self.id)
            return [Shot(shot_data) for shot_data in shots]

    @property
    def layouts(self):
        with session_scope() as session:
            layouts = session.query(LayoutData).filter(LayoutData.project_id==self.id)
            return [Layout(layout_data) for layout_data in layouts]

    def new_asset(self, name, template=None):
        log.info('New Asset {name}'.format(name=name))
        if not template:
            log.info('No asset template supplied. Using animation_asset.')
            template = templates.asset['animation_prop_asset']
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
        log.info('New ShotData {name}'.format(name=name))
        if not template:
            log.info('No shot template supplied. Using animation_shot.')
            template = templates.shot['animation_shot']
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
    """Control class for model.UserData instances.
    Allows assignment and querying of assignd tasks.
    """

    def __init__(self, model):
        self.id = model.id
        self.name = model.name

    def __str__(self):
        return self.name

    @property
    def tasks(self):
        with session_scope() as session:
            tasksData = session.query(TaskData).filter(TaskData.user_id==self.id).all()
            return [Task(taskData) for taskData in tasksData]


def new_project(name):
    project = ProjectData(name=name)
    with session_scope() as session:
        exists = session.query(ProjectData).filter_by(name=name).first()
        if exists:
            log.warning('Project already exists. Skipping creation.')
            return None
        log.info('Creating new Project {name}'.format(name=name))
        session.add(project)


def get_project_by_name(name):
    with session_scope() as session:
        project_model = session.query(ProjectData).filter_by(name=name).first()
        return Project(model=project_model)


def get_all_projects():
    with session_scope() as session:
        project_models = session.query(ProjectData).all()
        return [Project(model=project_model) for project_model in project_models]


def get_all_tasks(user=None, state=None):
    with session_scope() as session:
        tasks_models = session.query(TaskData)
        if user:
            tasks_models = tasks_models.filter(UserData.id == user.id)
        if state:
            tasks_models = tasks_models.filter_by(state=state)
        tasks_models = tasks_models.all()
        return [Task(model=task_model) for task_model in tasks_models]


def get_task_templates_by_category_name(category):
    all_templates = templates.templates_by_category
    if category not in all_templates:
        log.error('{category} is not defined in task templates.'.format(category=category))
        raise KeyError
    return all_templates[category]


def new_user(name):
    user = UserData(name=name)
    with session_scope() as session:
        exists = session.query(UserData).filter_by(name=name).first()
        if exists:
            log.warning('User already exists. Skipping creation.')
            return None
        log.info('Created new User {name}'.format(name=name))
        session.add(user)


def get_all_users():
    with session_scope() as session:
        users = [User(data) for data in session.query(UserData).all()]
        return users


def get_user_by_name(name):
    with session_scope() as session:
        user = session.query(UserData).filter_by(name=name).first()
        if not user:
            raise ValueError('Username {user} not in database'.format(user=name))
        return User(model=user)


if __name__ == '__main__':
    d = get_user_by_name(name='phil')
    print(d.name)
    for t in d.tasks:
        print(t)

    ps = get_all_projects()
    print(ps)
    me = get_project_by_name(name='me')
    print(me.assets)
    print(me.shots)
    for asset in me.assets:
        print(asset)
        print(asset.tasks)