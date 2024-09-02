import math
from io import BytesIO
from PyQt5.QtGui import QPixmap

def dms_to_degrees(d, m, s):
    """将度分秒转换为十进制度"""
    return d + m / 60.0 + s / 3600.0

def degrees_to_radians(degrees):
    """将十进制度转换为弧度"""
    return degrees * math.pi / 180

def calculate_polygon_points(start_x, start_y, angles, lengths,angle):
    """计算多边形的顶点坐标"""
    points = [(start_x, start_y)]
    current_angle = angle  # 初始方向角为90度，即正北方向

    for i in range(len(angles)):
        angle_degrees = dms_to_degrees(*angles[i])
        current_angle += angle_degrees - 180  # 转换为外角
        angle_radians = degrees_to_radians(current_angle)

        x = points[-1][0] + lengths[i] * math.cos(angle_radians)
        y = points[-1][1] + lengths[i] * math.sin(angle_radians)
        points.append((x, y))

    return points

def calculate_closure_error(points):
    """计算坐标的闭合差"""
    start_point = points[0]
    end_point = points[-1]
    closure_error_x = end_point[0] - start_point[0]
    closure_error_y = end_point[1] - start_point[1]
    return closure_error_x, closure_error_y

def distribute_closure_error(points, lengths, closure_error_x, closure_error_y):
    """将闭合差按照边长加权反号分配到每个顶点"""
    total_length = sum(lengths)
    corrections = []
    corrected_points = [points[0]]  # 起点坐标不变

    for i in range(1, len(points)):
        weight = lengths[i-1] / total_length
        correction_x = -closure_error_x * weight
        correction_y = -closure_error_y * weight

        corrected_x = corrected_points[-1][0] + (points[i][0] - points[i-1][0]) + correction_x
        corrected_y = corrected_points[-1][1] + (points[i][1] - points[i-1][1]) + correction_y
        
        corrections.append((correction_x, correction_y))
        corrected_points.append((corrected_x, corrected_y))
    
    return corrected_points, corrections

def value_point(self):
    d = self.ui.lineEdit_3.text() or "0"
    m = self.ui.lineEdit_4.text() or "0"
    s = self.ui.lineEdit_5.text() or "0"
    d = float(d)
    m = float(m)
    s = float(s)
    return dms_to_degrees(d,m,s)

def add_data_(df, dict2):
    first_column_name = df.columns[0]
    first_column_values = df[first_column_name].tolist()
    first_column_values.append(first_column_values[0])
    merged_dict = {first_column_name: first_column_values}
    merged_dict.update(dict2)
    return merged_dict

import matplotlib.pyplot as plt
import numpy as np

def dms_to_degrees(d, m, s):
    """Convert degrees, minutes, seconds to decimal degrees"""
    return d + m / 60.0 + s / 3600.0

def calculate_polygon_points_no(angles, lengths):
    """Calculate the coordinates of the polygon vertices based on internal angles and lengths"""
    points = [(0, 0)]
    current_angle = 0

    for i in range(len(angles)):
        # Convert internal angle to external angle for calculation
        current_angle -= 180 - dms_to_degrees(*angles[i])
        angle_rad = np.deg2rad(current_angle)
        x = points[-1][0] + lengths[i] * np.cos(angle_rad)
        y = points[-1][1] + lengths[i] * np.sin(angle_rad)
        points.append((x, y))

    return points

def plot_polygon(points, point_labels, angles, lengths,num):
    """Plot the polygon and label the points"""
    fig, ax = plt.subplots()
    
    x_coords, y_coords = zip(*points)
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)

    # Adjust plot size based on points
    ax.set_xlim(min_x - 5, max_x + 5)
    ax.set_ylim(min_y - 5, max_y + 5)

    # Check if the polygon is closed
    final_segment_length = np.sqrt((points[0][0] - points[-1][0]) ** 2 + (points[0][1] - points[-1][1]) ** 2)
    is_closed = np.isclose(final_segment_length, 0)

    if is_closed:
        polygon = plt.Polygon(points, closed=True, fill=None, edgecolor='r')
        ax.add_patch(polygon)
    else:
        # Plot the polygon with the last edge in red if not closed
        polygon = plt.Polygon(points[:-1], closed=False, fill=None, edgecolor='black')
        ax.add_patch(polygon)
        ax.plot([points[-2][0], points[0][0]], [points[-2][1], points[0][1]], 'r')
        excess_length = final_segment_length
        mid_x = (points[-2][0] + points[0][0]) / 2
        mid_y = (points[-2][1] + points[0][1]) / 2
        plt.text(mid_x, mid_y, f"{excess_length:.2f}", fontsize=10, ha='center', va='bottom', color='red')

    for i, (x, y) in enumerate(points[:-1]):  # Avoid the last duplicated point
        label = f"{point_labels[i]}"
        plt.text(x, y, label, fontsize=12, ha='right', va='bottom')
    
    for i, angle in enumerate(angles):
        d, m, s = angle
        angle_label = f"{d}°{m}'{s}''"
        x, y = points[i]
        plt.text(x, y - 1, angle_label, fontsize=10, ha='right', va='top', color='blue')  # Adjusted position
    
    for i in range(len(lengths)):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        length_label = f"{lengths[i]:.2f}"
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        plt.text(mid_x, mid_y, length_label, fontsize=10, ha='center', va='center', color='green')  # Adjusted position
    
    ax.set_aspect('equal', adjustable='datalim')
    plt.grid(True)
    if num=='0':
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()  # 关闭图像以释放资源
        return buf
    else :
        plt.show()
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

def image_to_label(buf, label):
    """
    将图像数据加载到 QLabel 上，并设置指定的大小。

    :param buf: 图像数据的字节流。
    :param label: QLabel 控件，用于显示图像。
    """
    pixmap = QPixmap()
    pixmap.loadFromData(buf.getvalue(), format='PNG')
    
    # 调整图片大小
    pixmap = pixmap.scaled(161, 121, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
    label.setPixmap(pixmap)


import pandas as pd
import matplotlib.pyplot as plt

def draw_bal(df,num):
    """
    从 DataFrame 中提取点号、修正后坐标x 和 修正后坐标y，绘制图形并连接所有点。
    
    :param df: 包含数据的 DataFrame，必须包含 '点号'、'修正后坐标x' 和 '修正后坐标y' 列。
    """
    # 提取数据
    point_labels = df['点号'].tolist()
    x_coords = df['修正后坐标x'].tolist()
    y_coords = df['修正后坐标y'].tolist()

    # 创建图形
    plt.figure(figsize=(10, 6))
    
    # 绘制点
    plt.scatter(x_coords, y_coords, color='red', label='Points')
    
    # 连接所有点
    for i in range(len(x_coords)):
        if i < len(x_coords) - 1:
            plt.plot([x_coords[i], x_coords[i + 1]], [y_coords[i], y_coords[i + 1]], 'b-o')
    
    # 绘制最后一个点与第一个点的连接
    if len(x_coords) > 1:
        plt.plot([x_coords[-1], x_coords[0]], [y_coords[-1], y_coords[0]], 'b-o')

    # 添加点标签
    for i, label in enumerate(point_labels):
        plt.text(x_coords[i], y_coords[i], label, fontsize=9, ha='right')
    
    # 设置图形标题和轴标签
    plt.title('Point Plot with Connections')
    plt.xlabel('修正后坐标x')
    plt.ylabel('修正后坐标y')
    plt.grid(True)
    plt.legend()
    if num=='0':
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()  # 关闭图像以释放资源
        return buf
    else :
        plt.show()
        
