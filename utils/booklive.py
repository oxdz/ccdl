from selenium import webdriver


class booklive:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    # @staticmethod
    def login(self, username: str, password: str):
        input_username = self.driver.find_element_by_id("mail_address")
        input_password = self.driver.find_element_by_id("login_password")
        input_username.clear()
        input_password.clear()
        input_username.send_keys(username)
        input_password.send_keys(password)
        login_button_1 = self.driver.find_element_by_id("login_button_1")
        login_button_1.click()

    # @staticmethod
    def logout(self):
        self.driver.get("https://booklive.jp/index/logout")
