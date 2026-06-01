"""Full launch: gz sim + robot_state_publisher + spawn robot + ros_gz_bridge + RViz."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

import xacro


def generate_launch_description():
    pkg_name = 'my_robot_gazebo'
    pkg_share = get_package_share_directory(pkg_name)
    ros_gz_sim = FindPackageShare('ros_gz_sim')

    xacro_file = os.path.join(pkg_share, 'urdf', 'my_robot.urdf.xacro')
    robot_description = xacro.process_file(xacro_file).toxml()

    bridge_config = os.path.join(pkg_share, 'config', 'bridge.yaml')
    rviz_config = os.path.join(pkg_share, 'rviz', 'my_robot.rviz')

    world = LaunchConfiguration('world')
    use_rviz = LaunchConfiguration('use_rviz')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    yaw = LaunchConfiguration('yaw')

    declared = [
        DeclareLaunchArgument('world',   default_value='obstacles.sdf'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('x',   default_value='0.0'),
        DeclareLaunchArgument('y',   default_value='0.0'),
        DeclareLaunchArgument('z',   default_value='0.1'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
    ]

    world_path = PathJoinSubstitution([FindPackageShare(pkg_name), 'worlds', world])

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([ros_gz_sim, 'launch', 'gz_sim.launch.py'])
        ),
        launch_arguments={'gz_args': ['-r ', world_path]}.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
    )

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-name', 'my_robot',
            '-topic', 'robot_description',
            '-x', x, '-y', y, '-z', z, '-Y', yaw,
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        parameters=[{
            'config_file': bridge_config,
            'use_sim_time': True,
        }],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription(declared + [gz_sim, robot_state_publisher, spawn, bridge, rviz])
