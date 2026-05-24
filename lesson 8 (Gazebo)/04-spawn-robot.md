# Спавн робота в Gazebo

Цель: загрузить URDF из предыдущей статьи в Gazebo, добавить плагины симуляции (diff-drive, joint state publisher) и проверить что робот едет по команде из `gz topic`.

## Что нужно добавить к URDF

URDF описывает геометрию и инерцию — этого хватает для RViz и `robot_state_publisher`. Но Gazebo нужны **плагины симуляции**: контроллер моторов, источник одометрии, публикация состояний суставов.

Плагины Gazebo живут внутри тегов `<gazebo>` в URDF/SDF. Чтобы не смешивать «чистую» модель робота с симуляционными деталями, выносим плагины в отдельный xacro файл и подключаем через `<xacro:include>`.

## Структура

```
urdf/
├── r2d2.urdf.xacro            ← чистая модель (предыдущая статья)
├── r2d2_properties.xacro
├── r2d2_macros.xacro
└── r2d2_gazebo.xacro          ← модель + плагины Gazebo
```

## Плагины Gazebo — r2d2_gazebo.xacro

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="r2d2_gazebo">

  <!-- Подключаем чистую модель -->
  <xacro:include filename="$(find my_robot_gazebo)/urdf/r2d2.urdf.xacro"/>

  <!-- Diff-drive контроллер: принимает /cmd_vel, крутит колёса, публикует /odom -->
  <gazebo>
    <plugin filename="gz-sim-diff-drive-system"
            name="gz::sim::systems::DiffDrive">
      <left_joint>left_front_wheel_joint</left_joint>
      <right_joint>right_front_wheel_joint</right_joint>
      <wheel_separation>0.44</wheel_separation>
      <wheel_radius>0.035</wheel_radius>
      <odom_publish_frequency>30</odom_publish_frequency>
      <topic>cmd_vel</topic>
      <odom_topic>odom</odom_topic>
      <tf_topic>tf</tf_topic>
      <frame_id>odom</frame_id>
      <child_frame_id>base_footprint</child_frame_id>
    </plugin>
  </gazebo>

  <!-- Joint state publisher: публикует /joint_states для tf задних колёс -->
  <gazebo>
    <plugin filename="gz-sim-joint-state-publisher-system"
            name="gz::sim::systems::JointStatePublisher">
      <topic>joint_states</topic>
      <joint_name>left_front_wheel_joint</joint_name>
      <joint_name>right_front_wheel_joint</joint_name>
      <joint_name>left_back_wheel_joint</joint_name>
      <joint_name>right_back_wheel_joint</joint_name>
    </plugin>
  </gazebo>

</robot>
```

### Что делает каждый плагин

**`gz-sim-diff-drive-system`** — реализует кинематику differential drive. На вход — `geometry_msgs/Twist` (линейная и угловая скорость), на выходе — крутящие моменты на левом и правом колесе и одометрия в `nav_msgs/Odometry`.

Параметры:
* `wheel_separation` — расстояние между колёсами по Y. У нас ноги отстоят на 0.22 от центра, значит расстояние между левым и правым = 0.44.
* `wheel_radius` — радиус колеса для расчёта одометрии.
* `odom_publish_frequency` — частота публикации одометрии.
* `topic` — куда подписаться на команды.
* `odom_topic` — куда публиковать одометрию.

DiffDrive управляет только **одной парой колёс** (передние). Задние колёса в diff-drive не входят — они просто вращаются свободно как поддержка.

**`gz-sim-joint-state-publisher-system`** — публикует углы поворота суставов в `sensor_msgs/JointState`. Без него `robot_state_publisher` не сможет посчитать TF для подвижных частей.

## Один источник для робота: gazebo_additions.xacro

В рабочем проекте удобнее иметь один входной файл который Gazebo и `robot_state_publisher` грузят одинаково:

```python
# В launch файле
robot_description = ParameterValue(
    Command([
        FindExecutable(name='xacro'), ' ',
        PathJoinSubstitution([
            FindPackageShare('my_robot_gazebo'),
            'urdf', 'r2d2_gazebo.xacro'
        ])
    ]),
    value_type=str
)
```

`robot_state_publisher` теги `<gazebo>` игнорирует — для него это просто посторонний XML. Gazebo же наоборот берёт их в работу.

## Спавн через ros_gz_sim

Робот загружается в работающий Gazebo через ноду `create` из пакета `ros_gz_sim`. Она читает URDF из топика `/robot_description` (который публикует `robot_state_publisher`) и создаёт модель в указанной позе:

```python
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
```

`-z 0.4` — поднимаем робота немного над полом, чтобы он мягко опустился на колёса. Если поставить `-z 0.0`, колёса застрянут в полу.

## Полный launch файл

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
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='blue',
        description='Имя файла мира без расширения .sdf'
    )

    # Запуск Gazebo через готовый wrapper
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

    # Описание робота через robot_state_publisher
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
            )
        }],
        output='screen'
    )

    # Спавн робота
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

    return LaunchDescription([
        world_arg,
        gz_sim,
        rsp,
        # Спавн с задержкой — Gazebo должен успеть подняться
        TimerAction(period=2.0, actions=[spawn]),
    ])
```

`TimerAction` нужен потому что Gazebo стартует асинхронно. Спавн робота до того как мир готов — приводит к ошибке.

Сохраните файл как `launch/spawn_robot.launch.py` и добавьте в `CMakeLists.txt`:

```cmake
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)
```

## Запуск и проверка

```bash
cd ~/ros2_ws
colcon build --packages-select my_robot_gazebo
source install/setup.bash

ros2 launch my_robot_gazebo spawn_robot.launch.py
```

Окно Gazebo откроется, через две секунды появится R2D2 на голубом фоне.

## Управление через gz topic

Пока ROS 2 ничего не знает про команды управления — мост ещё не настроен. Но управлять роботом можно напрямую через шину Gazebo:

```bash
# Ехать вперёд со скоростью 0.3 м/с
gz topic -t /cmd_vel -m gz.msgs.Twist \
  -p 'linear: {x: 0.3}, angular: {z: 0.0}'

# Поворот на месте
gz topic -t /cmd_vel -m gz.msgs.Twist \
  -p 'linear: {x: 0.0}, angular: {z: 0.5}'

# Остановиться
gz topic -t /cmd_vel -m gz.msgs.Twist \
  -p 'linear: {x: 0.0}, angular: {z: 0.0}'
```

Робот поедет. Одометрия публикуется в `/odom` (тоже в шине Gazebo):

```bash
gz topic -e -t /odom -n 1
```

Видно как меняется поза робота со временем.

## Что произошло

Поток данных при движении робота:

```
gz topic -p /cmd_vel
        ↓
DiffDrive плагин (внутри Gazebo)
        ↓
крутящие моменты на колёсах
        ↓
физика Gazebo (DART)
        ↓
обновление поз
        ↓
одометрия → /odom
TF → /tf
JointStates → /joint_states
```

В ROS 2 этих топиков ещё нет — они живут только внутри Gazebo. Чтобы вытащить их в DDS, нужен `parameter_bridge` — это следующая статья.

## Контрольные проверки

* После `ros2 launch spawn_robot.launch.py` в Gazebo появляется R2D2 на четырёх колёсах.
* `gz model -l --world empty` (или `--world blue`) показывает `r2d2_robot` среди моделей.
* Команда `gz topic -t /cmd_vel ...` заставляет робота двигаться.
* `gz topic -l` показывает `/cmd_vel`, `/odom`, `/joint_states`, `/tf`.

## Возможные проблемы

**Робот падает после спавна и не может встать.** Колёса столкнулись с полом или друг с другом. Увеличьте `-z` при спавне или проверьте collision геометрию ног.

**Колёса крутятся но робот не едет.** Trение на колёсах нулевое из-за отсутствия collision у ground_plane. Проверьте что в SDF мира есть `<collision>` у плоскости.

**DiffDrive не реагирует на `/cmd_vel`.** Имя топика в плагине должно совпадать с тем что вы публикуете. Проверьте `gz topic -l` — там должен быть `/cmd_vel`.

## Дальше

В следующей статье — `parameter_bridge`: переносим топики из шины Gazebo в DDS чтобы управлять роботом из ROS 2 нод (включая `teleop_twist_keyboard`).
