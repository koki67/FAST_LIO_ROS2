import os.path

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_path = get_package_share_directory('fast_lio')
    default_config_path = os.path.join(package_path, 'config')
    default_rviz_config_path = os.path.join(
        package_path, 'rviz', 'fastlio.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time')
    config_path = LaunchConfiguration('config_path')
    config_file = LaunchConfiguration('config_file')
    pointcloud_topic = LaunchConfiguration('pointcloud_topic')
    imu_topic = LaunchConfiguration('imu_topic')
    rviz_use = LaunchConfiguration('rviz')
    rviz_cfg = LaunchConfiguration('rviz_cfg')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )
    declare_config_path_cmd = DeclareLaunchArgument(
        'config_path', default_value=default_config_path,
        description='Yaml config file path'
    )
    declare_config_file_cmd = DeclareLaunchArgument(
        'config_file', default_value='mid360.yaml',
        description='Config file'
    )
    # The two topic args below default to the canonical Hesai+GO2-W topics so
    # `config_file:=go2w.yaml` works out of the box. For any other yaml, pass
    # the matching `pointcloud_topic:=...` and `imu_topic:=...` to override the
    # defaults declared here. These overrides always take precedence over the
    # `common.lid_topic` / `common.imu_topic` keys loaded from the yaml.
    declare_pointcloud_topic_cmd = DeclareLaunchArgument(
        'pointcloud_topic', default_value='/points_raw',
        description='LiDAR PointCloud2 topic (overrides common.lid_topic from yaml)'
    )
    declare_imu_topic_cmd = DeclareLaunchArgument(
        'imu_topic', default_value='/go2w/imu',
        description='IMU topic (overrides common.imu_topic from yaml)'
    )
    declare_rviz_cmd = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Use RViz to monitor results'
    )
    declare_rviz_config_path_cmd = DeclareLaunchArgument(
        'rviz_cfg', default_value=default_rviz_config_path,
        description='RViz config file path'
    )

    hesai_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare('hesai_lidar'), 'launch', 'hesai_lidar_launch.py'])
        ])
    )
    imu_publisher_node = Node(
        package='go2w_imu_publisher',
        executable='imu_publisher',
        output='screen',
    )

    fast_lio_node = Node(
        package='fast_lio',
        executable='fastlio_mapping',
        # Parameter sources are merged in order; entries later in the list
        # override entries earlier in the list, so the dict at the end wins
        # over the values loaded from the yaml file.
        parameters=[PathJoinSubstitution([config_path, config_file]),
                    {'use_sim_time': use_sim_time,
                     'common.lid_topic': pointcloud_topic,
                     'common.imu_topic': imu_topic}],
        output='screen'
    )
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_cfg],
        condition=IfCondition(rviz_use)
    )

    ld = LaunchDescription()
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_config_path_cmd)
    ld.add_action(declare_config_file_cmd)
    ld.add_action(declare_pointcloud_topic_cmd)
    ld.add_action(declare_imu_topic_cmd)
    ld.add_action(declare_rviz_cmd)
    ld.add_action(declare_rviz_config_path_cmd)

    ld.add_action(hesai_launch)
    ld.add_action(imu_publisher_node)
    ld.add_action(fast_lio_node)
    ld.add_action(rviz_node)

    return ld
