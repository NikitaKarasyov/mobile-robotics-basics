# URDF робота и Xacro макросы

Цель: подключить URDF-модель робота к Gazebo Harmonic. По пути научимся использовать **Xacro** — препроцессор XML, который убирает дублирование в URDF и позволяет параметризовать модель.

## Зачем нужен Xacro

URDF — это XML. Когда модель растёт, файл превращается в стену повторяющегося кода: четыре колеса, две ноги, набор симметричных деталей. Любое изменение нужно вносить в нескольких местах, и легко ошибиться.

Xacro решает три проблемы:

| Возможность | Что даёт |
|---|---|
| `<xacro:property>` | Константы (радиус колеса, длина ноги) в одном месте |
| `<xacro:macro>` | Шаблоны для повторяющихся деталей (колесо, нога) |
| `<xacro:include>` | Разбивка модели на файлы |

На входе — `.xacro` файл. На выходе после препроцессинга — обычный URDF, который Gazebo и `robot_state_publisher` понимают как раньше.

## Что собираем

Возьмём классического R2D2 из туториала ROS, но перепишем его на Xacro:

* `base_link` — цилиндрический корпус;
* две ноги с базами и по два колеса на каждой стороне (всего 4 колеса);
* голова со «шляпой»;
* грипперы как декоративный элемент.

Колёса будут параметризованы — массы, радиусы и положение задаются константами.

## Структура файлов

```
my_robot_gazebo/
├── urdf/
│   ├── r2d2.urdf.xacro          ← главный файл
│   ├── r2d2_macros.xacro        ← макросы (колесо, нога)
│   └── r2d2_properties.xacro    ← константы (массы, размеры)
├── worlds/
│   ├── empty.sdf
│   └── blue.sdf
└── CMakeLists.txt
```

## Константы — r2d2_properties.xacro

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">

  <!-- Корпус -->
  <xacro:property name="base_radius" value="0.2"/>
  <xacro:property name="base_length" value="0.6"/>
  <xacro:property name="base_mass" value="5.0"/>

  <!-- Колесо -->
  <xacro:property name="wheel_radius" value="0.035"/>
  <xacro:property name="wheel_length" value="0.1"/>
  <xacro:property name="wheel_mass" value="0.5"/>

  <!-- Нога -->
  <xacro:property name="leg_size_x" value="0.6"/>
  <xacro:property name="leg_size_y" value="0.1"/>
  <xacro:property name="leg_size_z" value="0.2"/>
  <xacro:property name="leg_mass" value="0.5"/>

  <!-- База ноги -->
  <xacro:property name="legbase_size_x" value="0.4"/>
  <xacro:property name="legbase_size_y" value="0.1"/>
  <xacro:property name="legbase_size_z" value="0.1"/>
  <xacro:property name="legbase_mass" value="0.3"/>

  <!-- Голова -->
  <xacro:property name="head_radius" value="0.2"/>
  <xacro:property name="head_mass" value="1.0"/>

  <!-- Размещение -->
  <xacro:property name="leg_offset_y" value="0.22"/>
  <xacro:property name="leg_offset_z" value="0.25"/>
  <xacro:property name="wheel_offset_x" value="0.133"/>
  <xacro:property name="wheel_offset_z" value="-0.085"/>

</robot>
```

Все размеры в одном месте — изменили `wheel_radius`, обновились все четыре колеса.

## Макросы — r2d2_macros.xacro

Макрос колеса — параметризован стороной (`left`/`right`), положением (`front`/`back`) и родительским линком:

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">

  <!-- Инерция цилиндра (используется для корпуса и колёс) -->
  <xacro:macro name="cylinder_inertia" params="m r h">
    <inertial>
      <mass value="${m}"/>
      <inertia
        ixx="${m*(3*r*r + h*h)/12}" ixy="0" ixz="0"
        iyy="${m*(3*r*r + h*h)/12}" iyz="0"
        izz="${m*r*r/2}"/>
    </inertial>
  </xacro:macro>

  <!-- Инерция box -->
  <xacro:macro name="box_inertia" params="m x y z">
    <inertial>
      <mass value="${m}"/>
      <inertia
        ixx="${m*(y*y + z*z)/12}" ixy="0" ixz="0"
        iyy="${m*(x*x + z*z)/12}" iyz="0"
        izz="${m*(x*x + y*y)/12}"/>
    </inertial>
  </xacro:macro>

  <!-- Инерция сферы -->
  <xacro:macro name="sphere_inertia" params="m r">
    <inertial>
      <mass value="${m}"/>
      <inertia
        ixx="${2*m*r*r/5}" ixy="0" ixz="0"
        iyy="${2*m*r*r/5}" iyz="0"
        izz="${2*m*r*r/5}"/>
    </inertial>
  </xacro:macro>

  <!-- Макрос колеса -->
  <xacro:macro name="wheel" params="side position parent x_offset">
    <link name="${side}_${position}_wheel">
      <visual>
        <origin rpy="1.57075 0 0" xyz="0 0 0"/>
        <geometry>
          <cylinder length="${wheel_length}" radius="${wheel_radius}"/>
        </geometry>
        <material name="black"/>
      </visual>
      <collision>
        <origin rpy="1.57075 0 0" xyz="0 0 0"/>
        <geometry>
          <cylinder length="${wheel_length}" radius="${wheel_radius}"/>
        </geometry>
      </collision>
      <xacro:cylinder_inertia m="${wheel_mass}" r="${wheel_radius}" h="${wheel_length}"/>
    </link>

    <joint name="${side}_${position}_wheel_joint" type="continuous">
      <parent link="${parent}"/>
      <child link="${side}_${position}_wheel"/>
      <origin xyz="${x_offset} 0 ${wheel_offset_z}"/>
      <axis xyz="0 1 0"/>
    </joint>
  </xacro:macro>

  <!-- Макрос ноги с базой и двумя колёсами -->
  <xacro:macro name="leg_assembly" params="side y_sign">
    <link name="${side}_leg">
      <visual>
        <origin rpy="0 1.57075 0" xyz="0 0 -0.3"/>
        <geometry>
          <box size="${leg_size_x} ${leg_size_y} ${leg_size_z}"/>
        </geometry>
        <material name="white"/>
      </visual>
      <collision>
        <origin rpy="0 1.57075 0" xyz="0 0 -0.3"/>
        <geometry>
          <box size="${leg_size_x} ${leg_size_y} ${leg_size_z}"/>
        </geometry>
      </collision>
      <xacro:box_inertia m="${leg_mass}" x="${leg_size_x}" y="${leg_size_y}" z="${leg_size_z}"/>
    </link>

    <joint name="base_to_${side}_leg" type="fixed">
      <parent link="base_link"/>
      <child link="${side}_leg"/>
      <origin xyz="0 ${y_sign * leg_offset_y} ${leg_offset_z}"/>
    </joint>

    <link name="${side}_base">
      <visual>
        <geometry>
          <box size="${legbase_size_x} ${legbase_size_y} ${legbase_size_z}"/>
        </geometry>
        <material name="white"/>
      </visual>
      <collision>
        <geometry>
          <box size="${legbase_size_x} ${legbase_size_y} ${legbase_size_z}"/>
        </geometry>
      </collision>
      <xacro:box_inertia m="${legbase_mass}"
                         x="${legbase_size_x}"
                         y="${legbase_size_y}"
                         z="${legbase_size_z}"/>
    </link>

    <joint name="${side}_base_joint" type="fixed">
      <parent link="${side}_leg"/>
      <child link="${side}_base"/>
      <origin xyz="0 0 -0.6"/>
    </joint>

    <xacro:wheel side="${side}" position="front" parent="${side}_base" x_offset="${wheel_offset_x}"/>
    <xacro:wheel side="${side}" position="back" parent="${side}_base" x_offset="-${wheel_offset_x}"/>
  </xacro:macro>

</robot>
```

Обратите внимание на синтаксис `${...}` — это вычисляемые выражения Xacro. Внутри можно использовать арифметику: `${m*r*r/2}` посчитается во время препроцессинга.

## Главный файл — r2d2.urdf.xacro

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="r2d2">

  <xacro:include filename="$(find my_robot_gazebo)/urdf/r2d2_properties.xacro"/>
  <xacro:include filename="$(find my_robot_gazebo)/urdf/r2d2_macros.xacro"/>

  <!-- Материалы -->
  <material name="blue"><color rgba="0 0 0.8 1"/></material>
  <material name="black"><color rgba="0 0 0 1"/></material>
  <material name="white"><color rgba="1 1 1 1"/></material>

  <!-- base_footprint — стандартный root фрейм на уровне пола -->
  <link name="base_footprint"/>

  <joint name="base_footprint_joint" type="fixed">
    <parent link="base_footprint"/>
    <child link="base_link"/>
    <origin xyz="0 0 0.1"/>
  </joint>

  <!-- Корпус -->
  <link name="base_link">
    <visual>
      <geometry>
        <cylinder length="${base_length}" radius="${base_radius}"/>
      </geometry>
      <material name="blue"/>
    </visual>
    <collision>
      <geometry>
        <cylinder length="${base_length}" radius="${base_radius}"/>
      </geometry>
    </collision>
    <xacro:cylinder_inertia m="${base_mass}" r="${base_radius}" h="${base_length}"/>
  </link>

  <!-- Сборка ног — один вызов на каждую сторону -->
  <xacro:leg_assembly side="right" y_sign="-1"/>
  <xacro:leg_assembly side="left"  y_sign="1"/>

  <!-- Голова -->
  <link name="head">
    <visual>
      <geometry>
        <sphere radius="${head_radius}"/>
      </geometry>
      <material name="white"/>
    </visual>
    <collision>
      <geometry>
        <sphere radius="${head_radius}"/>
      </geometry>
    </collision>
    <xacro:sphere_inertia m="${head_mass}" r="${head_radius}"/>
  </link>

  <joint name="head_swivel" type="fixed">
    <parent link="base_link"/>
    <child link="head"/>
    <origin xyz="0 0 0.3"/>
  </joint>

</robot>
```

Финальный файл короче и читаемее исходного «плоского» URDF в полтора раза, при этом семантически они эквивалентны.

## Проверка препроцессинга

Прежде чем подключать к Gazebo, проверим что Xacro корректно генерирует URDF:

```bash
cd ~/ros2_ws
colcon build --packages-select my_robot_gazebo
source install/setup.bash

ros2 run xacro xacro \
  $(ros2 pkg prefix my_robot_gazebo)/share/my_robot_gazebo/urdf/r2d2.urdf.xacro
```

Вывод — обычный URDF, развёрнутый из макросов. Если синтаксическая ошибка, Xacro покажет точное место.

## Установка файлов через CMakeLists.txt

В `CMakeLists.txt` пакета добавьте:

```cmake
install(DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)
```

После пересборки `urdf/` появится в `install/my_robot_gazebo/share/`.

## robot_state_publisher

Чтобы TF дерево обновлялось и Gazebo получил описание робота, нужен `robot_state_publisher`. Он берёт URDF из параметра и публикует фреймы каждого линка.

В launch файле:

```python
from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution, Command, FindExecutable
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'), ' ',
            PathJoinSubstitution([
                FindPackageShare('my_robot_gazebo'),
                'urdf', 'r2d2.urdf.xacro'
            ])
        ]),
        value_type=str
    )

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    return LaunchDescription([rsp])
```

Обратите внимание — Xacro запускается **в момент запуска launch**, на лету. Не нужно отдельно конвертировать `.xacro` → `.urdf`.

## Контрольные проверки

* `ros2 run xacro xacro r2d2.urdf.xacro` выводит валидный URDF без ошибок.
* После запуска launch с `robot_state_publisher` команда `ros2 topic echo /robot_description` показывает развёрнутый URDF.
* `ros2 run tf2_tools view_frames` строит граф фреймов: `base_footprint → base_link → head, left_leg, right_leg → ...`.

## Дальше

В следующей статье — спавн робота в Gazebo через `ros_gz_sim create` и подключение плагина diff-drive для управления колёсами.
