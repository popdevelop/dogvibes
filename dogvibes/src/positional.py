#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.db import models, transaction
from django.db.models.fields import FieldDoesNotExist

class InjectingModelBase(models.base.ModelBase):
    """This helper metaclass is used by PositionalSortMixIn.
    This metaclass injects the additional IntegerField position,
    which holds the information about the position of the item
    in the list."""

    def __new__(cls, name, bases, attrs):
        """Metaclass constructor calling Django and then modifying
        the resulting class"""
        # get the class which was alreeady built by Django
        child = models.base.ModelBase.__new__(cls, name, bases, attrs)

        # try to add some more or less neccessary fields
        try:
            # add the IntegerField
            position_field = models.IntegerField(editable=False, unique=True)
            try:
                # try to get the `position` field
                child._meta.get_field('position')
            except FieldDoesNotExist:
                # it was not found - create it now
                child.add_to_class('position', position_field)

        except AttributeError:
            # add_to_class was not yet added to the class.
            # No problem, this is called twice by Django, add_to_class
            # will appear later
            pass
        # we're done - output the class, it's ready for use
        return child

class PositionalSortMixIn(object):
    """This mix-in class implements a user defined order in the database.
    To apply this mix-in you need to inherit from it before you inherit
    from `models.Model`. It adds an IntegerField called `position` to your
    model. Be careful, it overwrites any existing field that you might have
    defined. Additionally, this mix-in changes the default ordering
    behavior to order by the position field.

    Take care: your model needs to have a manager which returns all objects
    set as default manager, that is, the first defined manager. It does not
    need tp be named `objects`. Future versions of this Mixin may inject its
    own, private manager"""
    # get a metaclass which injects the neccessary fields
    __metaclass__ = InjectingModelBase

    def __init__(self, *args, **kwargs):
        """Initialize the class and set up some magic"""
        # call the parent - the ensure it behaves exactly like
        # the original model
        models.Model.__init__(self, *args, **kwargs)

        # set position as the first field to order.
        # of course this gets overridden when using database queries which
        # request another ordering method (order_by)
        if 'position' not in self._meta.ordering:
            self._meta.ordering = ['position'] + list(self._meta.ordering)

    def get_object_at_offset(self, offset):
        """Get the object whose position is `offset` positions away
        from it's own."""
        # get the class in which this was mixed in
        model_class = self.__class__
        try:
            return model_class._default_manager.filter(playlist=self.playlist, position=self.position+offset)
        except model_class.DoesNotExist:
            # no such model? no deal, just return None
            return None

    # some shortcuts, convenience methods
    get_next = lambda self: self.get_object_at_offset(1)
    get_previous = lambda self: self.get_object_at_offset(-1)

    @transaction.commit_on_success
    def move_down(self):
        """Moves element one position down"""
        model_class = self.__class__
        # get the element after this one
        one_after = self.get_next()

        if not one_after:
            # already the last element
            return

        # flip the positions
        # a spare position field is needed
        final = model_class._default_manager.filter(playlist=self.playlist).order_by('-position')[0].position + 1
        # move the object after this one to the bottom of the list
        one_after.position = final
        one_after.save()
        # move this object one down
        self.position += 1
        self.save()
        # move the element that was after this one before this one now
        one_after.position = self.position - 1
        one_after.save()

    @transaction.commit_on_success
    def move_up(self):
        """Moves element one position up"""
        model_class = self.__class__
        # get the element before this one
        one_before = self.get_previous()

        if not one_before:
            # already the first
            return

        # flip the positions:
        # first get a spare position field
        final = model_class._default_manager.filter(playlist=self.playlist).order_by('-position')[0].position + 1
        # move the object that was before to the exact last position
        one_before.position = final
        one_before.save()
        # now, move this object one position up
        self.position -= 1
        self.save()
        # finally, move the object that was before to the position after this object
        one_before.position = self.position + 1
        one_before.save()

    @transaction.commit_on_success
    def insert_before(self, other):
        """Inserts an object in the database so that the objects will be ordered just
        behind the `other` object - this has to be of the same type, of course"""
        # we only need to call another method and prepare the proper parameters
        self.insert_at(other.position)

    @transaction.commit_on_success
    def insert_after(self, other):
        """Inserts an object in the database so that the objects will be ordered just
        behind the `other` object - this has to be of the same type, of course"""
        # we only need to call another method and prepare the proper parameters
        self.insert_at(other.position + 1)

    @transaction.commit_on_success
    def insert_at(self, position):
        """Saves the object at a specified position.
        The `position` field """
        # get the class reference
        model_class = self.__class__
        # the position in what we want to put this in
        self.position = position
        # get all the objects which are at or after the currrent position
        # order them from back to front because of the unique `position` constraint
        objects_after = model_class._default_manager.filter(playlist=self.playlist, position__gte=position).order_by('-position')
        for element in objects_after:
            element.position += 1
            element.save()
        self.save()

    @transaction.commit_on_success
    def swap_position(self, other):
        """Swaps the position with some other class instance"""
        # save the current position
        current_position = self.position
        # set own position to special, temporary position
        self.position = -1
        self.save()
        self.position, other.position = other.position, current_position
        for obj in (other, self):
            obj.save()

    def save(self, force_insert=True):
        """Saves the model to the database.
        It populates the `position` field of the model automatically if there
        is no such field set. In this case, the element will be appended at
        the end of the list."""
        # Note: force_insert is necglected!
        model_class = self.__class__
        # is there a position saved? (explicitly testing None because 0 would be false as well)
        if self.position == None:
            # no, it was empty. Find one
            try:
                # get the last object
                last = model_class._default_manager.filter(playlist=self.playlist).order_by('-position')[0]
                # the position of the last element
                if last.position == None:
                    self.position = 0
                else:
                    self.position = last.position + 1
            except IndexError:
                # IndexError happened: the query did not return any objects
                # so this has to be the first
                self.position = 0

        # save the now properly set-up model
        return models.Model.save(self)

    def delete(self):
        """Deletes the item from the list."""
        model_class = self.__class__
        # get all objects with a position greater than this objects position
        objects_after = model_class._default_manager.filter(playlist=self.playlist, position__gt=self.position)
        # now we remove this model instance
        # so the `position` is free and other instances can fill this gap
        models.Model.delete(self)

        # iterate through all objects which were found
        for element in objects_after:
            # decrease the position in the list (means: move forward)
            element.position -= 1
            element.save()
