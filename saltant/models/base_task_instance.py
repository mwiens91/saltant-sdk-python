"""Base class for task instance models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import json
import dateutil.parser
from saltant.constants import (
    HTTP_200_OK,
    HTTP_201_CREATED,
)
from .resource import Model, ModelManager


class BaseTaskInstance(Model):
    """Base model for a task instance.

    Attributes:
        name (str): The name of the task instance.
        uuid (str): The UUID of the task instance.
        state (str): The state of the task instance.
        user (str): The username of the user who started the task.
        task_queue (int): The ID of the task queue the instance is
            running on.
        task_type (int): The ID of the task type for the instance.
        datetime_created (:class:`datetime.datetime`): The datetime when
            the task instance was created.
        datetime_finished (:class:`datetime.datetime`): The datetime
            when the task instance finished.
        arguments (dict): The arguments the task instance was run with.
    """
    def __init__(
            self,
            uuid,
            state,
            user,
            task_queue,
            task_type,
            datetime_created,
            datetime_finished,
            arguments,
            name="",):
        """Initialize a task instance.

        Args:
            uuid (str): The UUID of the task instance.
            state (str): The state of the task instance.
            user (str): The username of the user who started the task.
            task_queue (int): The ID of the task queue the instance is
                running on.
            task_type (int): The ID of the task type for the instance.
            datetime_created (:class:`datetime.datetime`): The datetime
                when the task instance was created.
            datetime_finished (:class:`datetime.datetime`): The datetime
                when the task instance finished.
            arguments (dict): The arguments the task instance was run
                with.
            name (str, optional): The name of the task instance.
                Defaults to an empty string.
        """
        self.name = name
        self.uuid = uuid
        self.state = state
        self.user = user
        self.task_queue = task_queue
        self.task_type = task_type
        self.datetime_created = datetime_created
        self.datetime_finished = datetime_finished
        self.arguments = arguments

    def __str__(self):
        """String representation of the task instance."""
        return self.uuid


class BaseTaskInstanceManager(ModelManager):
    """Base manager for task instances.

    Attributes:
        _client (:py:class:`saltant.client.Client`): An authenticated
            saltant client.
        list_url (str): The URL to list task instances.
        detail_url (str): The URL format to get specific task instances.
        model (:py:class:`saltant.models.resource.Model`): The model of
            the task instance being used.
    """
    model = BaseTaskInstance

    def get(self, uuid):
        """Get the task instance.

        Args:
            uuid (str): The UUID of the task instance to get.

        Returns:
            :obj:`saltant.models.base_task_instance.BaseTaskInstance`:
                A task instance model instance representing the task
                instance requested.
        """
        # Get the object
        request_url = (
            self._client.base_api_url
            + self.detail_url.format(uuid=uuid))

        response = self._client.session.get(request_url)

        # Validate that the request was successful
        self.validate_request_success(
            response_text=reponse.text,
            request_url=request_url,
            status_code=response.status_code,
            expected_status_code=HTTP_200_OK,)

        # Return a model instance representing the task instance
        return self.response_data_to_model_instance(response.json())

    def list(self, query_filters=None):
        """List task instances.

        Currently this gets *everything* and iterates through all
        possible pages in the API. This may be unsuitable for production
        environments with huge databases, so finer grained page support
        should likely be added at some point.

        Args:
            query_filters (dict, optional): API query filters to apply
                to the request.  For example,

                {'name__startswith': 'azure',
                 'user__in': [1, 2, 3, 4],}

        Returns:
            list: A list of :py:class:`saltant.models.resource.Model`
                instances matching the query parameters
        """
        # Add in the page and page_size parameters to the filter, such
        # that our request gets *all* objects in the list. However,
        # don't do this if the user has explicitly included these
        # parameters in the filter.
        if not query_filters:
            query_filters = {}

        if page not in query_filters:
            query_filters['page'] = 1

        if page_size not in query_filters:
            # The below "magic number" is the 2^63 - 1, which is the
            # largest number you can hold in a 64 bit integer.
            query_filters['page_size'] = 9223372036854775807

        # Form the request URL - first add in the query filters
        query_filter_sub_url = ''

        for idx, filter_param in enumerate(query_filters):
            # Prepend '?' or '&'
            if idx == 0:
                query_filter_sub_url += '?'
            else:
                query_filter_sub_url += '&'

            # Add in the query filter
            query_filter_sub_url += '{param}={val}'.format(
                param=filter_param,
                val=query_filters[filter_param],
            )

        # Stitch together all sub-urls
        request_url = (
            self._client.base_api_url
            + self.list_url
            + query_filter_sub_url)

        # Make the request
        response = self._client.session.get(request_url)

        # Validate that the request was successful
        self.validate_request_success(
            response_text=reponse.text,
            request_url=request_url,
            status_code=response.status_code,
            expected_status_code=HTTP_200_OK,)

        # Return a model instance representing the task instance
        # TODO: run this through a for loop
        return self.response_data_to_model_instance(response.json())

    def create(self,
               task_type_id,
               task_queue_id,
               arguments=None,
               name="",):
        """Create a task instance.

        Args:
            task_type_id (int): The ID of the task type to base the task
                instance on.
            task_queue_id (int): The ID of the task queue to run the job
                on.
            arguments (dict, optional): The arguments to give the task
                type.
            name (str, optional): A non-unique name to give the task
                instance.

        Returns:
            :obj:`saltant.models.base_task_instance.BaseTaskInstance`:
                A task instance model instance representing the task
                instance just created.
        """
        # Make arguments an empty dictionary if None
        if not arguments:
            arguments = {}

        # Create the object
        request_url = self._client.base_api_url + self.list_url
        data_to_post = {
            "name": name,
            "arguments": json.dumps(arguments),
            "task_type": task_type_id,
            "task_queue": task_queue_id,}

        response = self._client.session.post(request_url, data=data_to_post)

        # Validate that the request was successful
        self.validate_request_success(
            response_text=response.text,
            request_url=request_url,
            status_code=response.status_code,
            expected_status_code=HTTP_201_CREATED,)

        # Return a model instance representing the task instance
        return self.response_data_to_model_instance(response.json())

    @classmethod
    def response_data_to_model_instance(cls, response_data):
        """Convert response data to a task instance model.

        Args:
            response_data (dict): The data from the request's response.

        Returns:
            :py:obj:`saltant.models.resource.Model`:
                A model instance representing the task instance from the
                reponse data.
        """
        # Coerce datetime strings into datetime objects
        response_data['datetime_created'] = (
            dateutil.parser.parse(response_data['datetime_created']))

        if response_data['datetime_finished']:
            response_data['datetime_finished'] = (
                dateutil.parser.parse(response_data['datetime_finished']))

        # Instantiate a model for the task instance
        return cls.model(**response_data)
