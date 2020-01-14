# coding=utf-8
import os
from datetime import datetime, date
import requests
import yaml
import json

class GFEverydaySMS:
    weather_types = {"风": 1, "云": 2, "雨": 3, "雪": 4, "霜": 5, "露": 6, "雾": 7, "雷": 8, "晴": 9, "阴": 10,
                     "feng": 1, "yun": 2, "yu": 3, "xue": 4, "shuang": 5, "lu": 6, "wu": 7, "lei": 8, "qing": 9, "yin": 10}
    urls = {"zaoan": 'http://api.tianapi.com/txapi/zaoan/index?key={0}',
            "tianqi": 'http://api.tianapi.com/txapi/tianqi/index?key={0}&city={1}',
            "wanan": 'http://api.tianapi.com/txapi/wanan/index?key={0}',
            "qinghua": 'http://api.tianapi.com/txapi/saylove/index?key={0}',
            "sms": 'https://api.binstd.com/sms/send?appkey={0}&mobile={1}&content={2}'}
    # 注意：顺序影响短信编辑
    zaoan_apis = ["tianqi", "zaoan"]
    wanan_apis = ["qinghua", "wanan"]

    def __init__(self):
        self.sms_list, self.dictum_channels, self.tx_api_key, self.bin_std_api_key = self.get_init_data()

    def get_init_data(self):
        '''
        初始化基础数据
        :return: None
        '''
        with open('_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.Loader)
        morning_alarm_timed = config.get('morning_alarm_timed').strip()
        evening_alarm_timed = config.get('evening_alarm_timed').strip()
        init_msg = f"每天定时发送时间：早-{morning_alarm_timed}, 晚-{evening_alarm_timed}\n"

        morning_dictum_channel = config.get('morning_dictum_channel', '')
        evening_dictum_channel = config.get('evening_dictum_channel', '')
        dictum_channels = [morning_dictum_channel, evening_dictum_channel]
        init_msg += f"信息获取渠道：早-{morning_dictum_channel}, 晚-{evening_dictum_channel}\n\n"

        sms_list = []
        sms_infos = config.get('sms_infos')
        for sms_info in sms_infos:
            sms = {}
            phone_number_file = sms_info.get('phone_number_file').strip()
            sms["phone_numbers"] = []
            with open(phone_number_file, "r") as file:
                raw_phone_numbers = file.readlines()
            for raw_phone_number in raw_phone_numbers:
                phone_number = raw_phone_number.strip()
                if(len(phone_number) > 0):
                    sms["phone_numbers"].append(phone_number)
            sms["gf_name"] = sms_info.get('gf_name', '')
            sms["city_name"] = sms_info.get('city_name', '')
            sms["start_date"] = sms_info.get('start_date', '')
            sms["sweet_words"] = sms_info.get('sweet_words', '')

            sms_list.append(sms)
            print_msg = f"女朋友的手机号码：{str(sms['phone_numbers'])}\n" \
                        f"女友所在地区：{sms['city_name']}\n" \
                        f"在一起的第一天日期：{sms['start_date']}\n" \
                        f"最后一句为：{sms['sweet_words']}\n\n"
            init_msg += print_msg

        tx_api_key = ''
        bin_std_api_key = []
        try:
            with open(config.get('tx_api_key_file', 'no_config'), "r") as file:
                tx_api_key = file.readline()
            with open(config.get('bin_std_api_key_file', 'no_config'), "r") as file:
                bin_std_app_key = file.readline().strip()
                bin_std_secret_key = file.readline().strip()
                bin_std_api_key = [bin_std_app_key, bin_std_secret_key]
        except:
            print("获取 API Key 失败，文件打开失败！请检查是否存在配置文件中的 api_key_file...\n")

        init_msg += f"tx_api_key:{tx_api_key}\nbin_std_api_key:{str(bin_std_api_key)}\n"

        print(u"*" * 25 + "init msg" + u"*" * 25)
        print(init_msg)

        return sms_list, dictum_channels, tx_api_key, bin_std_api_key

    def start_today_info(self, chat_id, send_test=False):
        '''
        每日定时开始处理。
        :param chat_id:int, 判断早晚安信息（0：早安，1：晚安）。
        :param send_test:bool, 测试标志，当为True时，不发送信息。
        :return: None。
        '''
        print("*" * 20 + "start_today_info" + "*" * 20)
        print("chat_id:", chat_id, "send_test:", send_test)
        print("获取相关信息...")
        date_str = date.today().strftime('%Y-%m-%d')
        for sms in self.sms_list:
            days = (datetime.strptime(date_str, '%Y-%m-%d') - datetime.strptime(sms["start_date"], '%Y-%m-%d')).days
            # 判断早安还是晚安
            if chat_id == 0:
                sms_msg = f"{sms['gf_name']}，今天是我们相恋的第{days}天！想你~\n"
                apis = self.zaoan_apis
            elif(chat_id == 1):
                sms_msg = f"{sms['gf_name']}，我们相恋的第{days}天就要结束啦！爱你~\n"
                apis = self.wanan_apis
            else:
                print("Wrong chat id!!!")
                return
            # 构建短信
            for k in apis:
                if k == "tianqi":
                    url = self.urls[k].format(self.tx_api_key, sms["city_name"])
                else:
                    url = self.urls[k].format(self.tx_api_key)
                sms_msg += self.get_url_info(url, k, "./cache/" + k + "/" + date_str + ".txt")
            sms_msg += sms['sweet_words']
            # 发送短信
            if len(sms["phone_numbers"]) <= 0:
                print("No Phone Number with msg:", sms_msg)
                return
            else:
                phone_numbers = sms["phone_numbers"][0]
                for phone_number in sms["phone_numbers"][1:]:
                    phone_numbers += "," + phone_number
                if not send_test:
                    url = self.urls["sms"].format(self.bin_std_api_key[0], phone_numbers, sms_msg)
                    self.send_sms_with_url(url)
                print(f"发送给{phone_numbers}成功:\n", sms_msg)
                return

    def get_url_info(self, url, k, file_path=""):
        '''
        获取url的返回值
        :param url: 请求地址
        :param k: 请求类型
        :param file_name: 缓存文件名
        :return: url返回值
        '''
        print("*" * 10 + "getting url info" + "*" * 10)
        if(os.path.exists(file_path)):
            print("reading cache file: ", file_path)
            with open(file_path, "r") as file:
                content = json.load(file)
        else:
            print("request url: ", url)
            resp = requests.get(url)
            content = json.loads(resp.text)
            if content:
                print(content)
            with open(file_path, "w") as file:
                file.write(json.dumps(content))

        c = content['newslist'][0]
        if k == "tianqi":
            msg = f"***天气预报来袭~~~\n" \
                  f"***{c['date']} {c['week']}\n" \
                  f"***今日{c['weather']}\n" \
                  f"***气温{c['lowest']}/{c['highest']}，当前气温{c['real']}\n" \
                  f"***风力{c['windspeed']}\n" \
                  f"***空气质量 {c['air_level']}\n"
        elif k == "zaoan":
            if "早安" in c["content"]:
                msg = c["content"] + "\n"
            else:
                msg = "早安~\n" + c["content"] + "\n"
        elif k == "wanan":
            if "晚安" in c["content"]:
                msg = c["content"] + "\n"
            else:
                msg = c["content"] + "\n晚安~\n"
        elif k == "qinghua":
            msg = c["content"] + "\n"
        else:
            msg = c["content"] + "\n"
        return msg

    def send_sms_with_url(self, url):
        print("*" * 10 + "sending sms" + "*" * 10)
        resp = requests.get(url)
        content = json.loads(resp.text)
        if content:
            print(content)

if __name__ == '__main__':
    g = GFEverydaySMS()
    g.start_today_info(0, send_test=True)
    g.start_today_info(1, send_test=True)