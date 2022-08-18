import numpy as np
import time

from autolab_core import RigidTransform
from frankapy import FrankaArm, SensorDataMessageType
from frankapy import FrankaConstants as FC
from frankapy.proto_utils import sensor_proto2ros_msg, make_sensor_group_msg
from frankapy.proto import PosePositionSensorMessage, ShouldTerminateSensorMessage, CartesianImpedanceSensorMessage
from franka_interface_msgs.msg import SensorDataGroup

from frankapy.utils import min_jerk, min_jerk_weight

if __name__ == "__main__":
    fa = FrankaArm()
    fa.reset_joints()

    fa.log_info('Generating Trajectory')
    p0 = fa.get_pose()
    p1 = p0.copy()
    T_delta = RigidTransform(
        translation=np.array([0, 0, 0.2]),
        rotation=RigidTransform.z_axis_rotation(np.deg2rad(30)), 
                            from_frame=p1.from_frame, to_frame=p1.from_frame)
    p1 = p1 * T_delta
    fa.goto_pose(p1)

    T = 5
    dt = 0.02
    ts = np.arange(0, T, dt)
    current_gripper_width = 0.08
    has_closed = False

    weights = [min_jerk_weight(t, T) for t in ts]
    pose_traj = [p1.interpolate_with(p0, w) for w in weights]

    z_stiffness_traj = [min_jerk(100, 800, t, T) for t in ts]

    fa.log_info('Initializing Sensor Publisher')

    fa.log_info('Publishing pose trajectory...')
    # To ensure skill doesn't end before completing trajectory, make the buffer time much longer than needed
    fa.goto_pose(pose_traj[1], duration=T, dynamic=True, buffer_time=10,
        cartesian_impedances=FC.DEFAULT_TRANSLATIONAL_STIFFNESSES[:2] + [z_stiffness_traj[1]] + FC.DEFAULT_ROTATIONAL_STIFFNESSES
    )
    init_time = fa.get_time()

    for i in range(2, len(ts)):
        timestamp = fa.get_time() - init_time
        traj_gen_proto_msg = PosePositionSensorMessage(
            id=i, timestamp=timestamp, 
            position=pose_traj[i].translation, quaternion=pose_traj[i].quaternion
        )
        fb_ctrlr_proto = CartesianImpedanceSensorMessage(
            id=i, timestamp=timestamp,
            translational_stiffnesses=FC.DEFAULT_TRANSLATIONAL_STIFFNESSES[:2] + [z_stiffness_traj[i]],
            rotational_stiffnesses=FC.DEFAULT_ROTATIONAL_STIFFNESSES
        )
        ros_msg = make_sensor_group_msg(
            trajectory_generator_sensor_msg=sensor_proto2ros_msg(
                traj_gen_proto_msg, SensorDataMessageType.POSE_POSITION),
            feedback_controller_sensor_msg=sensor_proto2ros_msg(
                fb_ctrlr_proto, SensorDataMessageType.CARTESIAN_IMPEDANCE)
            )

        if not has_closed:
            current_gripper_width -= 0.0005
        else:
            current_gripper_width += 0.0005

        if current_gripper_width < 0.002:
            has_closed = True

        #fa.goto_gripper(current_gripper_width, block=False)
        
        fa.log_info('Publishing: ID {}'.format(traj_gen_proto_msg.id))
        fa.publish_sensor_data(ros_msg)
        time.sleep(dt)

    # Stop the skill
    # Alternatively can call fa.stop_skill()
    term_proto_msg = ShouldTerminateSensorMessage(timestamp=fa.get_time() - init_time, should_terminate=True)
    ros_msg = make_sensor_group_msg(
        termination_handler_sensor_msg=sensor_proto2ros_msg(
            term_proto_msg, SensorDataMessageType.SHOULD_TERMINATE)
        )
    fa.publish_sensor_data(ros_msg)

    fa.log_info('Done')
