# Первый мир и gz CLI

Цель: разобраться, как Gazebo Harmonic организует мир (`world.sdf`), какие системы (`plugin`) нужны минимум, и как взаимодействовать с симуляцией через `gz topic`, `gz model`, `gz service`.

## Что такое SDF

**SDF** (Simulation Description Format) — XML-формат, описывающий сцену симуляции: миры, модели, физику, свет, плагины. URDF робота можно представить как подмножество SDF, но мир описывается только в SDF.

Минимальный жизнеспособный мир требует четырёх системных плагинов:

| Плагин | За что отвечает |
|---|---|
| `gz-sim-physics-system` | Физика (DART по умолчанию) |
| `gz-sim-user-commands-system` | Принимает команды от GUI (spawn, удалить, переместить) |
| `gz-sim-scene-broadcaster-system` | Рассылает обновления сцены подключённым клиентам |
| `gz-sim-sensors-system` | Рендеринг камер/лидаров (нужен, если есть сенсоры) |

Если позже будем использовать IMU — подключаем дополнительно `gz-sim-imu-system`. Для diff-drive — `gz-sim-diff-drive-system` уже описан внутри модели робота.

структура SDF
<sdf>
  <world name="...">        ← имя мира (важно для gz model -l --world ИМЯ)

    <scene>                 ← визуальное оформление (небо, сетка)
    <physics>               ← параметры физического движка
    <plugin>                ← системные плагины (физика, сенсоры, GUI)
    <light>                 ← освещение
    <model name="ground_plane">  ← статические объекты мира
    <model name="box_1">         ← препятствия

  </world>
</sdf>

## Свой минимальный мир

```bash
# Создайте рабочее пространство (если нет)
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Создайте пакет my_robot_gazebo
ros2 pkg create --build-type ament_cmake my_robot_gazebo

cd ~/ros2_ws/src/my_robot_gazebo
mkdir -p worlds

# Создайте и отредактируйте файл
nano worlds/empty.sdf
```

Файл `worlds/empty.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.10">
  <world name="empty">
    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <plugin filename="gz-sim-physics-system"           name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system"     name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system"           name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-imu-system"               name="gz::sim::systems::Imu"/>

    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.5 -1</direction>
    </light>

    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane><normal>0 0 1</normal><size>100 100</size></plane>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <plane><normal>0 0 1</normal><size>100 100</size></plane>
          </geometry>
          <material>
            <ambient>0.8 0.8 0.8 1</ambient>
            <diffuse>0.8 0.8 0.8 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
  </world>
</sdf>
```

## Мир с голубым облачным фоном

Для разнообразия — мир с небом и облаками:

```bash
nano worlds/blue.sdf
```

```xml
<?xml version="1.0"?>
<sdf version="1.10">
  <world name="empty">
    <scene>
      <sky>
        <time>12</time>
        <cloud_speed>0.5</cloud_speed>
        <cloud_ambient>0.2 0.2 0.3</cloud_ambient>
      </sky>
      <grid>true</grid>
    </scene>

    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>

    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.5 -1</direction>
    </light>

    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane><normal>0 0 1</normal><size>100 100</size></plane>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <plane><normal>0 0 1</normal><size>100 100</size></plane>
          </geometry>
          <material>
            <ambient>0.8 0.8 0.8 1</ambient>
            <diffuse>0.8 0.8 0.8 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
  </world>
</sdf>
```

## Мир с препятствиями — obstacles.sdf

Понадобится для тестирования навигации:

```bash
nano worlds/obstacles.sdf
```

```xml
<?xml version="1.0"?>
<sdf version="1.10">
  <world name="obstacles">
    <scene>
      <ambient>0.4 0.4 0.4 1</ambient>
      <background>0.7 0.7 0.7 1</background>
    </scene>

    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>

    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <direction>-0.5 0.5 -1</direction>
    </light>

    <!-- Пол -->
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><plane><normal>0 0 1</normal><size>20 20</size></plane></geometry>
        </collision>
        <visual name="visual">
          <geometry><plane><normal>0 0 1</normal><size>20 20</size></plane></geometry>
          <material>
            <ambient>0.8 0.8 0.8 1</ambient>
            <diffuse>0.8 0.8 0.8 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- Зелёная коробка -->
    <model name="box_1">
      <static>true</static>
      <pose>2.0 1.0 0.5 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>1 1 1</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>1 1 1</size></box></geometry>
          <material>
            <ambient>0.2 0.6 0.2 1</ambient>
            <diffuse>0.2 0.6 0.2 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- Красная коробка -->
    <model name="box_2">
      <static>true</static>
      <pose>-1.5 -2.0 0.5 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>1 1 1</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>1 1 1</size></box></geometry>
          <material>
            <ambient>0.6 0.2 0.2 1</ambient>
            <diffuse>0.6 0.2 0.2 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- Стена -->
    <model name="wall_north">
      <static>true</static>
      <pose>0 4 0.5 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>8 0.2 1</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>8 0.2 1</size></box></geometry>
          <material>
            <ambient>0.5 0.5 0.7 1</ambient>
            <diffuse>0.5 0.5 0.7 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
  </world>
</sdf>
```

## Установка миров через CMakeLists.txt

```bash
nano CMakeLists.txt
```

Добавьте в конец файла (до `ament_package()`):

```cmake
install(DIRECTORY worlds
  DESTINATION share/${PROJECT_NAME}
)
```

Соберите пакет:

```bash
cd ~/ros2_ws
colcon build --packages-select my_robot_gazebo
source install/setup.bash
```

## Запуск напрямую через gz sim

Без launch файла:

```bash
gz sim -r -v 3 \
  $(ros2 pkg prefix my_robot_gazebo)/share/my_robot_gazebo/worlds/empty.sdf
```

* `-r` — сразу запустить симуляцию (не на паузе).
* `-v 3` — умеренный лог.

Замените `empty.sdf` на `blue.sdf` или `obstacles.sdf` чтобы запустить другой мир.

## Запуск через launch файл

В пакете создайте `launch/gazebo.launch.py`:

```python
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='empty',
        description='Имя файла мира без расширения .sdf'
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch', 'gz_sim.launch.py'
            ])
        ]),
        launch_arguments=[
            ('gz_args', [
                '-r -v 3 ',
                PathJoinSubstitution([
                    FindPackageShare('my_robot_gazebo'),
                    'worlds',
                    [LaunchConfiguration('world'), '.sdf']
                ])
            ])
        ]
    )

    return LaunchDescription([world_arg, gz_sim])
```

Не забудьте установить директорию `launch` в `CMakeLists.txt`:

```cmake
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)
```

После пересборки:

```bash
ros2 launch my_robot_gazebo gazebo.launch.py
ros2 launch my_robot_gazebo gazebo.launch.py world:=blue
ros2 launch my_robot_gazebo gazebo.launch.py world:=obstacles
```

## gz CLI: что можно делать прямо сейчас

`gz` — это полноценный шинный инструмент, аналог `ros2` cli. Основные группы команд:

| Команда | Назначение |
|---------|------------|
| `gz topic -l` | Список топиков транспорта Gazebo |
| `gz topic -i -t /clock` | Информация о топике |
| `gz topic -e -t /clock -n 5` | Прочитать 5 сообщений |
| `gz topic -t /cmd_vel -p ...` | Опубликовать сообщение |
| `gz service -l` | Список сервисов |
| `gz service -s ... --reqtype ... --reptype ... --timeout 1000 --req ...` | Вызвать сервис |
| `gz model -l --world empty` | Список моделей в мире |
| `gz model -m my_robot --pose` | Поза модели |

## Практика: подвинуть модель сервисом

Запустите `obstacles.sdf` и в другом терминале сдвиньте зелёную коробку:

```bash
gz service -s /world/obstacles/set_pose \
  --reqtype gz.msgs.Pose \
  --reptype gz.msgs.Boolean \
  --timeout 1000 \
  --req 'name: "box_1", position: {x: 0.0, y: 0.0, z: 0.5}'
```

Зелёная коробка прыгнет в центр сцены.

## Связь с ROS 2

На этом шаге ROS 2 ещё ничего не знает о Gazebo. Топики `/clock`, `/world/...` живут только в шине **Gazebo Transport**. Чтобы перенести их в DDS, нужен `parameter_bridge` — этим займёмся в статье 5.

## Контрольные проверки

* `ros2 launch my_robot_gazebo gazebo.launch.py` открывает окно симулятора с серой плоскостью.
* `ros2 launch my_robot_gazebo gazebo.launch.py world:=obstacles` показывает мир с коробками и стеной.
* `gz topic -l` показывает не менее 5 топиков.
* `gz model -l --world empty` возвращает хотя бы `ground_plane`.
* `gz model -l --world obstacles` возвращает `ground_plane`, `box_1`, `box_2`, `wall_north`.

## Дальше

[URDF робота и Xacro макросы](./03-urdf-xacro.md) — собираем модель R2D2.
