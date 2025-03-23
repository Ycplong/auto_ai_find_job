import time


from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver import Keys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from langchain_functions import load_cookies, save_cookies, is_logged_in


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
    xpath_locator = "//*[@id='zpPassportWidget']/div/div/div/div/div[1]/div"
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, xpath_locator))
    )

def log_in(platform):
    global driver

    # 尝试加载 Cookies
    if load_cookies(driver,'zl'):
        driver.refresh()  # 刷新页面使 Cookies 生效
        if is_logged_in(platform):
            return  # 已登录则退出
    #
    # 点击登录按钮
    try:
        login_button = driver.find_element(By.XPATH, "//*[@id='zpPassportWidget']/div/div/div/div/div[1]/div")
        login_button.click()
        print("点击登录按钮")
    except NoSuchElementException:
        print("未找到登录按钮，可能已经在登录页面")

    # 等待微信扫码按钮出现
    xpath_locator_wechat_login = "//*[@id='zpPassportWidget']/div/div/div/div/div[2]/div[1]/img[1]"
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, xpath_locator_wechat_login))
        )
        print("微信扫码按钮已找到，等待扫码...")
    except (TimeoutException, NoSuchElementException):
        print("微信扫码按钮未找到，可能不是首次登录，跳过点击操作。")
    except Exception as e:
        print(f"发生未知错误: {e}")

    # 等待登录成功
    print("扫码登录中。。。。。。。。。。。。")
    xpath_locator_wechat_logo = "//*[@id='root']/div[3]/div[2]/div[3]/div[1]/div[2]/div[1]/img"
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, xpath_locator_wechat_logo)))
    print("扫码登录成功")

    # 保存 Cookies
    # 保存 Cookies
    save_cookies(driver,'zl')




def get_job_description():
    global driver

    try:
        # 打印当前页面的 URL 和标题（调试用）
        print(f"当前页面 URL: {driver.current_url}")
        print(f"当前页面标题: {driver.title}")

        # 打印 1111 和 driver 状态
        print(1111)
        print(driver)

        # 获取所有职位元素
        index_job_tag = "//*[@id='positionList-hook']/div/div[1]/div"

        # 保存原始窗口句柄
        original_window = driver.current_window_handle

        # 记录已经处理过的职位元素
        processed_elements = set()

        # 逐步滚动加载所有职位
        current_position = 0
        scroll_step = 500  # 每次滚动 500 像素

        while True:
            # 获取当前可见的职位元素
            current_job_elements = driver.find_elements(By.XPATH, index_job_tag)
            print(f"当前页面job数量{len(current_job_elements)}")
            # 处理当前加载的职位元素
            for index,element in enumerate(current_job_elements):
                if element not in processed_elements:  # 避免重复处理
                    try:
                        # 点击职位元素
                        # element.click()
                        href_tag = f"//*[@id='positionList-hook']/div/div[1]/div[{index+1}]/div[1]/div[1]/div[1]/a"
                        href_tag_element = WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, href_tag))
                        )
                        href_tag_element.click()
                        print(f"处理职位: {element.text}")
                        time.sleep(1)
                        # 获取所有窗口句柄
                        all_windows = driver.window_handles

                        # 切换到新页面
                        driver.switch_to.window(all_windows[-1])
                        print(f"切换到新页面，当前页面标题: {driver.title}")

                        # 在这里可以添加其他操作，例如提取职位描述
                        # 例如：
                        # job_description_xpath = "//*[@id='wrap']/div[2]/div[2]/div/div/div[2]/div/div[2]/p"
                        # job_description_element = WebDriverWait(driver, 10).until(
                        #     EC.presence_of_element_located((By.XPATH, job_description_xpath)))
                        # job_description = job_description_element.text
                        # print(f"职位描述: {job_description}")

                        # 关闭新页面
                        driver.close()

                        # 切换回原始页面
                        driver.switch_to.window(original_window)
                        print("切换回原始页面")

                        # 标记为已处理
                        processed_elements.add(element)

                    except Exception as e:
                        print(f"处理职位时发生错误: {e}")
                        # 如果发生错误，关闭新页面并切换回原始页面
                        if len(driver.window_handles) > 1:
                            driver.close()
                            driver.switch_to.window(original_window)
            # 滚动一小段距离
            current_position += scroll_step
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            print(f"滚动到位置: {current_position}")
            # 打印找到的职位数量
            print(f"当前找到 {len(processed_elements)} 个职位")
            # 等待新内容加载
            time.sleep(1)  # 根据实际情况调整等待时间



            # 计算新的页面高度
            new_scroll_height = driver.execute_script("return document.body.scrollHeight")
            if current_position >= new_scroll_height:
                print("已滚动到底部")
                break



    except Exception as e:
        print(f"发生未知错误: {e}")


def one_click_delivery():
    global driver
    while True:
        try:
            # 打印当前页面的 URL 和标题（调试用）
            print(f"当前页面 URL: {driver.current_url}")
            print(f"当前页面标题: {driver.title}")

            # 打印调试信息
            print(1111)
            print(driver)

            # 获取所有职位元素
            index_job_tag = "//*[@id='positionList-hook']/div/div[1]/div"
            # 获取当前可见的职位元素
            current_job_elements = driver.find_elements(By.XPATH, index_job_tag)
            print(f"当前页面job数量: {len(current_job_elements)}")

            # 使用 JavaScript 滚动到页面底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # 等待页面加载（如果需要）
            time.sleep(2)  # 根据实际情况调整等待时间

            # 获取全选按钮并点击
            all_select = "//*[@id='positionList-hook']/div/div[2]/div[1]/div/div[1]/i"
            all_select_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, all_select)))
            all_select_element.click()
            print("准备投递")
            # 获取全部投递按钮并点击
            try:
                #//*[@id="positionList-hook"]/div/div[2]/div[1]/div/div[2]/div/span
                all_delivery = "//*[@id='positionList-hook']/div/div[2]/div[1]/div/div[2]/div/span"
                all_delivery_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, all_delivery))
                )
                all_delivery_element.click()
                print(f"全部投递 {all_delivery_element.text[-2:]} 个职位")
            except Exception as e:
                print(str(e))

            # 处理可能出现的弹窗
            try:
                may_close = "//*[@id='root']/div[3]/div[3]/div/img[2]"
                may_close_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, may_close)))
                may_close_element.click()
            except (NoSuchElementException, TimeoutException):
                print("本次未出现关闭页面")

            # 切换到新窗口并关闭
            all_windows = driver.window_handles
            original_window = driver.current_window_handle
            driver.switch_to.window(all_windows[-1])
            driver.close()
            driver.switch_to.window(original_window)

            # 获取下一页按钮
            next_page = "//*[@id='positionList-hook']/div/div[2]/div[2]/div/a[7]"
            try:
                next_page_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, next_page))
                )
                next_page_element.click()
            except (NoSuchElementException, TimeoutException):
                print("没有下一页了，退出循环")
                break  # 如果没有下一页，退出循环

        except Exception as e:
            print(f"发生异常: {e}")
            break  # 如果发生异常，退出循环




def select_dropdown_option( driver,label,city):
    # 尝试在具有特定类的元素中找到文本
    #trigger_elements = driver.find_elements(By.XPATH, "//*[@id='root']/div[3]/div[2]/div[3]/div[1]/div[2]/div[1]/img")
    city_tag = "//*[@id='rightNav_top']/div/div[1]/div/div[1]/div/a"
    # 确保city元素已加载并且可以获取文本
    try:
        city_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, city_tag))
        )
        city_element.click()
        print(f"搜索到切换城市按钮")
        # 获取所有窗口句柄
        all_windows = driver.window_handles
        # 切换到第二个页面
        driver.switch_to.window(all_windows[-1])
        try:
            # //*[@id="root"]/div[2]/div[2]/div/div[1]/div[2]/div/input
            driver.save_screenshot("screenshot.png")
            sel_city_tag = "//input[@class='city-search__box__text--field']"
            sel_city_css_se = "#root > div.city-center > div.city-center__nav > div > div.city-search.clearfix > div.city-search__box > div > input"
            sel_city_element = WebDriverWait(driver, 13).until(
                EC.presence_of_element_located((By.XPATH, sel_city_tag))
            )
            print("找到城市输入框")
            sel_city_element.send_keys(city)
            sel_city_element.send_keys(Keys.ENTER)
            print(f"键入城市到{city}")
        except TimeoutException:
            print("键入城市超时")
        except NoSuchElementException:
            print("未知错误")
    except TimeoutException:
        print("搜索切换城市超时")
    except NoSuchElementException:
        print("未知错误")
    # 获取所有窗口句柄
    all_windows = driver.window_handles

    # 切换到第3个页面
    driver.switch_to.window(all_windows[-1])

    # //*[@id="root"]/div[1]/div/div[2]/div/div/div[2]/div/div/input
    job_text = "//*[@id='root']/div[1]/div/div[2]/div/div/div[2]/div/div/input"
    try:
        job_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, job_text)))
        job_element.send_keys(label)
        job_element.send_keys(Keys.ENTER)
    except TimeoutException:
        print("搜索键入职位超时")
    except NoSuchElementException:
        print("未知错误")


    # 获取所有窗口句柄
    all_windows = driver.window_handles

    # 切换到第3个页面
    driver.switch_to.window(all_windows[-1])
    print(f"当前页面 1URL: {driver.current_url}")
    driver.save_screenshot("screenshot1.png")
    print(f'到达对应城市{city}找{label}')



if __name__ == '__main__':
    # Variables
    url = "https://www.zhaopin.com/"
    browser_type = "chrome"
    chrome_driver_path = 'chromedriver.exe'
    edge_driver_path = ''
    google_path = r'C:\Users\Administrator\AppData\Local\Google\Chrome\Bin\chrome.exe'
    # 全局 WebDriver 实例
    driver = None
    open_browser_with_options(url,browser_type)
    log_in()
    label = 'python测试开发'
    city = '深圳'
    select_dropdown_option(driver,label,city)
    # 调用 get_job_description()
    try:
        print("页面已加载完成，开始获取第一个页面的所有职位描述")
        one_click_delivery()
    except TimeoutException:
        print("页面加载超时，无法获取职位描述")
    except Exception as e:
        print(f"发生未知错误: {e}")
    # 关闭浏览器
    if driver:
        driver.quit()