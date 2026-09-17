import os

from launch import LaunchDescription
from launch.substitutions import Command, FindExecutable
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    package_dir = get_package_share_directory('panda_description')

    urdf_file = os.path.join(
        package_dir, 'urdf', 'panda.urdf.xacro'
    )

    rviz_file = os.path.join(
        package_dir, 'rviz', 'panda.rviz'
    )

    robot_description = {
        'robot_description': Command([
            FindExecutable(name='xacro'),
            ' ',
            urdf_file
        ])
    }

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[robot_description],
        ),

        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_file],
            output='screen',
        ),
    ])
