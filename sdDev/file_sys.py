import os
import time


def clean_files(folder_path, time_limit):
    """
    清理文件夹中超过指定时长的文件
    :param folder_path: 文件夹路径
    :param time_limit: 时长限制，单位为秒
    :return: 清理文件个数与清理掉的文件所占的储存空间大小
    """
    # 初始化清理文件个数与清理掉的文件所占的储存空间大小
    clean_file_num = 0
    clean_file_size = 0
    # 获取文件夹中的所有文件
    files = os.listdir(folder_path)
    # 遍历文件夹中的文件
    for file in files:
        # 获取文件的绝对路径
        file_path = os.path.join(folder_path, file)
        # 获取文件的修改时间
        modify_time = os.path.getmtime(file_path)
        # 获取当前时间
        current_time = time.time()
        # 计算文件的存在时长
        file_time_limit = current_time - modify_time
        # 如果文件存在时长超过指定时长，则删除文件
        if file_time_limit > time_limit:
            # 获取文件的大小
            file_size = os.path.getsize(file_path)
            # 删除文件
            os.remove(file_path)
            # 清理文件个数加1
            clean_file_num += 1
            # 清理文件大小加上文件大小
            clean_file_size += file_size
            # 打印清理文件信息
            print(f'清理文件：{file_path}，大小：{file_size/1024/1024} MB')
    # 打印清理文件结果
    print(f'清理文件个数：{clean_file_num}，清理文件大小：{clean_file_size/1024/1024} MB')

