# Урок 8. Gazebo Harmonic

Цель урока - научиться запускать симуляцию мобильного робота в **Gazebo Harmonic** в связке с **ROS 2 Jazzy**, перенести топики между шинами через `ros_gz_bridge` и собрать готовый стенд для перехода к Nav2.

К концу урока у вас будет:

- свой пакет [my_robot_gazebo](<../ros2_ws/src/my_robot_gazebo>) с diff-drive роботом, лидаром и IMU;
- кастомный мир с препятствиями (`obstacles.sdf`);
- одна команда `ros2 launch my_robot_gazebo spawn_robot.launch.py`, поднимающая всё разом;
- управление с клавиатуры через `teleop_twist_keyboard`;
- топики `/scan`, `/odom`, `/cmd_vel`, `/imu`, `/tf` в ROS 2 - готовые для Nav2.

## Что нужно знать заранее

| Из урока | Что используем |
|---|---|
| [Урок 4](<../lesson 4 (launches and parameters)/README.md>) | launch-файлы, передача аргументов |
| [Урок 5](<../lesson 5 (URDF and XACRO)/README.md>) | URDF, Xacro, инерции |
| [Урок 6](<../lesson 6 (RViz2 and rqt)/README.md>) | RViz2 displays |
| [Урок 7](<../lesson 7 (TF2)/README.md>) | tf2: фреймы `odom`, `base_footprint`, `base_link` |

## Порядок прохождения

| Шаг | Статья | Результат |
|---:|---|---|
| 1 | [Установка Gazebo Harmonic](installing_gazebo.md) | `gz sim empty.sdf` открывает GUI, `parameter_bridge` пробрасывает `/clock` |
| 2 | [Первый мир и gz CLI](first_world.md) | Свой `empty.sdf` запускается, освоены `gz topic`/`gz model`/`gz service` |
| 3 | [Spawn URDF робота](spawning_urdf.md) | Diff-drive Xacro с плагинами spawn'ится в Gazebo и едет по `gz topic -p /cmd_vel` |
| 4 | [Мост Gazebo ↔ ROS 2](ros_gz_bridge.md) | `parameter_bridge` с YAML конфигом переносит топики в DDS |
| 5 | [Сенсоры: лидар и IMU](sensors_lidar_imu.md) | `/scan` 10 Гц, `/imu` 100 Гц, точки видны в RViz |
| 6 | [Свой мир и teleop](custom_world_teleop.md) | `obstacles.sdf` + teleop клавиатурой, готов стенд для Nav2 |

## Пакет в workspace

- [my_robot_gazebo](<../ros2_ws/src/my_robot_gazebo>) - целиком: Xacro модель, два SDF мира, два launch, YAML bridge, RViz layout.

Сборка:

```bash
cd ~/projects/misis/mobile-robotics-basics/ros2_ws
rosdep install -i --from-path src --rosdistro $ROS_DISTRO -y
colcon build --symlink-install --packages-select my_robot_gazebo
source install/setup.bash
```

## Команды одной шпаргалкой

```bash
# Только симулятор
ros2 launch my_robot_gazebo gazebo.launch.py world:=empty.sdf

# Полный сценарий (Gazebo + робот + bridge + RViz)
ros2 launch my_robot_gazebo spawn_robot.launch.py

# Teleop в другом терминале
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Запись bag для последующего воспроизведения
ros2 bag record -o teleop_run /cmd_vel /odom /scan /imu /tf /tf_static
```

## Соглашения урока

- Все блоки SDF/URDF приводятся в статьях с прямой ссылкой на цельный файл в workspace.
- Имена плагинов и типов сообщений - именно для **Harmonic** (`gz-sim-*-system`, `gz.msgs.*`). Для Gazebo Classic / `gazebo_ros_pkgs` они другие и здесь не используются.
- Все ROS 2 ноды запускаются с `use_sim_time:=true`, иначе `tf` и `LaserScan` "уплывут" во времени.

## После урока

- [Урок 9 - Nav2](<../lesson 9 (NAV2)/README.md>): тот же робот, но с глобальным/локальным планировщиком и SLAM.
- [Урок 10 - TurtleBot3](<../lesson 10 (turtlebot3 sim)/README.md>): готовый промышленный аналог, можно сравнить структуру `*.sdf` и плагины.
