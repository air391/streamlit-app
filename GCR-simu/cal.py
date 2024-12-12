import numpy as np
def box_intersection_length(origins, directions, box_min, box_max):
    """
    计算多个线段与长方体的相交长度
    
    参数:
    - origins: N*3 数组，线段起点
    - directions: N*3 数组，方向向量
    - box_min: 长方体最小坐标点
    - box_max: 长方体最大坐标点
    
    返回: N长度的相交长度数组
    """
    # 对每个坐标轴计算交点
    tmin = np.full(origins.shape[0], float('-inf'))
    tmax = np.full(origins.shape[0], float('inf'))
    
    for i in range(3):
        # 处理方向向量在该轴上为0的情况
        zero_dir_mask = directions[:, i] == 0
        
        # 计算非零方向的交点
        t1 = (box_min[i] - origins[:, i]) / directions[:, i]
        t2 = (box_max[i] - origins[:, i]) / directions[:, i]
        
        # 更新tmin和tmax
        temp_tmin = np.minimum(t1, t2)
        temp_tmax = np.maximum(t1, t2)
        
        tmin = np.maximum(tmin, temp_tmin)
        tmax = np.minimum(tmax, temp_tmax)
    
    # 计算相交长度
    intersection_lengths = np.maximum(0, tmax - tmin)
    intersection_lengths[tmax < tmin] = 0
    intersection_lengths[tmax < 0] = 0
    
    return intersection_lengths
def is_point_in_box(point, box_min, box_max):
    """
    检查点是否在长方体内
    
    参数:
    - point: 待检查点坐标 [x, y, z]
    - box_min: 长方体最小坐标点
    - box_max: 长方体最大坐标点
    
    返回: 布尔值，点是否在长方体内
    """
    return np.all((point >= box_min) & (point <= box_max))
def filter_points_in_box(points, box_min, box_max):
    """
    批量检查点是否在长方体内
    
    参数:
    - points: 点集 (N x 3 数组)
    - box_min: 长方体最小坐标点
    - box_max: 长方体最大坐标点
    
    返回: 不在长方体内的点
    """
    mask = np.all((points >= box_min) & (points <= box_max), axis=1)
    return points[~mask]
def generate_points(num_points, box_min, box_max):
    """
    在指定长方体内生成均匀分布的随机点
    
    参数:
    - num_points: 点的数量
    - box_min: 长方体最小坐标点
    - box_max: 长方体最大坐标点
    
    返回: 长方体内的随机点
    """
    # 生成[0,1]区间点
    points = np.random.rand(num_points, 3)
    # 缩放和平移到目标长方体
    points = points * (box_max - box_min) + box_min
    
    return points
def generate_directions(num_directions, half=False):
    """
    批量生成球面均匀分布的随机方向
    
    参数:
    - num_directions: 方向数量
    
    返回: 球面均匀分布的单位方向向量
    """
    # 使用均匀分布的极角和方位角
    theta = np.random.uniform(0, 2*np.pi, num_directions)
    max_phi = np.pi/2 if half else np.pi
    phi = np.random.uniform(0, max_phi, num_directions)

    x = np.sin(phi) * np.cos(theta)
    y = np.sin(phi) * np.sin(theta)
    z = np.cos(phi)
    return np.column_stack([x, y, z])
