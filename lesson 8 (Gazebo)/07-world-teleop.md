# Кастомный мир и teleop

Цель: создать мир с препятствиями для тестирования навигации и подключить управление с клавиатуры через `teleop_twist_keyboard`. К концу статьи у вас будет стенд готовый для перехода к Nav2.

## Мир с препятствиями — obstacles.sdf

Минимальный мир с парой коробок и стенами для тестирования объезда:

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
          <geometry>
            <plane><normal>0 0 1</normal><size>20 20</size></plane>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <plane><normal>0 0 1</normal><size>20 20</size></plane>
          </geometry>
          <material>
            <ambient>0.8 0.8 0.8 1</ambient>
            <diffuse>0.8 0.8 0.8 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- Коробка 1 -->
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

    <!-- Коробка 2 -->
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

Сохраните как `worlds/obstacles.sdf`. После `colcon build` он попадёт в installed share.

## Запуск с новым миром

Launch файл уже поддерживает аргумент `world`:

```bash
ros2 launch my_robot_gazebo spawn_robot.launch.py world:=obstacles
```

В Gazebo появится сцена с препятствиями. В RViz при включённом `/scan` будет видно как лидар «обводит» зелёную и красную коробки и стену.

## teleop_twist_keyboard

Пакет ставится одной командой:

```bash
sudo apt install ros-jazzy-teleop-twist-keyboard
```

Запуск:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Управление:

```
   u    i    o          U I O — strafe (для голономных)
   j    k    l          J K L
   m    ,    .

i — вперёд        k — стоп
,  — назад
j — поворот влево
l — поворот вправо
u — вперёд+влево
o — вперёд+вправо

q/z — увеличить/уменьшить все скорости на 10%
w/x — только линейную
e/c — только угловую
```

**Важно:** курсор должен быть в окне с teleop. Если в другом терминале — клавиши не доходят.

## Проверка движения

После запуска `spawn_robot.launch.py` с миром `obstacles`:

```bash
# Терминал 1
ros2 launch my_robot_gazebo spawn_robot.launch.py world:=obstacles

# Терминал 2 — teleop
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Нажмите `x` несколько раз чтобы сбавить начальную скорость до 0.1-0.2 (резкие команды могут «уронить» робот). Потом стрелки.

В RViz:
* Робот движется
* TF фреймы поворачиваются
* LaserScan «крутится» вместе с роботом, показывая препятствия

## Запись bag для последующего воспроизведения

`rosbag2` сохраняет потоки сообщений в файл. Полезно для отладки и для подачи в Nav2 без живой симуляции:

```bash
ros2 bag record -o teleop_run \
  /cmd_vel /odom /scan /imu /tf /tf_static /clock
```

Поездите роботом 30-60 секунд, потом `Ctrl+C`. В директории появится папка `teleop_run/` с записью.

Воспроизведение:

```bash
ros2 bag play teleop_run/ --clock
```

Флаг `--clock` важен — bag будет публиковать `/clock`, чтобы все ноды работали с тем же временем что в записи.

## Структура готового пакета

```
my_robot_gazebo/
├── CMakeLists.txt
├── package.xml
├── config/
│   └── ros_gz_bridge.yaml
├── launch/
│   ├── gazebo.launch.py
│   └── spawn_robot.launch.py
├── urdf/
│   ├── r2d2.urdf.xacro
│   ├── r2d2_macros.xacro
│   ├── r2d2_properties.xacro
│   └── r2d2_gazebo.xacro
└── worlds/
    ├── empty.sdf
    ├── blue.sdf
    └── obstacles.sdf
```

`CMakeLists.txt` должен устанавливать все эти директории:

```cmake
install(DIRECTORY
  config
  launch
  urdf
  worlds
  DESTINATION share/${PROJECT_NAME}
)
```

## Что готово к Nav2

После этого урока у вас есть:

* Робот в симуляции с реалистичной физикой (`/cmd_vel` → движение).
* Лазерный дальномер (`/scan` 10 Гц).
* Одометрия (`/odom` 30 Гц).
* IMU (`/imu` 100 Гц).
* TF дерево (`odom` → `base_footprint` → `base_link` → сенсоры).
* `use_sim_time` везде корректно настроен.

Это и есть стандартный интерфейс который ожидает Nav2 — следующий урок про автономную навигацию.

## Контрольные проверки

* `ros2 launch ... world:=obstacles` показывает мир с коробками.
* Лидар видит коробки в RViz при `Fixed Frame = odom`.
* `teleop_twist_keyboard` движет робота, скорости меняются `q/z`/`w/x`/`e/c`.
* `ros2 bag record` сохраняет поток, `ros2 bag play` воспроизводит.

## Возможные проблемы

**Робот уезжает за стенку при езде.** Стена тонкая (0.2м) — увеличьте до 0.4-0.5 если нужно.

**Лидар «пробивает» препятствия.** У препятствия нет `<collision>` или он меньше `<visual>`. Проверьте SDF.

**Teleop не реагирует на клавиши.** Курсор не в его окне, или раскладка не английская. Кликните на окно teleop, переключите на EN.

**Bag записал но пустой.** Не указан `--storage mcap` (по умолчанию `sqlite3`, тоже работает), или нужные топики не подписаны. Проверьте `ros2 topic list` перед записью.

## Дальше

Это конец основной части урока. Если интересует углубление — есть бонусная часть про балансирующего робота (двухколёсный R2D2 с LQR контроллером). Там разбирается физика перевёрнутого маятника, расчёт центра масс из URDF, и теория оптимального управления.
