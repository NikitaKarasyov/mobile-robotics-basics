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

Запускаем напрямую (без launch):

```bash
gz sim -r -v 3 \
  $(ros2 pkg prefix my_robot_gazebo)/share/my_robot_gazebo/worlds/empty.sdf
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

Запустите `obstacles.sdf` и в другом терминале:

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
