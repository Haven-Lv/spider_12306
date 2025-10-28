ticket_counts_history = []
import json
import time
from datetime import datetime

import pandas as pd
import prettytable as pt
# time_counts_history=[]
import requests


def gainMainingTickets():
    # 发送请求
    global from_city
    global to_city
    global data
    f=open('city.json',encoding='utf-8')
    jsonData=json.loads(f.read())
    from_city=input("请输入出发城市：")
    to_city=input("到达的城市：")
    print("输入日期时格式为XXXX-XX-XX")
    data=input("出发的日期：")
    url = f'https://kyfw.12306.cn/otn/leftTicket/queryG?leftTicketDTO.train_date={data}&leftTicketDTO.from_station={jsonData[from_city]}&leftTicketDTO.to_station={jsonData[to_city]}&purpose_codes=ADULT'
    headers = {
        # Cookie用户信息
        'Cookie': '_uab_collina=172770016548439167743266; JSESSIONID=9AECAC4E9521778A68B1FC58A9CE3D27; route=c5c62a339e7744272a54643b3be5bf64; BIGipServerotn=2664890634.50210.0000; _jc_save_fromStation=%u957F%u6C99%2CCSQ; _jc_save_toStation=%u4E0A%u6D77%2CSHH; _jc_save_fromDate=2024-10-09; _jc_save_toDate=2024-09-30; _jc_save_wfdc_flag=dc; guidesStatus=off; highContrastMode=defaltMode; cursorStatus=off',
        # User-Agent 用户代理，浏览器基本信息
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    # 获取数据
    response = requests.get(url=url, headers=headers)
    # 解析数据
    tb=pt.PrettyTable()
    tb.field_names = [
        '序号',
        '车次',
        '出发时间',
        '到达时间',
        '耗时',
        '特等座',
        '一等',
        '二等',
        '软卧',
        '硬卧',
        '硬座',
        '无座',
    ]
    page=1
    for i in response.json()['data']['result']:
        info = i.split('|')
        num = info[3]  # 车次
        start_time = info[8]  # 出发时间
        end_time = info[9]   # 到达时间
        use_time = info[10]    # 耗时
        topGrade = info[25]     # 特等座
        first_class = info[31]   # 一等
        second_class = info[30]  # 二等
        soft_sleeper = info[23]  # 软卧
        hard_sleeper = info[28]  # 硬卧
        hard_seat = info[29]  # 硬座
        no_seat = info[26]  # 无座
        tb.add_row([
            page,
            num,
            start_time,
            end_time,
            use_time,
            topGrade,
            first_class,
            second_class,
            soft_sleeper,
            hard_sleeper,
            hard_seat,
            no_seat,
        ])
        page+=1
    print(tb)
    number=int(input("请输入查询余票的序号:"))
    all=response.json()['data']['result'][number-1]
    info = all.split('|')
    global num_train
    num_train = info[3]  # 车次
    if info[25]:
        print("特等座25")
    if info[31]:
        print("一等31")
    if info[30]:
        print("二等30")
    if info[23]:
        print("软卧23")
    if info[28]:
        print("硬卧28")
    if info[29]:
        print("硬座29")
    if info[26]:
        print("无座26")
    global seatNumber
    seatNumber = int(input("请输入查询的坐席后面的数字编号："))
    print(f"余票为：{info[seatNumber]}")
    if info[seatNumber]=="有":
        trainNumber=20
    elif info[seatNumber]=="无":
        trainNumber=0
    else:
        trainNumber=info[seatNumber]
    # 获取当前时间
    current_time = datetime.now()
    # 格式化时间
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    temp=[formatted_time,trainNumber]
    ticket_counts_history.append(temp)  # renew



def renewMainingTickets():
    f = open('city.json', encoding='utf-8')
    jsonData = json.loads(f.read())
    url = f'https://kyfw.12306.cn/otn/leftTicket/queryG?leftTicketDTO.train_date={data}&leftTicketDTO.from_station={jsonData[from_city]}&leftTicketDTO.to_station={jsonData[to_city]}&purpose_codes=ADULT'
    headers = {
        # Cookie用户信息
        'Cookie': '_uab_collina=172770016548439167743266; JSESSIONID=9AECAC4E9521778A68B1FC58A9CE3D27; route=c5c62a339e7744272a54643b3be5bf64; BIGipServerotn=2664890634.50210.0000; _jc_save_fromStation=%u957F%u6C99%2CCSQ; _jc_save_toStation=%u4E0A%u6D77%2CSHH; _jc_save_fromDate=2024-10-09; _jc_save_toDate=2024-09-30; _jc_save_wfdc_flag=dc; guidesStatus=off; highContrastMode=defaltMode; cursorStatus=off',
        # User-Agent 用户代理，浏览器基本信息
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    # 获取数据
    response = requests.get(url=url, headers=headers)
    k=0
    for i in response.json()['data']['result']:
        info = i.split('|')
        if info[3]==num_train:
            break
        else:
            k+=1
    all = response.json()['data']['result'][k]
    info = all.split('|')
    if info[seatNumber] == "有":
        trainNumber = 20
    elif info[seatNumber] == "无":
        trainNumber = 0
    else:
        trainNumber = info[seatNumber]
    # 获取当前时间
    current_time = datetime.now()
    # 格式化时间
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    temp = [formatted_time, trainNumber]
    ticket_counts_history.append(temp)  # renew
# 首先获取初始值
gainMainingTickets()
# 循环间隔
circulate=int(input("请输入循环几分钟："))
print("正在进行第一次循环，请稍后...")
k=0
while True:
    renewMainingTickets()
    time.sleep(60)
    k+=1
    print(f"循环第{k}次")

    if k==circulate:
        break

# 转换为Excel
def deal():
    df = pd.DataFrame(ticket_counts_history, columns=["时间", "余票"])
    df.to_excel("ticket_counts_history.xlsx", index=False)
    print("Excel文件已保存")

deal()

