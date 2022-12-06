ShotGrid Loader API reference
#############################

Loader API
==========

The loader API gives developers access the underlying data structures and
methods used by the loader UI to manage actions. They can use this interface to build more
advanced custom load workflows.

The main interface of the API is the :ref:`loader-api-manager` class which exposes the methods that drive the Loader UI
for the actions management.

The code below shows how to execute a suite of actions using this API:

.. code-block:: python

    # need to have an engine running in a context where the loader has been
    # configured.
    engine = sgtk.platform.current_engine()

    # get the loader app instance from the engine's list of configured apps
    loader_app = engine.apps.get("tk-multi-loader2")

    # ensure we have the loader instance.
    if not loader_app:
        raise Exception("The loader is not configured for this context.")

    # create a new loader manager instance
    manager = loader_app.create_loader_manager()

    # use case 1: retrieve the actions for a single publish and execute a specific action
    loader_actions = manager.get_actions_for_publish(publish, manager.UI_AREA_MAIN)

    for action in loader_actions:
        if action["name"] == "my_action":
            manager.execute_action(publish, action)

    # use case 2: retrieve the common actions between many publishes and execute one of these action for all the publishes
    loader_actions = manager.get_actions_for_publishes(publishes, manager.UI_AREA_MAIN)

    reference_actions = loader_actions.get("my_action")
    if reference_actions:
        manager.execute_multiple_actions(reference_actions)

See the documentation for each of these classes below for more detail on how
to use them.

.. _loader-api-manager:

LoaderManager
--------------

This class gives developers direct access to the same methods and data
structures used by the Loader UI to manage actions. You can create an instance of this class
directly via the configured loader app like this:

.. code-block:: python

    # need to have an engine running in a context where the publisher has been
    # configured.
    engine = sgtk.platform.current_engine()

    # get the loader app instance from the engine's list of configured apps
    loader_app = engine.apps.get("tk-multi-loader2")

    # ensure we have the loader instance.
    if not loader_app:
        raise Exception("The loader is not configured for this context.")

    # create a new loader manager instance
    manager = loader_app.create_loader_manager()

.. py:currentmodule:: tk_multi_loader.api

.. autoclass:: LoaderManager
    :members:
