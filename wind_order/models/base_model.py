# -*- coding: utf-8 -*-
"""
Base class inherited by all calculation models

@author: 36719
"""

from collections import OrderedDict


class Base:
    def __init__(self, **inputs):
        # Dictionary of inputs
        self._inputs = OrderedDict(**inputs)
        # Dictionary of outputs
        self._outputs = OrderedDict()

    def model_type(self):
        """
        Get the class name from a model instance
        :return: string that is the class name of this model instance
        """
        return str(self.__class__.__name__)

    def regulate(self):
        """
        Regularized the inputs to make sure the inputs available
        """

    def run(self):
        """
        Calculate a set of output values as a function of set of input values
        Raising an Error if run() method have not defined in the instance of models
        :return: a dictionary of values
        """

        raise NotImplementedError("WARNING: Model base class calculate called on model of type: " + self.model_type()
                                  + ". Has a calculate method been implemented in the child model?")

    def pop(self):
        """
        Return outputs of model after run
        :return:
        """
        return self._outputs
