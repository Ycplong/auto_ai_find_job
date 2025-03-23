from selenium.common import NoSuchElementException, TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from langchain_functions import load_cookies, save_cookies, is_logged_in

# 全局 WebDriver 实例
driver = None


def get_driver():
    global driver
    return driver


def open_browser_with_options(url, browser,google_path,chrome_driver_path):
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
    xpath_locator = "//*[@id='header']/div[1]/div[3]/div/a"
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, xpath_locator))
    )


def log_in(platform):
    global driver

    # 尝试加载 Cookies
    if load_cookies(driver, 'boss'):
        driver.refresh()  # 刷新页面使 Cookies 生效
        if is_logged_in(driver,platform):
            return  # 已登录则退出

    # 点击登录按钮
    # 点击登录按钮
    try:
        login_button = driver.find_element(By.XPATH, "//*[@id='header']/div[1]/div[3]/div/a")
        login_button.click()
    except NoSuchElementException:
        print("未找到登录按钮，可能已经在登录页面")
    # 等待微信登录按钮出现
    xpath_locator_wechat_login = "//*[@id='wrap']/div/div[2]/div[2]/div[2]/div[1]/div[4]/a"
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_locator_wechat_login)))
        print("微信登录按钮已找到，尝试点击...")

        # 点击微信登录按钮
        wechat_button = driver.find_element(By.XPATH, xpath_locator_wechat_login)
        wechat_button.click()
        print("微信登录按钮点击成功！")
    except (TimeoutException, NoSuchElementException):
        print("微信登录按钮未找到，可能不是首次登录，跳过点击操作。")
    except Exception as e:
        print(f"发生未知错误: {e}")

    # 等待登录成功
    print("扫码登录中...")
    xpath_locator_wechat_logo = "//*[@id='header']/div[1]/div[3]/ul/li[2]/a/img"
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, xpath_locator_wechat_logo)))
    print("登录成功")

    # 保存 Cookies
    save_cookies(driver, 'boss')


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


def select_dropdown_option(driver, label):
    # 尝试在具有特定类的元素中找到文本
    trigger_elements = driver.find_elements(By.XPATH, "//*[@class='recommend-job-btn has-tooltip']")

    # 标记是否找到元素
    found = False

    for element in trigger_elements:
        if label in element.text:
            # 确保元素可见并且可点击
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element))
            element.click()  # 点击找到的元素
            found = True
            break

    # 如果在按钮中找到了文本，就不再继续下面的操作
    if found:
        # 取消注释，提供选择更多tag的时间
        # time.sleep(20)
        return

    # 如果在按钮中没有找到文本，执行原来的下拉列表操作
    # trigger_selector = "//*[@id='wrap']/div[2]/div[1]/div/div[1]/div"
    # WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.XPATH, trigger_selector))
    # ).click()  # 打开下拉菜单
    #
    # dropdown_selector = "ul.dropdown-expect-list"
    # WebDriverWait(driver, 10).until(
    #     EC.visibility_of_element_located((By.CSS_SELECTOR, dropdown_selector))
    # )
    #
    # option_selector = f"//li[contains(text(), '{label}')]"
    # WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.XPATH, option_selector))
    # ).click()  # 选择下拉菜单中的选项


def get_job_description_by_index(index):
    try:
        job_selector = f"//*[@id='wrap']/div[2]/div[2]/div/div/div[1]/ul/div[{index}]/li/div[1]/div/a"
        job_element = driver.find_element(By.XPATH, job_selector)
        job_element.click()

        description_selector = "//*[@id='wrap']/div[2]/div[2]/div/div/div[2]/div/div[2]/p"
        #//*[@id="wrap"]/div[2]/div[2]/div/div/div[2]/div/div[2]/p
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, description_selector))
        )
        job_description_element = driver.find_element(By.XPATH, description_selector)
        return job_description_element.text

    except NoSuchElementException:
        print(f"No job found at index {index}.")
        return None


if __name__ =="__main__":
    # Variables
    url = "https://www.zhipin.com/web/geek/job-recommend?ka=header-job-recommend"
    browser_type = "chrome"
    chrome_driver_path = 'chromedriver.exe'
    edge_driver_path = ''
    google_path = r'C:\Users\Administrator\AppData\Local\Google\Chrome\Bin\chrome.exe'
    open_browser_with_options(url, browser_type)
    # 关闭浏览器
    if driver:
        driver.quit()