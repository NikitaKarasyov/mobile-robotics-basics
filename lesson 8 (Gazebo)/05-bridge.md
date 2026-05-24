# Мост между Gazebo и ROS 2

Цель: подключить `ros_gz_bridge` — мост который переносит топики из шины Gazebo Transport в DDS (и обратно). После этого роботом можно управлять из ROS 2 нод, а сенсоры — обрабатывать привычными способами.

## Зачем нужен мост

Gazebo и ROS 2 — это две разные шины обмена сообщениями. Gazebo использует свой `gz-transport`, ROS 2 — DDS. Они независимы и сами по себе друг друга не видят.

`ros_gz_bridge` это нода-переходник. Она читает сообщения из одной шины и переотправляет в другую с конвертацией типов:

| Gazebo Transport | ROS 2 DDS |
|---|---|
| `gz.msgs.Twist` | `geometry_msgs/Twist` |
| `gz.msgs.Odometry` | `nav_msgs/Odometry` |
| `gz.msgs.IMU` | `sensor_msgs/Imu` |
| `gz.msgs.LaserScan` | `sensor_msgs/LaserScan` |
| `gz.msgs.Model` | `sensor_msgs/JointState` |
| `gz.msgs.Clock` | `rosgraph_msgs/Clock` |

## Два способа запустить мост

### Способ 1 — через CLI (для одного-двух топиков)

```bash
ros2 run ros_gz_bridge parameter_bridge \
  /cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist \
  /odom@nav_msgs/msg/Odometry@gz.msgs.Odometry
```

Формат: `имя_топика@ros_тип@gz_тип`. Между типами `@` — направление двустороннее, `[` — ROS → Gazebo, `]` — Gazebo → ROS.

### Способ 2 — через YAML (для многих топиков)

Когда топиков становится больше трёх, проще описать их в YAML и подключить как конфиг:

`config/ros_gz_bridge.yaml`:

```yaml
# Управление: ROS → Gazebo
- ros_topic_name: "cmd_vel"
  gz_topic_name: "cmd_vel"
  ros_type_name: "geometry_msgs/msg/Twist"
  gz_type_name: "gz.msgs.Twist"
  direction: ROS_TO_GZ

# Одометрия: Gazebo → ROS
- ros_topic_name: "odom"
  gz_topic_name: "odom"
  ros_type_name: "nav_msgs/msg/Odometry"
  gz_type_name: "gz.msgs.Odometry"
  direction: GZ_TO_ROS

# Состояния суставов: Gazebo → ROS
- ros_topic_name: "joint_states"
  gz_topic_name: "joint_states"
  ros_type_name: "sensor_msgs/msg/JointState"
  gz_type_name: "gz.msgs.Model"
  direction: GZ_TO_ROS

# Часы симуляции: Gazebo → ROS
- ros_topic_name: "clock"
  gz_topic_name: "clock"
  ros_type_name: "rosgraph_msgs/msg/Clock"
  gz_type_name: "gz.msgs.Clock"
  direction: GZ_TO_ROS
```

Подключение в launch:

```python
bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    parameters=[{
        'config_file': PathJoinSubstitution([
            FindPackageShare('my_robot_gazebo'),
            'config', 'ros_gz_bridge.yaml'
        ])
    }],
    output='screen'
)
```

И добавляем в `CMakeLists.txt`:

```cmake
install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)
```

## Направления передачи

Важно правильно выбрать `direction`:

* **`ROS_TO_GZ`** — команды управления. Внешние ноды публикуют в ROS, Gazebo получает.
* **`GZ_TO_ROS`** — данные сенсоров и состояние. Gazebo публикует, ROS-ноды читают.
* **`BIDIRECTIONAL`** — для случаев когда нужны оба направления (редко, и создаёт цикл — используйте осторожно).

## TF — особый случай

Дерево трансформаций `/tf` приходит из плагина diff-drive (см. предыдущую статью). В Gazebo оно типа `gz.msgs.Pose_V`, в ROS 2 — `tf2_msgs/TFMessage`. В YAML:

```yaml
- ros_topic_name: "tf"
  gz_topic_name: "tf"
  ros_type_name: "tf2_msgs/msg/TFMessage"
  gz_type_name: "gz.msgs.Pose_V"
  direction: GZ_TO_ROS
```

Без этого `RViz` не увидит позы робота.

## Полный launch с мостом

```python
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command, FindExecutable
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    world_arg = DeclareLaunchArgument('world', default_value='blue')

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'
            ])
        ]),
        launch_arguments=[
            ('gz_args', [
                '-r -v 3 ',
                PathJoinSubstitution([
                    FindPackageShare('my_robot_gazebo'), 'worlds',
                    [LaunchConfiguration('world'), '.sdf']
                ])
            ])
        ]
    )

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': ParameterValue(
                Command([
                    FindExecutable(name='xacro'), ' ',
                    PathJoinSubstitution([
                        FindPackageShare('my_robot_gazebo'),
                        'urdf', 'r2d2_gazebo.xacro'
                    ])
                ]),
                value_type=str
            ),
            'use_sim_time': True,
        }],
        output='screen'
    )

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'r2d2_robot',
            '-topic', 'robot_description',
            '-x', '0.0', '-y', '0.0', '-z', '0.4'
        ],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': PathJoinSubstitution([
                FindPackageShare('my_robot_gazebo'),
                'config', 'ros_gz_bridge.yaml'
            ]),
            'use_sim_time': True,
        }],
        output='screen'
    )

    return LaunchDescription([
        world_arg,
        gz_sim,
        rsp,
        TimerAction(period=2.0, actions=[bridge]),
        TimerAction(period=3.0, actions=[spawn]),
    ])
```

Порядок запуска:
1. Gazebo стартует
2. `robot_state_publisher` готов с URDF
3. Через 2 секунды — мост (он начинает слушать топики)
4. Через 3 секунды — спавн робота (топики уже мостятся)

## use_sim_time — обязательно

Все ROS 2 ноды которые работают с симуляцией должны использовать **время симуляции**, а не реальное:

```python
parameters=[{'use_sim_time': True}]
```

Без этого:
* TF будет «уезжать» во времени
* Лидар будет публиковать сканы со старым timestamp
* Nav2 потеряет данные

`use_sim_time` берёт время из топика `/clock` (его публикует Gazebo через мост).

## Проверка работы моста

После `ros2 launch spawn_robot.launch.py`:

```bash
ros2 topic list
```

Должны увидеть в ROS 2:
```
/cmd_vel
/odom
/joint_states
/tf
/clock
```

Проверим что одометрия идёт из Gazebo:

```bash
ros2 topic echo /odom --once
```

И что команда управления доходит обратно. В одном терминале:

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.0}}"
```

В другом — наблюдаем за позой:

```bash
ros2 topic echo /odom --field pose.pose.position
```

Поза должна меняться.

## RViz с мостом

Теперь можно показать робота в RViz, который читает только из ROS 2:

```bash
rviz2
```

В RViz:
* **Fixed Frame** — `odom`
* Добавить **RobotModel** — описание из топика `/robot_description`
* Добавить **TF** — увидите все фреймы
* Добавить **Odometry** — траекторию робота

При публикации `cmd_vel` робот двигается в Gazebo, и одновременно — модель в RViz.

## Контрольные проверки

* `ros2 topic list` показывает `/cmd_vel`, `/odom`, `/tf`, `/clock`, `/joint_states`.
* `ros2 topic hz /clock` показывает примерно 1000 Гц (зависит от `max_step_size` в SDF).
* `ros2 topic pub /cmd_vel ...` заставляет робота двигаться в Gazebo.
* В RViz при `Fixed Frame = odom` модель робота отображается и движется.

## Возможные проблемы

**`ros2 topic list` не показывает мостовые топики.** Мост не нашёл config файл. Проверьте путь к YAML и что директория `config/` установлена через CMakeLists.

**Топики появились, но `ros2 topic echo` пустой.** Направление в YAML неправильное. Проверьте `direction: GZ_TO_ROS` для сенсоров.

**TF дерево разорвано.** Не публикуется `joint_states` или нет моста для `/tf`. Без них `robot_state_publisher` не может построить TF для подвижных частей.

**`use_sim_time` warning.** Какая-то нода работает с реальным временем. Добавьте `'use_sim_time': True` в её параметры.

## Дальше

В следующей статье — добавляем сенсоры IMU и лидар. Они тоже работают через плагины и мостятся в ROS 2 как `/imu` и `/scan`.
