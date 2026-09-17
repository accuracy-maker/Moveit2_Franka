# panda moveit config

Most of files are copied from [moveit resources](https://github.com/moveit/moveit_resources)

## CMakeLists
add packages
```txt
# MoveIt planning and execution interfaces
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_ros_move_group REQUIRED)  

# Kinematics and motion-planning algorithms
find_package(moveit_kinematics REQUIRED) 
find_package(moveit_planners_ompl REQUIRED) 

# MoveIt RViz visualization and visualization utilities
find_package(moveit_ros_visualization REQUIRED) 
find_package(rviz2 REQUIRED)  
find_package(rviz_visual_tools REQUIRED) 

# install
install (
  DIRECTORY config launch 
  DESTINATION share/${PROJECT_NAME}
)
```
For `package.xml` file, we also need to add
```XML
<depend>moveit_ros_planning_interface</depend>
<depend>moveit_ros_move_group</depend>
<depend>moveit_kinematics</depend>
<depend>moveit_planners_ompl</depend>
<depend>moveit_ros_visualization</depend>
<depend>rviz2</depend>
<depend>rviz_visual_tools</depend>

<exec_depend>moveit_simple_controller_manager</exec_depend>
<exec_depend>moveit_configs_utils</exec_depend>
<exec_depend>pilz_industrial_motion_planner</exec_depend>
```
For the tag, it's usually:

- For dependencies only used in testing the code (e.g. gtest), use test_depend.

- For dependencies only used in building the code, use build_depend.

- For dependencies needed by headers the code exports, use build_export_depend.

- For dependencies only used when running the code, use exec_depend.

- For mixed purposes, use depend, which covers build, export, and execution time dependencies.


## create new folders
in convention, we need folders structure like
```txt
.
├── config <- necessary
├── include
│   └── panda_moveit_config
├── launch <- necessary
├── rviz <- necessary
└── src
```

## build the package
```bash
cd ~/ros2_ws
colcon build --packages-select panda_moveit_config --symlink-install
```

## Implement config folder

### xacro files
The first part we need to implement is the **xacro** family files, which defines the robot physical structure, semantic information during motion planning and control information.

Main files include:

#### Robot model files
---

```bash
panda.urdf.xacro
```

This is usually:
  - include panda model from `panda_description`
  - include the arm `ros2_control` definition
  - include the hand `ros_2` control definition
  - adds the complete robot model used by Moveit and controller

```XML
<robot name="panda" xmlns:xacro="...">

  <xacro:include
    filename="$(find-pkg-share panda_description)/urdf/panda.urdf.xacro"/>

  <xacro:include filename="panda.ros2_control.xacro"/>
  <xacro:include filename="panda_hand.ros2_control.xacro"/>

  ...
</robot>
```

#### ROS2 Control files
---
```bash
panda.ros2_control.xacro
panda_hand.ros2_control.xacro
```
these define how the arm and hand are controlled.

arm is for joint 1 to joint 7; hand for finger 1 and 2.

They define
- hardware plugin
- command interfaces
- state interfaces
- joint exposed to controllers
- fake, simulated or real hardware type

#### Moveit semantic description files
---
```bash
panda_arm.srdf.xacro
panda_arm_hand.srdf.xacro
```
These define how Moveit should use the robot

The SRDF Xacro files specify:
- planning groups
- arm joints
- hand joints
- end effectors
- virtual joints
- disabled collision pairs
- named robot poses

`panda_arm.srdf.xacro` typically creates an arm-only planning group; `panda_arm_hand.srdf.xacro` creates an arm-hand configuration

#### Xacro composition files
---
```bash
panda_arm.xacro
hand.xacro
```
they are reusable modules.

#### overall file structure
---
Overall, we have 7 xacro files:
```bash
.
├── hand.xacro
├── panda_arm_hand.srdf.xacro
├── panda_arm.srdf.xacro
├── panda_arm.xacro
├── panda_hand.ros2_control.xacro
├── panda.ros2_control.xacro
└── panda.urdf.xacro
``` 
### YAML files

#### initial_positions
---
```bash
initial_positions.yaml
```
it defines the initial pose of panda arm (joint1 to joint7)

#### limits
---
Limits are one of common constraints within motion planning.
- joint_limits.yaml: used in motion planning
- hard_joint_limits.yaml: used in real URDF
- pilz_cartesian_limits.yaml: used in motion planning for cartesian space planning

#### Kinmematics
---
Kinematics in motion planning mainly indicate inverse kinematics, i.e. given a fixed target pose, compute the joint configuraitons to reach that pose
There are many kinematics libraies can be plugged into Moveit framework by creating a YAML file.
- KDL (Kinematics and Dynamics Library): pseduoinverse Jacobian: \delta_q = J_inv * \delta_err [`kinematics.yaml`]
- Track_IK (Tolerant IK for Real-time Arm Control): two threads: one is running KDL, another is running SQP, and pick better one [`trac_ik_kinematics.yaml`]
- bio_ik: based on a memetic algorithm that combines gradient-based optimization with genetic and particle swarm optimization.[`bio_ik_kinematics.yaml`]
- 

folder structure is increased to 
```bash
.
├── bio_ik_kinematics.yaml
├── hand.xacro
├── hard_joint_limits.yaml
├── initial_positions.yaml
├── joint_limits.yaml
├── kinematics.yaml
├── panda_arm_hand.srdf.xacro
├── panda_arm.srdf.xacro
├── panda_arm.xacro
├── panda_hand.ros2_control.xacro
├── panda.ros2_control.xacro
├── panda.urdf.xacro
├── pilz_cartesian_limits.yaml
└── trac_ik_kinematics.yaml
```

#### controllers
---
controller yaml uses the interface telling MoveIt how to send a planned trajectory to robot’s controllers. Then `ros2_controller` will communicate with robots and exectute the planning.
- moveit_controllers.yaml: used by Moveit
- ros2_controller.yaml: used by ROS2
- gripper_moveit_controllers.yaml

#### Planning libraries
After define all beforementioned configurations, we can start to create the core part of Moveit, i.e. motion planning part.

There are several widely used libraries:
- OMPL: Open Motion Planning Library. It provides comprehensive **sampling-based** motion planning algorithms [`ompl_planning.yaml`]
- STOMP: Stochastic Trajectory Optimization for Motion Planning is a probabilistic optimization framework [`stomp_planning.yaml`]
- CHOMP: Covariant Hamiltonian Optimization for Motion Planning (CHOMP) is a gradient-based trajectory optimization procedure that makes many everyday motion planning problems both simple and trainable [`chomp_planning.yaml`]

right now, the folder structure is like
```bash
.
├── bio_ik_kinematics.yaml
├── chomp_planning.yaml
├── hand.xacro
├── hard_joint_limits.yaml
├── initial_positions.yaml
├── joint_limits.yaml
├── kinematics.yaml
├── moveit_controllers.yaml
├── ompl_planning.yaml
├── panda_arm_hand.srdf.xacro
├── panda_arm.srdf.xacro
├── panda_arm.xacro
├── panda_hand.ros2_control.xacro
├── panda.ros2_control.xacro
├── panda.urdf.xacro
├── pilz_cartesian_limits.yaml
├── pilz_industrial_motion_planner_planning.yaml
├── ros2_controllers.yaml
├── stomp_planning.yaml
└── trac_ik_kinematics.yaml
```
As we maintain it maunally, we don't include `.setup_assitant` here

## Launch file






