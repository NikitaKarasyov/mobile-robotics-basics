# my_robot_gazebo

Пакет учебного курса для урока 8 (Gazebo Harmonic + ROS 2 Jazzy).

Содержит:

- `urdf/my_robot.urdf.xacro` - diff-drive робот с лидаром и IMU, плагины Gazebo Harmonic в блоках `<gazebo>`;
- `worlds/empty.sdf` - минимальный мир с физикой и сенсорными системами;
- `worlds/obstacles.sdf` - комната 6×6 м со стенами, цилиндрами и коробками;
- `config/bridge.yaml` - конфигурация `ros_gz_bridge::parameter_bridge`;
- `launch/gazebo.launch.py` - запуск только симулятора с указанным миром;
- `launch/spawn_robot.launch.py` - полный сценарий: симулятор + `robot_state_publisher` + spawn + bridge + RViz;
- `rviz/my_robot.rviz` - готовый layout RViz2 со `scan`, `odom`, `RobotModel`, `TF`.

## Сборка

```bash
cd ~/projects/misis/mobile-robotics-basics/ros2_ws
rosdep install -i --from-path src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --packages-select my_robot_gazebo
source install/setup.bash
```

## Запуск

```bash
# Только симулятор:
ros2 launch my_robot_gazebo gazebo.launch.py world:=obstacles.sdf

# Полный сценарий с роботом, мостом и RViz:
ros2 launch my_robot_gazebo spawn_robot.launch.py

# Управление:
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r __ns:=/
```
