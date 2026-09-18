#include <rclcpp/rclcpp.hpp>

#include <geometry_msgs/msg/pose.hpp>
#include <moveit/move_group_interface/move_group_interface.hpp>
#include <moveit/planning_scene_interface/planning_scene_interface.hpp>
#include <moveit_msgs/msg/collision_object.hpp>
#include <shape_msgs/msg/solid_primitive.hpp>

int main(int argc, char* argv[])
{
  rclcpp::init(argc, argv);

  auto const node = std::make_shared<rclcpp::Node>(
    "play_around_box",
    rclcpp::NodeOptions()
      .automatically_declare_parameters_from_overrides(true)
  );

  // create a ROS logger
  auto const logger = rclcpp::get_logger("play_around_box");

  // planning

  moveit::planning_interface::MoveGroupInterface move_group(
      node, "panda_arm");

  moveit::planning_interface::PlanningSceneInterface planning_scene;

  // Create a box obstacle
  moveit_msgs::msg::CollisionObject box;
  box.header.frame_id = move_group.getPlanningFrame();
  box.id = "box";

  shape_msgs::msg::SolidPrimitive primitive;
  primitive.type = primitive.BOX;
  primitive.dimensions = {0.4, 0.4, 0.4};

  geometry_msgs::msg::Pose box_pose;
  box_pose.orientation.w = 1.0;
  box_pose.position.x = 0.45;
  box_pose.position.y = 0.0;
  box_pose.position.z = 0.2;

  box.primitives.push_back(primitive);
  box.primitive_poses.push_back(box_pose);
  box.operation = box.ADD;

  planning_scene.applyCollisionObject(box);

  RCLCPP_INFO(node->get_logger(), "Box added to planning scene");

  // Set a target pose
  geometry_msgs::msg::Pose target_pose;
  target_pose.orientation.w = 1.0;
  target_pose.position.x = 0.3;
  target_pose.position.y = 0.3;
  target_pose.position.z = 0.5;

  move_group.setPoseTarget(target_pose);

  moveit::planning_interface::MoveGroupInterface::Plan plan;

  bool success =
      static_cast<bool>(move_group.plan(plan));

  if (success)
  {
    RCLCPP_INFO(node->get_logger(), "Planning succeeded");
    move_group.execute(plan);
  }
  else
  {
    RCLCPP_ERROR(node->get_logger(), "Planning failed");
  }

  rclcpp::shutdown();
  return 0;
}
