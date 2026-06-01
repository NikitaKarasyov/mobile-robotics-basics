"""Launch only the Gazebo Harmonic simulator with a chosen world."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('my_robot_gazebo')
    ros_gz_sim = FindPackageShare('ros_gz_sim')

    world = LaunchConfiguration('world')

    declare_world = DeclareLaunchArgument(
        'world', default_value='empty.sdf',
        description='World file name in my_robot_gazebo/worlds.',
    )

    world_path = PathJoinSubstitution([pkg_share, 'worlds', world])

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([ros_gz_sim, 'launch', 'gz_sim.launch.py'])
        ),
        launch_arguments={'gz_args': ['-r ', world_path]}.items(),
    )

    return LaunchDescription([declare_world, gz_sim])
