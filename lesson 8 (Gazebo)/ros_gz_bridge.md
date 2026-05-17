# Мост Gazebo ↔ ROS 2: ros_gz_bridge

**Цель:** перенести топики из шины Gazebo Transport в DDS, чтобы ROS 2 ноды (`teleop_twist_keyboard`, RViz, Nav2) могли с ними работать.

## Зачем нужен bridge

Gazebo и ROS 2 - **разные шины сообщений** с разными форматами:

| | Gazebo Harmonic | ROS 2 |
|---|---|---|
| Шина | gz-transport (zmq) | DDS |
| Тип сообщения | `gz.msgs.Twist` (protobuf) | `geometry_msgs/msg/Twist` |

`ros_gz_bridge::parameter_bridge` - утилита, которая по конфигу подписывается на одной стороне и публикует на другой, конвертируя типы.

## Два способа задать маппинг

### 1) CLI-аргументы

Быстро для одного-двух топиков:

```bash
ros2 run ros_gz_bridge parameter_bridge \
  /cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist \
  /odom@nav_msgs/msg/Odometry[gz.msgs.Odometry \
  /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock
```

Стрелки: `@` - двунаправленно, `[` - GZ→ROS, `]` - ROS→GZ.

### 2) YAML конфиг (рекомендуется)

Для робота с лидаром, IMU, одометрией и `cmd_vel` маппингов уже много. Удобнее держать их в файле. См. [config/bridge.yaml](<../ros2_ws/src/my_robot_gazebo/config/bridge.yaml>):

```yaml
- ros_topic_name: "/cmd_vel"
  gz_topic_name: "/cmd_vel"
  ros_type_name: "geometry_msgs/msg/Twist"
  gz_type_name: "gz.msgs.Twist"
  direction: ROS_TO_GZ

- ros_topic_name: "/odom"
  gz_topic_name: "/odom"
  ros_type_name: "nav_msgs/msg/Odometry"
  gz_type_name: "gz.msgs.Odometry"
  direction: GZ_TO_ROS

- ros_topic_name: "/tf"
  gz_topic_name: "/tf"
  ros_type_name: "tf2_msgs/msg/TFMessage"
  gz_type_name: "gz.msgs.Pose_V"
  direction: GZ_TO_ROS
```

Запуск:

```bash
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:=$(ros2 pkg prefix my_robot_gazebo)/share/my_robot_gazebo/config/bridge.yaml \
             -p use_sim_time:=true
```

> `use_sim_time:=true` обязательно, если хотим, чтобы все ROS 2 подписчики использовали время симуляции из `/clock`.

## Проверка мост работает

В одном терминале с роботом и мостом, в другом - стандартные ROS 2 инструменты:

```bash
source /opt/ros/jazzy/setup.bash

ros2 topic list | sort
ros2 topic hz /odom
ros2 topic echo /scan --once
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.15}, angular: {z: 0.0}}"
```

Если в логе `parameter_bridge` появляются строки вида `Created bidirectional bridge for topic ...` - всё ок.

## Частые ошибки

- **Топика `/cmd_vel` нет в `gz topic -l`**. DiffDrive плагин не загрузился - проверьте имена суставов в URDF.
- **`/odom` есть в ROS 2, но `frame_id` = "" в `ros2 topic echo /odom`**. В Xacro в diff_drive не указали `frame_id`/`child_frame_id`.
- **`/tf` пустой в RViz**. У `gz.msgs.Pose_V` имена фреймов хранятся в `header.data`. Без явного `<tf_topic>tf</tf_topic>` плагин публикует в `/model/<name>/tf`, и маппинг не сработает.

## Альтернатива: image_bridge

Картинки эффективнее гонять через `ros_gz_image image_bridge`:

```bash
ros2 run ros_gz_image image_bridge /camera/image_raw
```

Он ходит без YAML, читает топик с двух сторон и поддерживает compressed transport. Нам не нужен в этом уроке (камеры нет), но запомните на будущее.

## Контрольные проверки

- [x] `ros2 topic list` показывает `/cmd_vel`, `/odom`, `/scan`, `/imu`, `/joint_states`, `/tf`, `/clock`.
- [x] `ros2 topic echo /odom` обновляется ~30 Гц.
- [x] `ros2 topic pub /cmd_vel ...` двигает робота в Gazebo.

## Дальше

[Сенсоры: лидар и IMU](sensors_lidar_imu.md).
