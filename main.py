# 修改后的12306余票查询程序，支持【多车次】、【多席位】追踪并保存为Excel
import json
import os
import random
import time
from datetime import datetime

import pandas as pd
import prettytable as pt
import requests

# 席位编号和名称的映射
SEAT_MAPPING = {
    25: '特等座',
    31: '一等座',
    30: '二等座',
    23: '软卧',
    28: '硬卧',
    29: '硬座',
    26: '无座',
}

# 全局变量
ticket_counts_history = []
from_city = ''
to_city = ''
data = '' # 出发日期

# 修改：使用字典存储选中的车次 {车次号: 初始info列表}
selected_trains = {} 
# 修改：使用字典存储选中的席位 {代码: 名称}
selected_seats = {} 

def get_ticket_number(status):
    """将票数状态字符串转换为数字"""
    if status == "有":
        return 20
    elif status == "无":
        return 0
    elif status.isdigit():
        return int(status)
    else:
        # 处理 '候补' 或其他非数字状态
        return 0

def gainMainingTickets():
    """获取初始车次信息并选择多个【车次】和多个【席位】进行追踪"""
    global from_city, to_city, data, selected_trains, selected_seats
    
    # 1. 城市和日期输入 (保持不变)
    f = open('city.json', encoding='utf-8')
    jsonData = json.loads(f.read())
    from_city = input("请输入出发城市：")
    to_city = input("到达的城市：")
    print("输入日期时格式为XXXX-XX-XX")
    data = input("出发的日期：")
    
    # 2. 发送请求获取车次列表 (保持不变)
    url = f'https://kyfw.12306.cn/otn/leftTicket/queryG?leftTicketDTO.train_date={data}&leftTicketDTO.from_station={jsonData[from_city]}&leftTicketDTO.to_station={jsonData[to_city]}&purpose_codes=ADULT'
    headers = {
        'Cookie': '_uab_collina=172770016548439167743266; JSESSIONID=9AECAC4E9521778A68B1FC58A9CE3D27; route=c5c62a339e7744272a54643b3be5bf64; BIGipServerotn=2664890634.50210.0000; _jc_save_fromStation=%u957F%u6C99%2CCSQ; _jc_save_toStation=%u4E0A%u6D77%2CSHH; _jc_save_fromDate=2024-10-09; _jc_save_toDate=2024-09-30; _jc_save_wfdc_flag=dc; guidesStatus=off; highContrastMode=defaltMode; cursorStatus=off',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    response = requests.get(url=url, headers=headers)
    results = response.json()['data']['result']
    
    # 3. 打印车次表格 (保持不变)
    tb = pt.PrettyTable()
    tb.field_names = ['序号', '车次', '出发时间', '到达时间', '耗时', '特等座', '一等', '二等', '软卧', '硬卧', '硬座', '无座']
    page = 1
    for i in results:
        info = i.split('|')
        tb.add_row([
            page, info[3], info[8], info[9], info[10], info[25], info[31], info[30], 
            info[23], info[28], info[29], info[26],
        ])
        page += 1
    print(tb)
    
    # 4. (修改) 选择【多】车次
    selected_trains.clear() # 清空旧数据
    train_input_str = input("请输入查询余票的序号 (可多选, 用逗号分隔, 如: 5,7,9): ")
    
    try:
        # 将 "5,7,9" 转换为索引 [4, 6, 8]
        selected_indices = [int(x.strip()) - 1 for x in train_input_str.split(',')]
    except ValueError:
        print("输入格式错误，请确保输入的是数字并用逗号分隔。")
        return
    
    for index in selected_indices:
        if 0 <= index < len(results):
            all_info_str = results[index]
            info = all_info_str.split('|')
            train_num = info[3]
            selected_trains[train_num] = info # 键是车次号, 值是该车次的初始信息
        else:
            print(f"警告：序号 {index + 1} 无效，已跳过。")
            
    if not selected_trains:
        print("未选择任何有效车次，程序退出。")
        exit()
        
    print(f"\n已选择追踪车次: {list(selected_trains.keys())}")
    
    # 5. 选择席位（多选）(保持不变)
    # (注意：这里的席位选择将应用于所有已选车次)
    print("\n请选择要追踪的席位编号 (逗号分隔):")
    
    # (逻辑微调：从已选的第一趟车获取可用的席位列表作为参考)
    first_train_info = list(selected_trains.values())[0]
    available_seats = {}
    for code, name in SEAT_MAPPING.items():
        if first_train_info[code]: 
            print(f"[{code}] {name} (状态参考: {first_train_info[code]})")
            available_seats[code] = name
            
    seat_input_str = input("请输入您希望追踪的坐席编号 (如: 30,28,26): ")
    
    try:
        selected_codes = [int(x.strip()) for x in seat_input_str.split(',')]
    except ValueError:
        print("输入格式错误，请确保输入的是数字并用逗号分隔。")
        return
        
    for code in selected_codes:
        if code in available_seats:
            selected_seats[code] = available_seats[code]
            
    if not selected_seats:
        print("未选择任何有效席位，程序退出。")
        exit()
            
    print(f"\n已选择追踪席位: {list(selected_seats.values())}")
    
    # 6. (修改) 收集【所有已选车次】的第一次数据
    print("\n正在收集所有已选车次的初始数据...")
    for train_num, info in selected_trains.items():
        collect_data(info, train_num) # 传入车次号和对应的info


def collect_data(info, train_num): # (修改) 增加 train_num 参数
    """根据已选席位，收集当前时间点的所有余票数据"""
    global ticket_counts_history
    
    # (修改) 初始化当前数据列表，第一个元素是时间，第二个是车次
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temp = [current_time_str, train_num]
    
    # 遍历所有选中的席位，按顺序添加票数
    for code in selected_seats.keys():
        ticket_status = info[code]
        ticket_count = get_ticket_number(ticket_status)
        temp.append(ticket_count)
            
    ticket_counts_history.append(temp)
    # (修改) 打印日志，包含车次号
    print(f"[{current_time_str}] {train_num}: 数据收集完成。")


def renewMainingTickets():
    """(修改) 循环更新【所有已选车次】的余票信息"""
    global ticket_counts_history, selected_trains
    
    f = open('city.json', encoding='utf-8')
    jsonData = json.loads(f.read())
    
    # 构建 URL 和 Headers (保持不变)
    url = f'https://kyfw.12306.cn/otn/leftTicket/queryG?leftTicketDTO.train_date={data}&leftTicketDTO.from_station={jsonData[from_city]}&leftTicketDTO.to_station={jsonData[to_city]}&purpose_codes=ADULT'
    headers = {
        'Cookie': '_uab_collina=172770016548439167743266; JSESSIONID=9AECAC4E9521778A68B1FC58A9CE3D27; route=c5c62a339e7744272a54643b3be5bf64; BIGipServerotn=2664890634.50210.0000; _jc_save_fromStation=%u957F%u6C99%2CCSQ; _jc_save_toStation=%u4E0A%u6D77%2CSHH; _jc_save_fromDate=2024-10-09; _jc_save_toDate=2024-09-30; _jc_save_wfdc_flag=dc; guidesStatus=off; highContrastMode=defaltMode; cursorStatus=off',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status() # 检查HTTP错误
        results = response.json()['data']['result']
    except requests.exceptions.RequestException as e:
        print(f"[请求失败] {e}")
        return
    except json.JSONDecodeError:
        print("[响应解析失败] 可能需要更新Cookie或IP被封锁。")
        return
    
    # (修改) 找到【所有】目标车次
    found_trains_info = {} # 存储本次查询到的 {车次: info}
    
    for i in results:
        info = i.split('|')
        train_num = info[3]
        
        # 检查这趟车是否在我们监控的 'selected_trains' 列表中
        if train_num in selected_trains:
            found_trains_info[train_num] = info
            
    if not found_trains_info:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 未在最新查询结果中找到任何已选车次，跳过本次更新。")
        return

    print("-" * 30)
    current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time_str}] 开始收集 {len(found_trains_info)} 趟车次的最新数据...")

    # (修改) 循环收集所有找到的车次的数据
    for train_num, info in found_trains_info.items():
        # (修改) 调用新的 collect_data
        collect_data(info, train_num) 
    
    # (修改) 检查是否有车次在本次查询中“失踪”了
    for train_num in selected_trains.keys():
        if train_num not in found_trains_info:
            print(f"警告：车次 {train_num} 在本次查询中未找到，可能已售罄或停运。")


def deal():
    """(修改) 将历史数据转换为Excel"""
    
    # (修改) 创建保存Excel文件的文件夹
    output_folder = "ticket_history_excel"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # (修改) 构建列名：时间 + 车次 + 选中的所有席位名称
    columns = ["时间", "车次"] + list(selected_seats.values())
    
    df = pd.DataFrame(ticket_counts_history, columns=columns)
    
    # (修改) 命名 Excel 文件，不再包含具体车次号
    filename = f"{from_city}_to_{to_city}_{data}_multi_train_history.xlsx"
    # (修改) 完整文件路径，包含输出文件夹
    full_path = os.path.join(output_folder, filename)
    df.to_excel(full_path, index=False)
    print(f"\nExcel文件已保存到: {full_path}")

# --- 主程序执行部分 ---

try:
    # 1. 首次获取数据并确定追踪目标
    gainMainingTickets()

    # 2. 循环追踪
    circulate = int(input("请输入循环几分钟："))
    print(f"\n正在对 {len(selected_trains)} 趟列车进行循环追踪...")
    print(f"监控车次: {list(selected_trains.keys())}")
    print(f"监控席位: {list(selected_seats.values())}")
    print("=" * 30)

    k = 0
    while True:
        if k >= circulate:
            print(f"已达到 {circulate} 次循环，停止追踪。")
            break
            
        k += 1
        print(f"\n--- 第 {k}/{circulate} 次查询 ---")
        
        renewMainingTickets()
        
        if k < circulate:
            time.sleep(random.randint(55, 65))

except KeyboardInterrupt:
    print("\n[用户操作] 检测到 Ctrl+C，程序已中断。")
except Exception as e:
    print(f"[程序异常] 发生未知错误: {e}")
finally:
    # 3. 转换为Excel
    if not ticket_counts_history:
        print("未收集到任何数据，程序退出。")
    else:
        print(f"\n正在保存已收集的 {len(ticket_counts_history)} 条数据到 Excel...")
        deal()