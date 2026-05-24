# URDF робота и Xacro макросы

Цель: подключить URDF-модель робота к Gazebo Harmonic. По пути научимся использовать **Xacro** — препроцессор XML, который убирает дублирование в URDF и позволяет параметризовать модель.

## Зачем нужен Xacro

URDF — это XML. Когда модель растёт, файл превращается в стену повторяющегося кода: четыре колеса, две ноги, набор симметричных деталей. Любое изменение нужно вносить в нескольких местах, и легко ошибиться.

Представьте что нужно изменить радиус колеса — без Xacro придётся найти и поменять это число в 8 местах (4 колеса × visual + collision). С Xacro — в одном.

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
* голова;
* грипперы как декоративный элемент.

## Структура файлов

```
my_robot_gazebo/
├── urdf/
│   ├── r2d2.urdf.xacro          ← главный файл, собирает всё вместе
│   ├── r2d2_macros.xacro        ← макросы (колесо, нога, инерции)
│   └── r2d2_properties.xacro    ← константы (массы, размеры)
├── worlds/
└── CMakeLists.txt
```

Разбивка на три файла — не обязательное требование, а хорошая практика. Константы отделены от логики макросов, а главный файл только собирает их вместе.

## Константы — r2d2_properties.xacro

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">

  <!-- Корпус -->
  <xacro:property name="base_radius" value="0.2"/>
  <xacro:property name="base_length" value="0.6"/>
  <xacro:property name="base_mass"   value="5.0"/>

  <!-- Колесо -->
  <xacro:property name="wheel_radius" value="0.035"/>
  <xacro:property name="wheel_length" value="0.1"/>
  <xacro:property name="wheel_mass"   value="0.5"/>

  <!-- Нога -->
  <xacro:property name="leg_size_x" value="0.6"/>
  <xacro:property name="leg_size_y" value="0.1"/>
  <xacro:property name="leg_size_z" value="0.2"/>
  <xacro:property name="leg_mass"   value="0.5"/>

  <!-- База ноги -->
  <xacro:property name="legbase_size_x" value="0.4"/>
  <xacro:property name="legbase_size_y" value="0.1"/>
  <xacro:property name="legbase_size_z" value="0.1"/>
  <xacro:property name="legbase_mass"   value="0.3"/>

  <!-- Голова -->
  <xacro:property name="head_radius" value="0.2"/>
  <xacro:property name="head_mass"   value="1.0"/>

  <!-- Расположение ног и колёс -->
  <xacro:property name="leg_offset_y"   value="0.22"/>
  <xacro:property name="leg_offset_z"   value="0.25"/>
  <xacro:property name="wheel_offset_x" value="0.133"/>
  <xacro:property name="wheel_offset_z" value="-0.085"/>

</robot>
```

Обратите внимание — файл тоже начинается с `<robot>`. Xacro просто объединяет содержимое всех подключённых файлов в один XML перед разворачиванием макросов.

## Макросы инерции — зачем они нужны

Каждый линк с массой должен иметь тег `<inertial>` с тензором инерции — иначе Gazebo будет вести себя нестабильно или зависнет. Считать тензор вручную для каждой детали утомительно, поэтому оформим расчёт как макрос.

Формулы для стандартных геометрических тел:

```xml
<!-- Инерция цилиндра: m — масса, r — радиус, h — высота -->
<xacro:macro name="cylinder_inertia" params="m r h">
  <inertial>
    <mass value="${m}"/>
    <inertia
      ixx="${m*(3*r*r + h*h)/12}" ixy="0" ixz="0"
      iyy="${m*(3*r*r + h*h)/12}" iyz="0"
      izz="${m*r*r/2}"/>
  </inertial>
</xacro:macro>
```

Синтаксис `${...}` — это вычисляемое выражение. `${m*r*r/2}` посчитается в момент препроцессинга и подставится как число. Так мы получаем формулы прямо в URDF.

`ixx`, `iyy`, `izz` — диагональные элементы тензора инерции. Для симметричных тел (цилиндр, сфера, куб) остальные элементы равны нулю, поэтому `ixy=0`, `ixz=0`, `iyz=0`.

```xml
<!-- Инерция box: m — масса, x/y/z — стороны -->
<xacro:macro name="box_inertia" params="m x y z">
  <inertial>
    <mass value="${m}"/>
    <inertia
      ixx="${m*(y*y + z*z)/12}" ixy="0" ixz="0"
      iyy="${m*(x*x + z*z)/12}" iyz="0"
      izz="${m*(x*x + y*y)/12}"/>
  </inertial>
</xacro:macro>

<!-- Инерция сферы: m — масса, r — радиус -->
<xacro:macro name="sphere_inertia" params="m r">
  <inertial>
    <mass value="${m}"/>
    <inertia
      ixx="${2*m*r*r/5}" ixy="0" ixz="0"
      iyy="${2*m*r*r/5}" iyz="0"
      izz="${2*m*r*r/5}"/>
  </inertial>
</xacro:macro>
```

Для сферы все три диагональных элемента одинаковы — сфера симметрична по всем осям.

## Макрос колеса

```xml
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
```

Разберём параметры макроса:

* `side` — `left` или `right`. Используется в имени линка: `${side}_${position}_wheel` → `left_front_wheel`.
* `position` — `front` или `back`. Вместе с `side` даёт уникальное имя каждому из четырёх колёс.
* `parent` — имя линка-родителя (база ноги). Колесо крепится к нему.
* `x_offset` — смещение по X от центра базы. Переднее колесо +0.133, заднее -0.133.

Почему `rpy="1.57075 0 0"` (поворот на π/2 вокруг X)? В URDF цилиндр по умолчанию стоит вертикально — его ось симметрии направлена по Z. Колесо должно лежать на боку, ось вращения по Y. Поворот на 90° вокруг X «укладывает» цилиндр набок.

Почему `axis xyz="0 1 0"`? Это ось вращения сустава — колесо крутится вокруг Y (поперёк направления движения). Именно так работает diff-drive: левое и правое колёса крутятся независимо вокруг общей поперечной оси.

Тип сустава `continuous` — бесконечное вращение без ограничений. Для колёс это правильно, в отличие от `revolute` (ограниченный угол) или `prismatic` (линейное смещение).

## Макрос сборки ноги

```xml
<xacro:macro name="leg_assembly" params="side y_sign">

  <!-- Нога — горизонтальная балка -->
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
    <xacro:box_inertia m="${leg_mass}"
                       x="${leg_size_x}" y="${leg_size_y}" z="${leg_size_z}"/>
  </link>

  <!-- Нога крепится к корпусу -->
  <joint name="base_to_${side}_leg" type="fixed">
    <parent link="base_link"/>
    <child link="${side}_leg"/>
    <origin xyz="0 ${y_sign * leg_offset_y} ${leg_offset_z}"/>
  </joint>

  <!-- База ноги — горизонтальная пластина с колёсами -->
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

  <!-- Два колеса на базе — вызов макроса wheel -->
  <xacro:wheel side="${side}" position="front"
               parent="${side}_base" x_offset="${wheel_offset_x}"/>
  <xacro:wheel side="${side}" position="back"
               parent="${side}_base" x_offset="-${wheel_offset_x}"/>

</xacro:macro>
```

Параметр `y_sign` — это либо `1`, либо `-1`. Левая нога крепится на `+leg_offset_y` от центра, правая на `-leg_offset_y`. Вместо двух почти одинаковых блоков кода используем один макрос с разным знаком смещения: `${y_sign * leg_offset_y}`.

Зачем `type="fixed"` для суставов ног и базы? Нога и база — жёсткая конструкция, они не должны двигаться относительно корпуса. Fixed сустав в Gazebo не имеет степеней свободы — Gazebo вообще объединяет все fixed-линки в один твёрдый объект.

В конце макроса два вызова `xacro:wheel` — это и есть мощь макросов. Одна строка разворачивается в целый блок описания линка и сустава.

## Главный файл — r2d2.urdf.xacro

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="r2d2">

  <!-- Подключаем вспомогательные файлы -->
  <xacro:include filename="$(find my_robot_gazebo)/urdf/r2d2_properties.xacro"/>
  <xacro:include filename="$(find my_robot_gazebo)/urdf/r2d2_macros.xacro"/>

  <!-- Материалы — задаём цвета один раз, используем по имени -->
  <material name="blue"><color rgba="0 0 0.8 1"/></material>
  <material name="black"><color rgba="0 0 0 1"/></material>
  <material name="white"><color rgba="1 1 1 1"/></material>

  <!-- base_footprint — стандартный root фрейм на уровне пола.
       ROS конвенция: этот фрейм всегда на земле под роботом.
       Используется Nav2 и другими пакетами навигации. -->
  <link name="base_footprint"/>

  <joint name="base_footprint_joint" type="fixed">
    <parent link="base_footprint"/>
    <child link="base_link"/>
    <origin xyz="0 0 0.1"/>  <!-- корпус поднят на 10 см над footprint -->
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
    <!-- Вызов макроса инерции — передаём параметры по имени -->
    <xacro:cylinder_inertia m="${base_mass}" r="${base_radius}" h="${base_length}"/>
  </link>

  <!-- Левая и правая сборка ноги — два вызова одного макроса -->
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

`$(find my_robot_gazebo)` — это специальный синтаксис Xacro/ROS. Он раскрывается в путь к установленному пакету. Работает только когда пакет собран и sourced.

Обратите внимание на `xacro:include` в начале — сначала подключаем свойства, потом макросы. Порядок важен: макросы используют свойства, значит свойства должны быть определены раньше.

## Проверка препроцессинга

Прежде чем подключать к Gazebo, убедимся что Xacro корректно разворачивает файл:

```bash
cd ~/ros2_ws
colcon build --packages-select my_robot_gazebo
source install/setup.bash

ros2 run xacro xacro \
  $(ros2 pkg prefix my_robot_gazebo)/share/my_robot_gazebo/urdf/r2d2.urdf.xacro
```

Вывод — обычный URDF со всеми развёрнутыми макросами. Если где-то опечатка в имени переменной или неверные параметры макроса — Xacro покажет точное место с номером строки. Это гораздо удобнее чем ошибки в рантайме Gazebo.

## CMakeLists.txt

Чтобы файлы попали в установленный пакет, добавьте в `CMakeLists.txt` перед `ament_package()`:

```cmake
install(DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)
```

После пересборки `urdf/` появится в `install/my_robot_gazebo/share/my_robot_gazebo/urdf/` — именно оттуда `$(find my_robot_gazebo)` будет их находить.

## robot_state_publisher

`robot_state_publisher` берёт URDF и углы суставов из `/joint_states`, вычисляет TF дерево и публикует его в `/tf`. Без него RViz не знает где находятся колёса относительно корпуса.

В launch файле ему передаётся результат команды `xacro r2d2.urdf.xacro` как строка через параметр `robot_description`. Xacro запускается **в момент запуска launch**, на лету — не нужно отдельно конвертировать `.xacro` → `.urdf`.

Как именно это выглядит в коде — увидим в следующей статье где `robot_state_publisher` запускается вместе с Gazebo и мостом в одном launch файле.

## Расчёт центра масс из URDF

Когда модель собрана, часто нужно знать положение центра масс (ЦМ) всего робота. Это важно для устойчивости на склонах, расчёта нагрузки и проектирования контроллеров.

Формула — взвешенное среднее положений всех линков:

```
z_цм = Σ(mᵢ · zᵢ) / Σmᵢ
```

Чтобы получить абсолютную высоту каждого линка — идём по дереву суставов от корня и складываем смещения:

```
base_footprint (z=0)
    ↓ base_footprint_joint: +0.1
base_link (z=0.1)
    ↓ base_to_right_leg: +0.25
right_leg (z=0.35)
    ↓ right_base_joint: -0.6
right_base (z=-0.25)
    ↓ wheel_joint: -0.085
right_front_wheel (z=-0.335)
```

Скрипт расчёта:

```python
import numpy as np

joints = {
    'base_footprint_joint': {'parent': 'base_footprint', 'child': 'base_link',         'z': 0.1},
    'base_to_right_leg':    {'parent': 'base_link',      'child': 'right_leg',         'z': 0.25},
    'base_to_left_leg':     {'parent': 'base_link',      'child': 'left_leg',          'z': 0.25},
    'right_base_joint':     {'parent': 'right_leg',      'child': 'right_base',        'z': -0.6},
    'left_base_joint':      {'parent': 'left_leg',       'child': 'left_base',         'z': -0.6},
    'right_wheel_joint':    {'parent': 'right_base',     'child': 'right_front_wheel', 'z': -0.085},
    'left_wheel_joint':     {'parent': 'left_base',      'child': 'left_front_wheel',  'z': -0.085},
    'head_swivel':          {'parent': 'base_link',      'child': 'head',              'z': 0.3},
}

masses = {
    'base_link': 5.0, 'right_leg': 0.5, 'left_leg': 0.5,
    'right_base': 0.3, 'left_base': 0.3,
    'right_front_wheel': 0.5, 'left_front_wheel': 0.5,
    'head': 1.0,
}

z_abs = {'base_footprint': 0.0}
changed = True
while changed:
    changed = False
    for j, data in joints.items():
        if data['parent'] in z_abs and data['child'] not in z_abs:
            z_abs[data['child']] = z_abs[data['parent']] + data['z']
            changed = True

total_m  = sum(masses.values())
total_mz = sum(masses[link] * z_abs[link] for link in masses)
z_cm = total_mz / total_m
print(f"ЦМ робота: z = {z_cm:.3f} м от base_footprint")
```

Быстрая проверка в Gazebo: **View → Center of Mass** — появится маркер в позиции ЦМ.

## Контрольные проверки

* `ros2 run xacro xacro r2d2.urdf.xacro` выводит валидный URDF без ошибок.
* В выводе есть 4 колеса: `left_front_wheel`, `left_back_wheel`, `right_front_wheel`, `right_back_wheel`.
* После запуска launch с `robot_state_publisher` команда `ros2 topic echo /robot_description` показывает развёрнутый URDF.
* `ros2 run tf2_tools view_frames` строит граф: `base_footprint → base_link → head, left_leg, right_leg → ...`.

## Дальше

В следующей статье — [спавн робота в Gazebo](./04-spawn-robot.md) и подключение плагина diff-drive.
