#! /usr/bin/env python

import roslib
roslib.load_manifest('free_gait_python')
from math import cos, sin
import rospy
import tf
import actionlib
import free_gait_msgs.msg
import geometry_msgs.msg
import trajectory_msgs.msg
import std_msgs.msg
import locomotion_controller_msgs.srv
import traceback
from actionlib_msgs.msg import *
from free_gait import *
from os import listdir
from os.path import *
import threading

global client

class ActionLoader:

    def __init__(self):
        self.action_server_topic = '/loco_free_gait/execute_steps'
        self.request = None
        self._load_parameters()
        self.client = actionlib.SimpleActionClient(self.action_server_topic, free_gait_msgs.msg.ExecuteStepsAction)
        self.action = None

    def _load_parameters(self):
        self.action_server_topic = rospy.get_param('~action_server')
        self.directory = rospy.get_param('~directory')

    def list_actions(self, request):
        actions = [ f for f in listdir(self.directory) if isfile(join(self.directory, f)) ]
        actions.sort()
        response = locomotion_controller_msgs.srv.GetAvailableControllersResponse(actions)
        return response

    def send_action(self, request, single_action=False):
        self.reset()
        self.request = request
        response = locomotion_controller_msgs.srv.SwitchControllerResponse()
        file_path = self._get_path(request.name)
        file_type = splitext(request.name)[-1]
        if file_path is None:
            rospy.logerr('Action with name "' + request.name + '" does not exists.')
            response.status = response.STATUS_NOTFOUND
        else:
            try:
                if file_type == '.yaml':
                    self._load_yaml_action(file_path)
                elif file_type == '.py':
                    self._load_python_action(file_path)

                self.action.wait_for_result()

                if self.action.result is None:
                    response.status = response.STATUS_ERROR
                    rospy.logerr('An error occurred while reading the action.')
                    return response

                if self.action.result.status == free_gait_msgs.msg.ExecuteStepsResult.RESULT_FAILED:
                    response.status = response.STATUS_ERROR
                    rospy.logerr('An error occurred while executing the action.')
                    return response

                if self.action.keep_alive:
                    rospy.loginfo("Action continues in the background.")
                else:
                    rospy.loginfo('Action successfully executed.')
                response.status = response.STATUS_SWITCHED

                if not self.action.keep_alive and single_action:
                    rospy.signal_shutdown("Action sent, shutting down.")
            except:
                rospy.logerr('An exception occurred while reading the action.')
                response.status = response.STATUS_ERROR
                rospy.logerr(traceback.print_exc())

        return response

    def _get_path(self, file):
        directory = rospy.get_param('~directory')
        file_path = abspath(join(directory, file))
        if not isfile(file_path):
            return None
        return file_path

    def _load_yaml_action(self, file_path):
        # Load action from YAML file.
        rospy.loginfo('Loading free gait action from YAML file "' + file_path + '".')
        goal = load_action_from_file(file_path)
        rospy.logdebug(goal)
        if goal is None:
            rospy.logerr('Could not load action from YAML file.')
        self.action = SimpleAction(self.client, goal)

    def _load_python_action(self, file_path):
        # Load action from Python script.
        rospy.loginfo('Loading free gait action from Python script "' + file_path + '".')
        # action_locals = dict()
        # Kind of nasty, but currently only way to make external imports work
        execfile(file_path, globals(), globals())
        self.action = action

    def check_and_start_action(self):
        if self.action is not None:
            if self.action.state == ActionState.INITIALIZED:
                self.action.start()

    def reset(self):
        if self.action:
            self.action.stop()
        del self.action
        self.action = None
        if self.client.gh:
            self.client.stop_tracking_goal()

    def preempt(self):
        try:
            if self.client.gh:
                if self.client.get_state() == GoalStatus.ACTIVE or self.client.get_state() == GoalStatus.PENDING:
                    self.client.cancel_all_goals()
                    rospy.logwarn('Canceling action.')
        except NameError:
            rospy.logerr(traceback.print_exc())


if __name__ == '__main__':
    try:
        rospy.init_node('free_gait_action_loader')
        action_loader = ActionLoader()
        rospy.on_shutdown(action_loader.preempt)

        # Decide what to do.
        load_file = False
        if rospy.has_param('~file'):
            file = rospy.get_param('~file')
            if file != "":
                load_file = True
            rospy.delete_param('~file')

        if load_file:
            request = locomotion_controller_msgs.srv.SwitchControllerRequest(file)
            thread = threading.Thread(target=action_loader.send_action, args=(request, True))
            thread.start()
        else:
            rospy.Service('~send_action', locomotion_controller_msgs.srv.SwitchController, action_loader.send_action)
            rospy.Service('~list_actions', locomotion_controller_msgs.srv.GetAvailableControllers, action_loader.list_actions)
            rospy.loginfo("Ready to load actions from service call.")

        updateRate = rospy.Rate(10)
        while not rospy.is_shutdown():
            # This is required for having the actions run in the main thread
            # (instead through the thread by the service callback).
            action_loader.check_and_start_action()
            updateRate.sleep()

    except rospy.ROSInterruptException:
        pass
