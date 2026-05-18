# Первый мир и gz CLI

**Цель:** разобраться, как Gazebo Harmonic организует мир (`world.sdf`), какие системы (`plugin`) нужны минимум, и как взаимодействовать с симуляцией через `gz topic`, `gz model`, `gz service`.

## Что такое SDF

**SDF** (Simulation Description Format) - XML-формат, описывающий сцену симуляции: миры, модели, физику, свет, плагины. URDF робота можно представить как подмножество SDF, но мир описывается только в SDF.

Минимальный жизнеспособный мир требует **четырёх системных плагинов**:

| Плагин | За что отвечает |
|---|---|
| `gz-sim-physics-system` | Физика (DART по умолчанию) |
| `gz-sim-user-commands-system` | Принимает команды от GUI (spawn, удалить, переместить) |
| `gz-sim-scene-broadcaster-system` | Рассылает обновления сцены подключённым клиентам |
| `gz-sim-sensors-system` | Рендеринг камер/лидаров (нужен, если есть сенсоры) |

Если позже будем использовать IMU - подключаем дополнительно `gz-sim-imu-system`, для diff-drive - `gz-sim-diff-drive-system` уже описан внутри модели робота.

## Свой минимальный мир

```
# Создайте рабочее пространство (если нет)
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Создайте пакет my_robot_gazebo
ros2 pkg create --build-type ament_cmake my_robot_gazebo

cd ~/ros2_ws/src/my_robot_gazebo
mkdir -p worlds

# Создайте и отредактируйте файл
nano ~/ros2_ws/src/my_robot_gazebo/worlds/empty.sdf
```
Файл [worlds/empty.sdf](<../ros2_ws/src/my_robot_gazebo/worlds/empty.sdf>):

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

    <light type="directional" name="sun">...</light>
    <model name="ground_plane">...</model>
  </world>
</sdf>
```
#### Давайте для примера возьмем файл с голубым облачным фоном:
```
# Создайте и отредактируйте файл
nano ~/ros2_ws/src/my_robot_gazebo/worlds/blue.sdf
```
blue.sdf:
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
            <plane>
              <normal>0 0 1</normal>
              <size>100 100</size>
            </plane>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>100 100</size>
            </plane>
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
```
# oбновите CMakeLists.txt
nano ~/ros2_ws/src/my_robot_gazebo/CMakeLists.txt

#Добавьте в конец файла (до ament_package()):

install(DIRECTORY worlds
  DESTINATION share/${PROJECT_NAME}
)

# соберите пакет
cd ~/ros2_ws
colcon build --packages-select my_robot_gazebo
source install/setup.bash
```
Запускаем напрямую (без launch) ***(флаг LIBGL_ALWAYS_SOFTWARE=1 при необходимости)***:

```bash
gz sim -r -v 3 $(ros2 pkg prefix my_robot_gazebo)/share/my_robot_gazebo/worlds/empty.sdf
# или
gz sim -r -v 3 $(ros2 pkg prefix my_robot_gazebo)/share/my_robot_gazebo/worlds/blue.sdf
```

Флаг `-r` - сразу запустить симуляцию (не на паузе). `-v 3` - умеренный лог.

## То же через launch-файл

В пакете уже есть готовый wrapper [launch/gazebo.launch.py](<../ros2_ws/src/my_robot_gazebo/launch/gazebo.launch.py>):

```bash
source ~/projects/misis/mobile-robotics-basics/ros2_ws/install/setup.bash
ros2 launch my_robot_gazebo gazebo.launch.py
ros2 launch my_robot_gazebo gazebo.launch.py world:=obstacles.sdf
```

`gazebo.launch.py` использует `gz_sim.launch.py` из `ros_gz_sim` и пробрасывает аргумент `world`.

## gz CLI: что можно делать прямо сейчас

`gz` - это полноценный шинный инструмент, аналог `ros2 cli`. Основные группы команд:

| Команда | Назначение |
|---|---|
| `gz topic -l` | Список топиков транспорта Gazebo |
| `gz topic -i -t /clock` | Информация о топике |
| `gz topic -e -t /clock -n 5` | Прочитать 5 сообщений |
| `gz topic -t /world/empty/clock -p` | Опубликовать сообщение |
| `gz service -l` | Список сервисов |
| `gz service -s ... --reqtype ... --reptype ... --timeout 1000 --req ...` | Вызвать сервис |
| `gz model -l --world empty` | Список моделей в мире |
| `gz model -m my_robot --pose` | Поза модели |

### Практика: подвинуть модель сервисом

Запустите `obstacles.sdf` ([worlds/obstacles.sdf](<../ros2_ws/src/my_robot_gazebo/worlds/obstacles.sdf>)) в другом терминале:

```bash
gz service -s /world/obstacles/set_pose \
  --reqtype gz.msgs.Pose \
  --reptype gz.msgs.Boolean \
  --timeout 1000 \
  --req 'name: "box_1", position: {x: 0.0, y: 0.0, z: 0.5}'
```

Зелёная коробка прыгнет в центр сцены и упадёт.

## Связь с ROS 2

На этом шаге ROS 2 ещё **ничего не знает** о Gazebo. Топики `/clock`, `/world/...` живут только в шине Gazebo Transport. Чтобы перенести их в DDS, нужен `parameter_bridge` - этим займётся [статья 4](ros_gz_bridge.md).

## Контрольные проверки

- [x] `ros2 launch my_robot_gazebo gazebo.launch.py` открывает окно симулятора с серой плоскостью.
- [x] `gz topic -l` показывает не менее 5 топиков.
- [x] `gz model -l --world empty` возвращает хотя бы `ground_plane`.

## Дальше

[Spawn URDF робота в Gazebo](spawning_urdf.md).
