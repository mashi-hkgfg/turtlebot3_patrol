"""一键巡件：Gazebo 世界 + Nav2 导航（加载自己的地图）+ 巡件节点。

用法：
  ros2 launch patrol patrol.launch.py
  （可选换地图：ros2 launch patrol patrol.launch.py map:=/绝对/路径/map.yaml）

注意：不要嵌套包含 turtlebot3_navigation2/navigation2.launch.py —— 嵌套包含时其
params_file 参数会解析为空串导致启动失败，因此本文件直接包含 nav2_bringup 并显式传参。
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

DEFAULT_MAP = os.path.expanduser('~/turtlebot3_patrol/map/map.yaml')

TB3_GAZEBO = get_package_share_directory('turtlebot3_gazebo')
NAV2_BRINGUP = get_package_share_directory('nav2_bringup')
TB3_NAV2 = get_package_share_directory('turtlebot3_navigation2')

# 与 turtlebot3_navigation2/navigation2.launch.py 内部计算一致
PARAMS_FILE = os.path.join(TB3_NAV2, 'param', 'humble', 'waffle.yaml')
RVIZ_CONFIG = os.path.join(TB3_NAV2, 'rviz', 'tb3_navigation2.rviz')


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=DEFAULT_MAP,
            description='要加载的地图 yaml 绝对路径'),

        # 1) 仿真世界：waffle + turtlebot3_world（Gazebo）
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(TB3_GAZEBO, 'launch', 'turtlebot3_world.launch.py'))),

        # 2) Nav2 导航栈（AMCL + 代价地图 + 规划/控制 + recovery）
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(NAV2_BRINGUP, 'launch', 'bringup_launch.py')),
            launch_arguments={
                'map': LaunchConfiguration('map'),
                'params_file': PARAMS_FILE,     # 显式传参，避免解析为空串
                'use_sim_time': 'true',         # 仿真环境统一使用仿真时钟（与 Gazebo 数据时间戳一致）
                'autostart': 'true',
            }.items()),

        # 3) RViz（与官方 nav2 launch 同一个配置）
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', RVIZ_CONFIG],
            parameters=[{'use_sim_time': True}],
            output='screen'),

        # 4) 巡件大脑：精确初始位姿 → 依序导航 3 点
        Node(
            package='patrol',
            executable='patrol_node',
            parameters=[{'use_sim_time': True}],
            output='screen'),
    ])
