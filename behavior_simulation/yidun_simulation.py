# coding: utf-8
import requests
import time
import random
import math

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select


class YidunCaptchaSimulator:
    def __init__(self):
        options = Options()
        options.add_experimental_option('excludeSwitches',
                                        ['enable-automation'])
        self.driver = webdriver.Chrome(executable_path='./chromedriver',
                                       options=options)
        self.wait = WebDriverWait(self.driver, 30)
        self.slider_url = "http://dun.163.com/trial/jigsaw"
        self.click_url = "https://dun.163.com/trial/picture-click"

    def scroll_to_captcha(self, url):
        self.driver.get(url=url)
        time.sleep(1)
        self.driver.find_element_by_xpath(
            '//body//main//li[2]').click()
        time.sleep(.5)
        ActionChains(self.driver).move_to_element(
            self.driver.find_element_by_xpath("//div[@class='yidun_tips']")).perform()

    def simulate_slider(self):
        self.driver.maximize_window()
        self.scroll_to_captcha(self.slider_url)
        try:
            while True:
                background = \
                    self.driver.find_element_by_xpath(
                        "/html/body/main/div[1]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[2]/div[3]/div/div/div[1]/div/div[1]/img[1]").get_attribute(
                        'src')
                slider = \
                    self.driver.find_element_by_xpath(
                        "/html/body/main/div[1]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[2]/div[3]/div/div/div[1]/div/div[1]/img[2]").get_attribute(
                        'src')
                # for test
                # input_image_content = None
                #
                # for (img_name, img_data) in zip(
                #         ["background.jpg", "slider.jpg"],
                #         [background, slider]):
                #     with open(img_name, 'wb') as f:
                #         rsp = requests.get(img_data)
                #         f.write(rsp.content)
                #         if 'background' in img_name:
                #             input_image_content = rsp.content
                input_image_content = requests.get(background).content

                distance = self.get_distance(input_image_content)
                if distance == -1:
                    return
                trajectory = self.get_tracks(distance + 2)  # ??????????????????????????????
                slider = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.CLASS_NAME, "yidun_jigsaw")))
                ActionChains(self.driver).click_and_hold(slider).perform()
                # move_by_offset????????????????????????Selenium????????????????????????????????????????????????
                # ????????????https://my.oschina.net/chinaandroid/blog/3219453/print
                for track in trajectory['plus']:
                    ActionChains(self.driver).move_by_offset(xoffset=track,
                                                             yoffset=round(
                                                                 random.uniform(
                                                                     1.0,
                                                                     3.0),
                                                                 1)).perform()
                time.sleep(0.1)
                for back_tracks in trajectory['reduce']:
                    ActionChains(self.driver).move_by_offset(
                        xoffset=back_tracks,
                        yoffset=round(
                            random.uniform(1.0,
                                           3.0),
                            1)).perform()

                ActionChains(self.driver).move_by_offset(xoffset=-4,
                                                         yoffset=0).perform()
                ActionChains(self.driver).move_by_offset(xoffset=4,
                                                         yoffset=0).perform()

                ActionChains(self.driver).release().perform()
                time.sleep(2)
        except Exception as e:
            print(e)

    def simulate_click(self):
        self.driver.maximize_window()
        self.scroll_to_captcha(self.click_url)
        try:
            while True:
                background = self.driver.find_element_by_xpath(
                    "//img[@class='yidun_bg-img']").get_attribute('src')

                tips = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.CLASS_NAME, "yidun_tips__answer")))  # ??????????????????
                words = self.driver.find_element_by_xpath("//span[@class='yidun_tips__point']")\
                    .text.replace('"', '').replace(" ", '')
                input_image_content = requests.get(background).content
                rets = self.get_rets(input_image_content, words)
                if rets == -1:
                    # ?????????????????????
                    self.driver.find_element_by_xpath("//div[@class='yidun_refresh']").click()
                    time.sleep(2)
                    continue
                self.touch_click_words(rets)
                time.sleep(2)
        except Exception as e:
            print(e)

    def touch_click_words(self, rets):
        """
        ??????????????????
        :param rets: ????????????
        :return: None
        """
        slice_num = 10
        x_range = list(map(lambda x: x / 10, range(slice_num)))
        element = self.driver.find_element_by_xpath("//img[@class='yidun_bg-img']")
        # ?????????????????????
        ActionChains(self.driver).move_to_element_with_offset(element, 0, 0).perform()
        route = []
        rets.insert(0, [0, 0])  # ????????????????????????
        for ret_index in range(1, len(rets)):
            # ???????????????????????????????????????
            for x in x_range:
                value = self.ease_out_back(x)
                two_words_x_gap = (rets[ret_index][0] - rets[ret_index-1][0])
                two_words_y_gap = (rets[ret_index][1] - rets[ret_index-1][1])
                route.append([round(rets[ret_index-1][0] + two_words_x_gap * value, 1),
                              round(rets[ret_index-1][1] + two_words_y_gap * value, 1)])
            # ????????????
            route.append([rets[ret_index][0], rets[ret_index][1]])
        time.sleep(random.uniform(0.5, 1.5))
        rets.pop(-1)
        for index in range(len(route)):
            if index % 10 == 0:
                ActionChains(self.driver).move_to_element_with_offset(element,
                                                                      route[index][0],
                                                                      route[index][1]).click().perform()
                time.sleep(random.uniform(0.5, 1.5))
            else:
                xoffset = route[index][0] - route[index - 1][0]
                yoffset = route[index][1] - route[index - 1][1]
                ActionChains(self.driver).move_by_offset(xoffset=round(xoffset, 1),
                                                         yoffset=round(yoffset, 1)).perform()

    @staticmethod
    def get_distance(content):
        """???????????????????????????"""
        result = requests.post('http://127.0.0.1:5001/detect', files={'image': content},
                               data={'choice': 'slider'})
        if result.status_code == 200:
            info = result.json()
            distance = info['x_center'] - (1/2 * info['width'])
            print(distance)
            # ????????????480 ???????????????320
            return distance * 320 / 480
        else:
            return -1

    @staticmethod
    def get_tracks(distance):
        """
        ????????????????????????????????????????????????????????????
        :param distance:
        :return:
        """
        valve = round(random.uniform(0.55, 0.75), 2)  # ??????????????????????????????
        distance += 20  # ????????????20px
        v, t, sum = 0, 0.2, 0  # ???????????????????????????????????????????????????????????????
        plus = []  # ??????????????????
        mid = distance * valve  # ?????????????????????????????????????????????????????????
        while sum < distance:
            if sum < mid:
                a = round(random.uniform(2.5, 3.5), 1)  # ???????????????????????????????????????
            else:
                a = -(round(random.uniform(2.0, 3.0), 1))  # ????????????????????????????????????????????????
            s = v * t + 0.5 * a * (t ** 2)  # ?????????????????????????????????
            v = v + a * t  # ??????????????????????????????
            sum += s
            plus.append(round(s))

        reduce = [-3, -3, -2, -2, -2, -2, -2, -1, -1, -1]  # ?????????????????????????????????20px
        print({'plus': plus, 'reduce': reduce})
        return {'plus': plus, 'reduce': reduce}

    def get_rets(self, content, words):
        result = requests.post('http://127.0.0.1:5001/detect', files={'image': content},
                               data={'choice': 'click', 'words': words})
        if result.status_code == 200:
            info = result.json()
            # ????????????480 ???????????????320
            rets = info['rets']
            for item in rets:
                item[0], item[1] = round(item[0] * 320 / 480, 1), round(item[1] * 320 / 480, 1)
            return rets
        else:
            return -1

    @staticmethod
    def ease_out_back(x):
        """
        https://easings.net/#easeOutBack
        ??????????????????easeOutBack??????
        :param x: 0~1 (float)
        :return:
        """
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(x - 1, 3) + c1 * pow(x - 1, 2)


if __name__ == '__main__':
    simulator = YidunCaptchaSimulator()
    # simulator.simulate_slider()
    simulator.simulate_click()
