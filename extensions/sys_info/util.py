import pynvml


def get_gpu_info():
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
