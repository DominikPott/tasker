"""Data structures and bindings to work with sql alchemy.

:mod:`tasker.model` this module holds datastrucktures which are placed in the project database.
They shouldn't be accessed directly only through the :mod:`tasker.control` functions.
"""

from sqlalchemy import Table, Column, ForeignKey, Integer, String, DateTime,  create_engine
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.ext.associationproxy import association_proxy

from tasker.db_config import database

__author__ = 'Dominik'

class State(object):
    '''
    Class to hold integer task states.
    It also provides a bidirectional converter between task integer and a nice name.
    '''

    # atomic states for single tasks and workflows
    pending = 'pending on other tasks'
    can_start = 'waiting to start'
    work_in_progress = 'work in progress'
    to_continue = 'to be continue'
    done = 'done'
    reject = 'rejected'
    hold = 'on hold'
    omit = 'omit'

    all_states = [pending, can_start, work_in_progress, to_continue, done, reject, hold, omit]


@as_declarative()
class Base(object):
    @declared_attr
    def __tablename__(cls):
        cls_name = cls.__name__.lower()
        name, _ = cls_name.rsplit('data', 1)
        return name
    id = Column(Integer, primary_key=True)

#mapping tables for taskData self reliant dependencie and depender mapping
task_to_task = Table('task_to_task', Base.metadata,
                     Column('left_task_id', Integer, ForeignKey('task.id'), primary_key=True),
                     Column('right_task_id', Integer, ForeignKey('task.id'), primary_key=True))


asset_to_layout= Table('asset_to_layout', Base.metadata,
                        Column('layout_id', Integer, ForeignKey('layout.id')),
                        Column('asset_id', Integer, ForeignKey('asset.id')),
                        )


shots_to_layouts = Table('shots_to_layouts', Base.metadata,
                         Column('shot_id', Integer, ForeignKey('shot.id')),
                         Column('layout_id', Integer, ForeignKey('layout.id')),
                         )

class TaskAssociation(Base):
    __tablename__ = 'task_association'
    discriminator = Column(String)
    __mapper_args__ = {'polymorphic_on' : discriminator}


class TaskData(Base):
    id = Column(Integer, primary_key=True)
    state = Column(String)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('UserData', back_populates='tasks')
    comments = relationship('CommentData',
                            cascade="all, delete-orphan",
                            )


    # Associate multiple parents with the taskData. Example: http://docs.sqlalchemy.org/en/latest/_modules/examples/generic_associations/discriminator_on_association.html
    association_id=Column(Integer, ForeignKey('task_association.id'))
    association = relationship('TaskAssociation',cascade="all, delete-orphan",single_parent=True, backref = 'tasks')
    parent = association_proxy('association', 'parent')


    # many to many self-reliant mapping for task dependencies. Example: http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html
    dependencies = relationship("TaskData",
                                secondary=task_to_task,
                                primaryjoin=id == task_to_task.c.left_task_id,
                                secondaryjoin=id == task_to_task.c.right_task_id,
                                backref="depender")

    # one to many self-reliant mapping for subtasks for the current taskData. Example: http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html
    parent_task_id = Column(Integer, ForeignKey('task.id'))
    parent_task = relationship('TaskData',
                               remote_side=[id],
                               backref='child_tasks')



class HasTasks(object):
    @declared_attr
    def task_association_id(cls):
        return Column(Integer, ForeignKey('task_association.id'))

    @declared_attr
    def task_association(cls):
        name = cls.__name__
        discriminator = name.lower()

        assoc_cls = type('%sTaskAssociation' % name,
                         (TaskAssociation, ),
                         dict(
                             __tablename__=None,
                             __mapper_args__ = {
                                 'polymorphic_identity' : discriminator
                             }
                         )
                         )

        cls.tasks = association_proxy(
            'task_association', 'tasks',
            creator = lambda tasks: assoc_cls(tasks=tasks)
        )

        return relationship(assoc_cls,
                            backref=backref('parent', uselist=False))


class CommentData(Base):
    id = Column(Integer, primary_key=True)
    text = Column(String(200), nullable=False)
    datetime = Column(DateTime)
    task_id = Column(Integer, ForeignKey('task.id'))


class AssetData(HasTasks, Base):
    name = Column(String(150), nullable=False)
    layouts = relationship('LayoutData',
                           secondary=asset_to_layout,
                           back_populates='assets')
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('ProjectData',
                           back_populates='assets')


class ShotData(HasTasks, Base):
    name = Column(String(50), nullable=False)

    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('ProjectData', back_populates='shots')

    layouts = relationship('LayoutData',
                           secondary=shots_to_layouts,
                           back_populates='shots')


class LayoutData(Base):
    __tablename__ = 'layout'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('ProjectData', back_populates='layouts')

    assets = relationship("AssetData",
                          secondary=asset_to_layout,
                          back_populates='layouts')

    shots = relationship('ShotData',
                         secondary=shots_to_layouts,
                         back_populates='layouts'
                         )


class ProjectData(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    assets = relationship('AssetData',
                          back_populates='project',
                          )

    shots = relationship('ShotData',
                         back_populates='project'
                         )

    layouts = relationship('LayoutData',
                         back_populates='project'
                         )


class UserData(Base):
    name=Column(String(20), nullable=False)
    tasks = relationship('TaskData',
                         back_populates='user'
                         )

engine = create_engine(database)
Base.metadata.create_all(engine)
