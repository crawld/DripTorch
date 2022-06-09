"""
Burn operation personnel
"""

# Core imports
from __future__ import annotations
import copy

# Internal imports
from driptorch.errors import *


class Igniter:
    """An igniter is anything with a velocity and ignition interval, like a person
    carrying a drip torch or a drone dispatching DAIDs.
    """

    # TODO: #5 Write serialization method for Igniter class
    def __init__(self, velocity: float, interval: float, interval_units: str = 'meters'):
        """Constructor computes and stores the interval in ignitions per meter (ipm)
        and ignitions per second (ips).

        Args:
            velocity (float): Speed of the igniter (meters/second)
            interval (float): Ignition interval in ipm (ignitions per meter) or ips (ignitions per second).
                Use the `interval_units` parameter to specifiy meters or seconds. An interval of 0 specifies
                a solid ignition line, while a negative value denotes a dashed ignition line and positve a
                dotted ignition line.
            interval_units (str, optional): Units for the ignition interval, must be "meters" or "seconds".
                Defaults to 'meters'.
        """

        self.velocity = velocity

        # Solid ignition line
        if interval == 0:
            self.interval_ipm = 0
            self.interval_ips = 0

        # Compute ipm and ips for dashes and dots
        elif interval_units == 'seconds':
            self.interval_ipm = interval / velocity
            self.interval_ips = interval
        else:
            self.interval_ipm = interval
            self.interval_ips = interval * velocity

    def copy(self) -> Igniter:
        """Sometimes we need to copy a particular Igniter because they're so good
        at what they do.

        Returns:
            driptorch.Igniter: A copy of the this Ignitor object
        """

        return copy.copy(self)

    def __str__(self):

        return (f'Igniter(velocity={self.velocity}, ' +
                f'interval_ipm={self.interval_ipm}, ' +
                f'interval_ips={self.interval_ips})')


class IgnitionCrew:
    """
    An ignition crew is a collection of igniters. Sometime you may want your igniters
    to all have the same velocity and/or interval. You can specifiy these constraints
    in the constructor.
    """

    # TODO: #2 Include same_interval boolean in constructor of IgnitionCrew and implement validator
    # TODO: #3 Write serialization method for IgnitionCrew object
    # TODO: #4 Improve IgnitionCrew __str__() method

    def __init__(self, same_velocity: bool = True):
        """Constructor

        Args:
            same_velocity (bool, optional): True requires all igniters of an instance
                to have equal velocities. Defaults to True.
        """

        self._same_velocity = same_velocity
        self._velocity_req = None

        self._igniters = []

    @classmethod
    def from_list(cls, igniters: list[Igniter], **kwargs) -> IgnitionCrew:
        """Alternate constructor for building an ignition crew from a list of igniters

        Args:
            igniters (List[Igniter]): List of Igniter objects

        Returns:
            IgnitionCrew: An IgnitionCrew object with igniters from provided list
        """

        ignition_crew = cls(**kwargs)

        # Add igniters from provided list to the crew object
        for igniter in igniters:
            ignition_crew.add_igniter(igniter)

        return ignition_crew

    @classmethod
    def clone_igniter(cls, igniter: Igniter, clones: int) -> IgnitionCrew:
        """Alternate constructor for building an ignition crew by cloning a given
        igniters `n` times.

        Args:
            igniter (Igniter): The Igniter object to clone
            clones (int): Number of clones (number of igniters in crew)

        Returns:
            IgnitionCrew: An IgnitionCrew object with `n` clones of the specified Igniter
        """

        igniters = [igniter.copy() for _ in range(clones)]

        return cls.from_list(igniters)

    def add_igniter(self, igniter: Igniter):
        """Add an igniter to the crew

        Args:
            igniter (Igniter): Igniter object to add to the crew
        """

        # Check the igniter's velocity
        self._validate_velocity(igniter.velocity)

        # If the validator didn't raise an exception, then add the igniter to the crew
        self._igniters.append(igniter)

    def _validate_velocity(self, velocity: float):
        """Private helper method to validate the velcity of the candidate igniter
        against the velocity requirement of the crew.

        Args:
            velocity (float): Velocity of the candidate igniter

        Raises:
            UnequalIgniterVelocity: Exception raised if igniter's velocity is invalid
        """

        if self._same_velocity:
            if self._velocity_req:
                if velocity != self._velocity_req:
                    raise UnequalIgniterVelocity(
                        UnequalIgniterVelocity.unequal_igniter_velocities)
            else:
                self._velocity_req = velocity

    def __getitem__(self, index):

        return self._igniters[index]

    def __len__(self):

        return len(self._igniters)

    def __iter__(self):

        for i in range(self.__len__()):
            yield self._igniters[i]

    def __str__(self):

        print_str = f'IgnitionCrew\n'
        for igniter in self._igniters:
            print_str += f'{igniter}\n'
        return print_str
