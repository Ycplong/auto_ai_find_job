import time

from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 全局 WebDriver 实例
driver = None


def get_driver():
    global driver
    return driver


def open_browser_with_options(url, browser):
    global driver
    if browser == "chrome":
        # 指定 Chrome 浏览器的路径
        # 创建 Chrome 选项
        options = ChromeOptions()
        options.binary_location = google_path  # 设置 Chrome 二进制路径
        # 创建 ChromeDriver 服务
        service = ChromeService(chrome_driver_path)
        # 启动 Chrome 浏览器
        driver = webdriver.Chrome(service=service, options=options)
    elif browser == "edge":
        # 创建 Edge 选项
        options = EdgeOptions()
        # 创建 EdgeDriver 服务
        service = EdgeService(edge_driver_path)
        # 启动 Edge 浏览器
        driver = webdriver.Edge(service=service, options=options)
    else:
        raise ValueError("Browser type not supported. Use 'chrome' or 'edge'.")

    # 最大化浏览器窗口
    driver.maximize_window()
    # 打开目标 URL
    driver.get(url)

    # 等待直到页面包含特定的 XPath 元素
    xpath_locator = "//*[@id='zpPassportWidget']/div/div/div/div/div[1]/div"
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, xpath_locator))
    )

def log_in():
    global driver

    # 点击按钮
    login_button = driver.find_element(By.XPATH, "//*[@id='zpPassportWidget']/div/div/div/div/div[1]/div")
    login_button.click()

    # 等待微信扫码按钮出现
    # 微信登录按钮的 XPath
    xpath_locator_wechat_login = "//*[@id='zpPassportWidget']/div/div/div/div/div[2]/div[1]/img[1]"

    try:
        # 等待微信登录按钮出现，最多等待 15 秒
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, xpath_locator_wechat_login))
        )
        print("微信扫码按钮已找到，等待扫码...")

        # # 查找微信登录按钮并点击
        # wechat_button = driver.find_element(By.XPATH, xpath_locator_wechat_login)
        # wechat_button.click()
        # print("微信登录按钮点击成功！")
    except TimeoutException:
        print("微信登录按钮未找到，可能不是首次登录，跳过点击操作。")
    except NoSuchElementException:
        print("微信登录按钮未找到，可能不是首次登录，跳过点击操作。")
    except Exception as e:
        print(f"发生未知错误: {e}")
    print("扫码登录中。。。。。。。。。。。。")
    #用户信息pic
    xpath_locator_wechat_logo = "//*[@id='root']/div[3]/div[2]/div[3]/div[1]/div[2]/div[1]/img"


    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, xpath_locator_wechat_logo))
    )
    print('扫码登录成功')



def get_job_description():
    global driver

    # 使用给定的 XPath 定位职位描述元素
    xpath_locator_job_description = "//*[@id='wrap']/div[2]/div[2]/div/div/div[2]/div/div[2]/p"

    # 确保元素已加载并且可以获取文本
    job_description_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, xpath_locator_job_description))
    )

    # 获取职位描述文本
    job_description = job_description_element.text
    print(job_description)  # 打印出职位描述，或者你可以在这里做其他处理

    # 返回职位描述文本，如果函数需要
    return job_description



def select_dropdown_option(driver, label,city):
    # 尝试在具有特定类的元素中找到文本
    trigger_elements = driver.find_elements(By.XPATH, "//*[@id='root']/div[3]/div[2]/div[3]/div[1]/div[2]/div[1]/img")
    city_tag = "//*[@id='rightNav_top']/div/div[1]/div/div[1]/div/a"
    # 确保city元素已加载并且可以获取文本
    try:
        city_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, city_tag))
        )
        city_element.click()
        try:
            sel_city_tag = "//*[@id='root']/div[2]/div[2]/div/div[1]/div[2]/div/input"
            sel_city_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, sel_city_tag))
            )
            sel_city_element.send_keys(city)
            sel_city_element.send_keys(Keys.ENTER)
        except TimeoutException:
            print("键入城市超时")
        except NoSuchElementException:
            print("未知错误")
    except TimeoutException:
        print("搜索切换城市超时")
    except NoSuchElementException:
        print("未知错误")
    job_text = "//*[@id='root']/div[1]/div/div[2]/div/div/div[2]/div/div/input"
    try:
        job_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, job_text)))
        job_element.send_keys(label)
        job_element.send_keys(Keys.ENTER)
    except TimeoutException:
        print("搜索切换城市超时/键入职位超时")
    except NoSuchElementException:
        print("未知错误")
    # 标记是否找到元素
    found = True


    if found:
        # 取消注释，提供选择更多tag的时间
        # time.sleep(20)
        return



# Variables
url = "https://www.zhaopin.com/"
browser_type = "chrome"
chrome_driver_path = 'chromedriver.exe'
edge_driver_path = ''
google_path = r'C:\Users\Administrator\AppData\Local\Google\Chrome\Bin\chrome.exe'
open_browser_with_options(url,browser_type)