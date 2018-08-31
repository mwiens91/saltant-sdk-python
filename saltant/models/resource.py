"""Contains base classes for models and related classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from saltant.exceptions import BadHttpRequestError


class ModelManager(object):
    """Base class for a model manager.

    Attributes:
        _client (:py:class:`saltant.client.Client`): An authenticated
            saltant client.
        list_url (str): The URL to list models.
        detail_url (str): The URL format to get specific models.
    """
    list_url = "NotImplemented"
    detail_url = "NotImplemented"

    def __init__(self, _client):
        """Save the client so we can make API calls in the manager.

        Args:
            _client (:py:class:`saltant.client.Client`): An
                authenticated saltant client.
        """
        self._client = _client

    def list(self):
        """List instances of models."""
        raise NotImplementedError

    def get(self):
        """Get a specific instance of a model."""
        raise NotImplementedError

    def create(self):
        """Create an instance of a model."""
        raise NotImplementedError

    @staticmethod
    def validate_request_success(
            request_url,
            status_code,
            expected_status_code,):
        """Validates that a request was successful.

        Args:
            request_url (str): The URL the request was made at.
            status_code (int): The status code of the response.
            expected_status_code (int): The expected status code of the
                response.

        Raises:
            :py:class:`saltant.exceptions.BadHttpRequestError`: The HTTP
                request failed.
        """
        try:
            assert status_code == expected_status_code
        except AssertionError:
            msg = "Request to {} failed with status {}".format(
                request_url,
                status_code,)
            raise BadHttpRequestError(msg)


class Model(object):
    """Base class for representing a model."""
    def __str__(self):
        """String representation of model."""
        raise NotImplementedError