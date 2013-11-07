# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import urllib
import tank
import uuid
import sys

from tank.platform.qt import QtCore, QtGui

class ShotgunAsyncDataRetriever(QtCore.QThread):
    """
    Background worker class
    """
    
    work_completed = QtCore.Signal(str, dict)
    work_failure = QtCore.Signal(str, str)
    
    queue_processing = QtCore.Signal()
    queue_complete = QtCore.Signal()
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtCore.QThread.__init__(self, parent)
        
        self._app = tank.platform.current_bundle()
        self._execute_tasks = True
        self._wait_condition = QtCore.QWaitCondition()
        self._queue_mutex = QtCore.QMutex()
        self._queue = []
        
    def stop(self):
        """
        Stops the worker, run this before shutdown
        """
        self._execute_tasks = False
        self._wait_condition.wakeAll()
        self.wait()        
        
    def execute_find(self, entity_type, filters, fields):    
        """
        
        """
        uid = uuid.uuid4().hex
        
        work = {"id": uid, "type": "find", "et": entity_type, "filters": filters, "fields": fields }
        self._queue_mutex.lock()
        try:
            # first in the queue
            self._queue.insert(0, work)
        finally:
            self._queue_mutex.unlock()
            
        # wake up execution loop!
        self._wait_condition.wakeAll()
        
        return uid
        
        
    def download_thumbnail(self, url):
        """
        Downloads a thumbnail from the internet
        """
        pass

    ############################################################################################
    #

    def run(self):

        while self._execute_tasks:
            
            # get the next item to process:
            item_to_process = None
            self._queue_mutex.lock()
            try:
                if len(self._queue) == 0:
                    
                    # nothing to do. Pausing.
                    self.queue_complete.emit()
                    
                    # wait for some more work - this unlocks the mutex
                    # until the wait condition is signalled where it
                    # will then attempt to obtain a lock before returning
                    self._wait_condition.wait(self._queue_mutex)
                    
                    if len(self._queue) == 0:
                        # still nothing in the queue!
                        continue
                    else:
                        # we got stuff to process
                        self.queue_processing.emit()
                    
                item_to_process = self._queue.pop(0)
            finally:
                self._queue_mutex.unlock()

            # ok, have something to do so lets do it:
            data = None
            try:
                # process the item:
                if item_to_process["type"] == "find":
                    data = self._app.shotgun.find(item_to_process["et"],
                                                  item_to_process["filters"],
                                                  item_to_process["fields"])
                
            except Exception, e:
                if self._execute_tasks:
                    self.work_failure.emit(item_to_process["id"], "An error occured: %s" % e)
            else:
                if self._execute_tasks:
                    self.work_completed.emit(item_to_process["id"], data)
                