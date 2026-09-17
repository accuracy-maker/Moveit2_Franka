import os


from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.coditions import IfCondition
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder

def distro_specific_path(package_share: str, base_relpath: str) -> str:
    """return a distro-overridable share-relative path"""

    # read the current ROS distribution
    # ROS_DISTRO=jazzy
    distro = os.environ.get("ROS_DISTRO", "")

    # if ROS_DISTRO is set
    if distro:
        # config/joint_limits.yaml
        # stem = config/joint_limits
        # ext = .yaml
        stem, ext = os.path.splitext(base_relpath)

        # override: <package_share>/config/joint_limits.jazzy.yaml
        override = os.path.join(package_share, f"{stem}.{distro}{ext}")

        if os.path.isfile(override):
            return override
    return os.path.join(package_share, base_relpath)

def generate_launch_description():

    # command line arguments
    rviz_config_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value = "moveit.rviz",
        description="RViz configuration file",
    )

    db_arg = DeclareLaunchArgument(
        "db",
        default_value = "False",
        description = "Database flag",
    )

    # mock_components: This means the robot uses simulated/mock hardware.
    # It is useful for testing controllers and MoveIt without connecting to a real robot.
    # isaac: This means the robot uses an Isaac Sim hardware interface, allowing ROS 2 control to communicate with a robot simulated in NVIDIA Isaac Sim.
    ros2_control_hardware_type = DeclareLaunchArgument(
        "ros2_control_hardware_type",
        default_value = "mock_components",
        description = "ROS 2 control hardware interface type to use for the launch file -- possible values: [mock_components, isaac]"
    )

    moveit_config = (
        MoveItConfigsBuilder("panda_moveit_config")
        .robot_description(
            file_path = "config/panda.urdf.xacro",
            mappings = {
                "ros2_control_hardware_type": LaunchConfiguration(
                    "ros2_control_hardware_type"
                )
            },
        )
        .robot_description_semantic(file_path = "config/panda.srdf")
        .planning_scene_monitor(
            publish_robot_description=True, publish_robot_description_semantic=True
        )
        .trajectory_execution(file_path = "config/gripper_moveit_controllers.yaml")
        .planning_pipelines(
            pipelines=["ompl", "chomp", "pilz_industrial_motion_planner", "stomp"]
        )
        .to_moveit_configs()
    )

    # start the actual move_group node/action server
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict()],
        arguments=["--ros-args", "--log-level", "info"], 
    )

    # RViz
    rviz_base = LaunchConfiguration("rviz_config")
    rviz_config = PathJoinSubstitution(
        [FindPackageShare("moveit_resources_panda_moveit_config"), "launch", rviz_base]
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.planning_pipelines,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
        ],
    )

    # Static TF
    static_tf_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        output="log",
        arguments=["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "world", "panda_link0"],
    )

    # Publish TF
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[moveit_config.robot_description],
    )

    # distro-dependent controller
   ros2_controllers_path = distro_specific_path(
        get_package_share_directory("panda_moveit_config"),
        "config/ros2_controllers.yaml",
   )
   
   # create ROS2 nodes
   ros2_control_node = Node(
        package = "controller_manager",
        executable = "ros2_control_node",
        parameters = [ros2_controllers_path],
        remappings = [
            ("/controller_manager/robot_description", "/robot_description"),
        ],
        output = "screen",
    )

   joint_state_broadcaster_spawner = Node(
        package = "controller_manager",
        executable = "spawner",
        arguments = [
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
            "--param-file",
            ros2_controllers_path,
        ],
    )
    
    panda_arm_controller_spawner = Node(
        package = "controller_manager",
        executable = "spawner",
        arguments = [
            "panda_arm_controller",
            "-c",
            "/controller_manager",
            "--param-file",
            ros2_controllers_path,
        ],
    )

    panda_hand_controller_spawner = Node(
        package = "controller_manager",
        executable = "spawner",
        arguments = [
            "panda_hand_controller",
            "-c",
            "/ros2_controller_manager",
            "--param-file",
            ros2_controllers_path,
        ]
    )

    # warehouse mongodb server
    db_config = LaunchConfiguration("db")
    mongodb_server_node = Node(
        package = "warehouse_ros_mongo",
        executable = "mongo_wrapper_ros.py",
        parameters = [
            {"warehouse_port" : 33829},
            {"warehouse_host": "localhost"},
            {"warehouse_plugin": "warehouse_ros_mongo::MongoDatabaseConnection"},
        ],
        output = "screen",
        condition = IfCondition(db_config),
    )

    return LaunchDescription(
        [
            rviz_config_arg,
            db_arg,
            ros2_control_hardware_type,
            rviz_node,
            static_tf_node,
            robot_state_publisher,
            move_group_node,
            ros2_control_node,
            joint_state_broadcaster_spawner,
            panda_arm_controller_spawner,
            panda_hand_controller_spawner,
            mongodb_server_node,
        ]
    )







