# 修改后的12306余票查询程序，支持多席位追踪并保存为Excel
import json
import time
from datetime import datetime

import pandas as pd
import prettytable as pt
import requests

# 席位编号和名称的映射，方便显示和存储
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
num_train = '' # 选中的车次
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
    """获取初始车次信息并选择多个席位进行追踪"""
    global from_city, to_city, data, num_train, selected_seats
    
    # 1. 城市和日期输入
    f = open('city.json', encoding='utf-8')
    jsonData = json.loads(f.read())
    from_city = input("请输入出发城市：")
    to_city = input("到达的城市：")
    print("输入日期时格式为XXXX-XX-XX")
    data = input("出发的日期：")
    
    # 2. 发送请求获取车次列表
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
    
    # 4. 选择车次
    number = int(input("请输入查询余票的序号:"))
    all_info_str = results[number - 1]
    info = all_info_str.split('|')
    num_train = info[3]
    
    # 5. 选择席位（多选）
    print("\n请选择要追踪的席位编号 (逗号分隔):")
    available_seats = {}
    for code, name in SEAT_MAPPING.items():
        if info[code]: # 检查该车次是否有此席位信息
            print(f"[{code}] {name} (当前状态: {info[code]})")
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
    
    # 6. 收集第一次数据
    collect_data(info)


def collect_data(info):
    """根据已选席位，收集当前时间点的所有余票数据"""
    global ticket_counts_history
    
    # 初始化当前数据列表，第一个元素是时间
    temp = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    
    # 遍历所有选中的席位，按顺序添加票数
    for code in selected_seats.keys():
        ticket_status = info[code]
        ticket_count = get_ticket_number(ticket_status)
        temp.append(ticket_count)
        
    ticket_counts_history.append(temp)
    print(f"[{temp[0]}] 初始余票数据收集完成。")
    print("-" * 30)

def renewMainingTickets():
    """循环更新余票信息"""
    global ticket_counts_history
    
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
        print(f"请求失败: {e}")
        return
    except json.JSONDecodeError:
        print("响应解析失败，可能需要更新Cookie或IP被封锁。")
        return
    
    # 找到目标车次
    target_info = None
    for i in results:
        info = i.split('|')
        if info[3] == num_train:
            target_info = info
            break
            
    if not target_info:
        print(f"未在最新查询结果中找到车次 {num_train}，跳过本次更新。")
        return

    # 收集并存储数据
    collect_data(target_info)


def deal():
    """将历史数据转换为Excel"""
    
    # 构建列名：时间 + 选中的所有席位名称
    columns = ["时间"] + list(selected_seats.values())
    
    df = pd.DataFrame(ticket_counts_history, columns=columns)
    
    # 命名 Excel 文件，包含车次和日期信息
    filename = f"{from_city}_to_{to_city}_{num_train}_{data}_tickets_history.xlsx"
    df.to_excel(filename, index=False)
    print(f"\nExcel文件已保存到: {filename}")

# --- 主程序执行部分 ---

# 1. 首次获取数据并确定追踪目标
gainMainingTickets()

# 2. 循环追踪
circulate = int(input("请输入循环几分钟："))
print("正在进行循环追踪...")

k = 0
while True:
    renewMainingTickets()
    
    k += 1
    print(f"循环第{k}次，已收集 {len(ticket_counts_history)} 条数据。")

    if k >= circulate:
        break
        
    time.sleep(60)

# 3. 转换为Excel
deal()