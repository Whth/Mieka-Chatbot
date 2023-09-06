import psutil
import pynvml


def get_gpu_info() -> str:
    """
    Retrieves information about the available GPUs on the system.

    Returns:
        str: A string containing information about each GPU, including name, utilization rate, power usage, temperature, and memory usage.
    """
    pynvml.nvmlInit()

    # 获取可用的GPU数量
    device_count = pynvml.nvmlDeviceGetCount()

    gpu_info = "GPU 信息:\n"

    for i in range(device_count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)

        # 获取GPU名称
        name = pynvml.nvmlDeviceGetName(handle)

        # 获取GPU温度
        temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)

        # 获取GPU内存信息
        memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        power_usage = pynvml.nvmlDeviceGetPowerUsage(handle)
        # 合并GPU信息到字符串
        gpu_info += "=========================\n"
        gpu_info += f"GPU {i+1}: {name}\n"
        gpu_info += f"\t占用率: {utilization.gpu}%\n"
        gpu_info += f"\t功耗: {power_usage/1000:.1f} W\n"
        gpu_info += f"\t温度: {temperature} C\n"
        gpu_info += f"\t显存: {memory_info.used / 1024**3:.2f} GB / {memory_info.total / 1024**3:.2f} GB"
    pynvml.nvmlShutdown()

    return gpu_info


def get_cpu_info() -> str:
    """
    Retrieves information about the CPU.

    Returns:
        str: A string containing information about the CPU, including the number of physical and logical cores, CPU frequency, and CPU usage.
    """
    cpu_info_str = (
        f"CPU信息：\n"
        f"\t物理核心数：{psutil.cpu_count()}\n"
        f"\t逻辑核心数：{psutil.cpu_count(True)}\n"
        f"\tCPU频率：{psutil.cpu_freq().max} MHz\n"
        f"\t占用率: {psutil.cpu_percent()}%"
    )
    return cpu_info_str


def get_disk_info() -> str:
    """
    Returns a string containing disk information.

    Returns:
        str: A string containing the disk information. The string is formatted as follows:
            - Total disk space in GB
            - Used disk space in GB
            - Available disk space in GB
            - Disk usage percentage
    """
    disk_info = psutil.disk_usage("/")
    disk_info_str = (
        f"磁盘信息：\n"
        f"\t总磁盘空间：{disk_info.total / 1024 / 1024 / 1024:.2f} GB\n"
        f"\t已使用磁盘空间：{disk_info.used / 1024 / 1024 / 1024:.2f} GB\n"
        f"\t可用磁盘空间：{disk_info.free / 1024 / 1024 / 1024:.2f} GB\n"
        f"\t磁盘使用率：{disk_info.percent}%"
    )
    return disk_info_str


def get_mem_info() -> str:
    """
    Retrieves the information about the system's memory usage.

    Returns:
        str: A string containing the memory information, formatted as follows:
            - Total memory: {total_memory} GB
            - Used memory: {used_memory} GB
            - Available memory: {available_memory} GB
            - Memory usage: {memory_usage}%
    """
    mem_info = psutil.virtual_memory()
    mem_info_str = (
        f"内存信息：\n"
        f"\t总内存：{mem_info.total / 1024 / 1024 / 1024:.2f} GB\n"
        f"\t已使用内存：{mem_info.used / 1024 / 1024 / 1024:.2f} GB\n"
        f"\t可用内存：{mem_info.available / 1024 / 1024 / 1024:.2f} GB\n"
        f"\t内存使用率：{mem_info.percent}%"
    )
    return mem_info_str


def get_all_info() -> str:
    """
    Returns a string containing all hardware information.

    :return: A string with CPU, memory, disk, and GPU information.
    :rtype: str
    """
    hardware_info = f"{get_cpu_info()}\n\n{get_mem_info()}\n\n{get_disk_info()}\n\n{get_gpu_info()}"
    return hardware_info
